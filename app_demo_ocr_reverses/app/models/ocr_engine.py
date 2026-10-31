import os
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

from paddleocr import TextDetection, TextRecognition
from app.core.logger import get_logger

logger = get_logger(__name__)


class OCREngine:
    """
    Low-level wrapper around PaddleOCR's detection and recognition models:
    1. PP-OCRv6_medium_det: DBNet text polygon detector
    2. PP-OCRv6_medium_rec: SVTRv2 text line recognizer
    Includes adaptive image enhancement fallback for low-light, blurry, or noisy industrial labels.
    """

    def __init__(
        self,
        det_model_name: str = "PP-OCRv6_medium_det",
        rec_model_name: str = "PP-OCRv6_medium_rec",
        device: Optional[str] = None,
        det_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.det_model_name = det_model_name
        self.rec_model_name = rec_model_name
        self.device = device
        self.det_params = det_params or {
            "limit_side_len": 960,
            "limit_type": "max",
            "thresh": 0.3,
            "box_thresh": 0.55,
            "unclip_ratio": 1.8,
        }

        logger.info(
            "Initializing OCREngine (det=%s, rec=%s)...",
            det_model_name,
            rec_model_name,
        )
        self.detector = TextDetection(
            model_name=det_model_name,
            device=device,
        )
        self.recognizer = TextRecognition(
            model_name=rec_model_name,
            device=device,
        )

    @staticmethod
    def enhance_degraded_image(image: np.ndarray) -> np.ndarray:
        """
        Enhance low-light, noisy, or blurry industrial label images using
        LAB CLAHE + bilateral filtering + unsharp masking.
        Preserves exact image dimensions so bounding box coordinates remain unchanged.
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_chan, a_chan, b_chan = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_chan)
        merged = cv2.merge((l_enhanced, a_chan, b_chan))
        enhanced_bgr = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

        # Denoise while preserving character edges
        denoised = cv2.bilateralFilter(enhanced_bgr, d=5, sigmaColor=35, sigmaSpace=35)

        # Mild unsharp mask to recover blurred character strokes
        gaussian = cv2.GaussianBlur(denoised, (0, 0), sigmaX=1.5)
        sharpened = cv2.addWeighted(denoised, 1.45, gaussian, -0.45, 0)
        return sharpened

    @staticmethod
    def is_image_low_quality(image: np.ndarray) -> bool:
        """
        Check if an image is low-light, low-contrast, or blurry.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(np.mean(gray))
        contrast_std = float(np.std(gray))
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        return mean_brightness < 85.0 or contrast_std < 35.0 or laplacian_var < 90.0

    def detect_text_regions(
        self, image: np.ndarray
    ) -> Tuple[List[np.ndarray], List[float], np.ndarray]:
        """
        Detect text polygons directly on the original image (preserving original coordinates).
        If the image is degraded (low-light/blurry) or yields no boxes, also checks the
        CLAHE-enhanced version (same dimensions) and picks the better detection set.

        Returns:
            polys: List of 4x2 numpy arrays in original image coordinates
            scores: List of detection scores
            working_img: Image array used for cropping (original or enhanced if degraded)
        """
        preds = list(self.detector.predict(image, **self.det_params))
        polys: List[np.ndarray] = []
        scores: List[float] = []
        if preds:
            raw_polys = preds[0].get("dt_polys", [])
            raw_scores = preds[0].get("dt_scores", [])
            polys = [np.array(p, dtype=np.float32) for p in raw_polys]
            scores = [float(s) for s in raw_scores]

        working_img = image
        if len(polys) == 0 or self.is_image_low_quality(image):
            enhanced_img = self.enhance_degraded_image(image)
            enh_preds = list(self.detector.predict(enhanced_img, **self.det_params))
            if enh_preds:
                enh_polys = [
                    np.array(p, dtype=np.float32)
                    for p in enh_preds[0].get("dt_polys", [])
                ]
                enh_scores = [float(s) for s in enh_preds[0].get("dt_scores", [])]
                if len(enh_polys) > len(polys) or (
                    len(enh_polys) == len(polys)
                    and len(enh_scores) > 0
                    and np.mean(enh_scores) > (np.mean(scores) if scores else 0.0)
                ):
                    polys = enh_polys
                    scores = enh_scores
                    working_img = enhanced_img

        # Sort polygons top-to-bottom, left-to-right in original coordinates
        if polys:
            order = sorted(
                range(len(polys)),
                key=lambda i: (
                    float(np.mean(polys[i][:, 1])) // 15,
                    float(np.min(polys[i][:, 0])),
                ),
            )
            polys = [polys[i] for i in order]
            scores = [scores[i] if i < len(scores) else 1.0 for i in order]

        return polys, scores, working_img

    def recognize_batch(
        self, crops: List[np.ndarray]
    ) -> List[Tuple[str, float]]:
        """
        Run text recognition on a list of horizontal text-line crops.

        Returns:
            List of (recognized_text, confidence_score)
        """
        if not crops:
            return []
        preds = list(self.recognizer.predict(crops))
        results: List[Tuple[str, float]] = []
        for res in preds:
            txt = str(res.get("rec_text", "")).strip()
            score = float(res.get("rec_score", 0.0))
            results.append((txt, score))
        return results
