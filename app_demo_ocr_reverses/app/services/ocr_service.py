from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np

from app.core.constants import InspectionJudgement
from app.core.geometry import crop_text_region, read_image_unicode
from app.core.logger import get_logger
from app.models.ocr_engine import OCREngine
from app.models.orientation_engine import OrientationEngine
from app.schemas.ocr_schema import (
    DocumentOrientationInfo,
    OCRInspectionResult,
    TextLineResult,
)
from app.services.orientation_service import OrientationService
from config import load_settings

logger = get_logger(__name__)


class OCRService:
    """
    High-level service orchestrating end-to-end OCR content recognition
    and orientation inspection (0°, 90°, 180°, 270°, Mirror, Skew/Tilt)
    while strictly preserving the original image's coordinate system and orientation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config if config is not None else load_settings()
        models_cfg = self.config.get("models", {})
        det_cfg = self.config.get("detection", {})
        rec_cfg = self.config.get("recognition", {})
        ori_cfg = self.config.get("orientation", {})

        self.score_thresh: float = float(rec_cfg.get("score_thresh", 0.35))
        self.vertical_aspect_ratio_thresh: float = float(
            ori_cfg.get("vertical_aspect_ratio_thresh", 1.5)
        )

        device = models_cfg.get("device", None)
        self.orientation_engine = OrientationEngine(
            doc_model_name=models_cfg.get(
                "doc_orientation_model_name", "PP-LCNet_x1_0_doc_ori"
            ),
            textline_model_name=models_cfg.get(
                "textline_orientation_model_name", "PP-LCNet_x1_0_textline_ori"
            ),
            device=device,
        )
        self.ocr_engine = OCREngine(
            det_model_name=models_cfg.get(
                "text_detection_model_name", "PP-OCRv6_medium_det"
            ),
            rec_model_name=models_cfg.get(
                "text_recognition_model_name", "PP-OCRv6_medium_rec"
            ),
            device=device,
            det_params={
                "limit_side_len": int(det_cfg.get("limit_side_len", 960)),
                "limit_type": str(det_cfg.get("limit_type", "max")),
                "thresh": float(det_cfg.get("thresh", 0.3)),
                "box_thresh": float(det_cfg.get("box_thresh", 0.55)),
                "unclip_ratio": float(det_cfg.get("unclip_ratio", 1.8)),
            },
        )
        self.orientation_service = OrientationService(
            orientation_engine=self.orientation_engine,
            config=self.config,
        )

    def inspect_image(
        self,
        image_input: Union[str, Path, np.ndarray],
        image_name: str = "input_image.png",
    ) -> Tuple[OCRInspectionResult, Optional[np.ndarray]]:
        """
        Run full OCR and orientation analysis on an image path or BGR numpy array.

        Returns:
            (OCRInspectionResult, raw_bgr_image)
        """
        t_start = time.perf_counter()
        image_path_str = ""

        try:
            if isinstance(image_input, (str, Path)):
                path_obj = Path(image_input)
                image_name = path_obj.name
                image_path_str = str(path_obj.resolve())
                raw_img = read_image_unicode(path_obj)
            elif isinstance(image_input, np.ndarray):
                raw_img = image_input.copy()
            else:
                raise TypeError(f"Unsupported image_input type: {type(image_input)}")
        except Exception as exc:
            elapsed = (time.perf_counter() - t_start) * 1000.0
            logger.error("Failed to load image %s: %s", image_name, exc)
            return (
                OCRInspectionResult(
                    image=image_name,
                    image_path=image_path_str,
                    success=False,
                    total_lines=0,
                    orientation=DocumentOrientationInfo(status="UNKNOWN"),
                    texts=[],
                    result=InspectionJudgement.NG.value,
                    reason=f"Lỗi đọc file ảnh: {exc}",
                    processing_time_ms=round(elapsed, 2),
                    error_message=str(exc),
                ),
                None,
            )

        try:
            # Step 1: Whole-document orientation classification on the RAW original image
            doc_angle, doc_conf = self.orientation_engine.classify_document(raw_img)

            # Step 2: Detect text regions directly on the original image (preserving original coordinates)
            polys, det_scores, working_img = self.ocr_engine.detect_text_regions(raw_img)

            if not polys:
                elapsed = (time.perf_counter() - t_start) * 1000.0
                doc_info, judgement, reason = (
                    self.orientation_service.aggregate_document_orientation(
                        lines=[],
                        doc_model_angle=doc_angle,
                        doc_model_confidence=doc_conf,
                    )
                )
                return (
                    OCRInspectionResult(
                        image=image_name,
                        image_path=image_path_str,
                        success=False,
                        total_lines=0,
                        orientation=doc_info,
                        texts=[],
                        result=judgement,
                        reason=reason,
                        processing_time_ms=round(elapsed, 2),
                        error_message="No text regions detected",
                    ),
                    raw_img,
                )

            # Step 3: Crop each detected polygon and prepare 4 orientation hypotheses per line
            line_meta: List[Dict[str, Any]] = []
            ori_batch_crops: List[np.ndarray] = []
            rec_batch_crops: List[np.ndarray] = []

            for poly in polys:
                (
                    crop,
                    w,
                    h,
                    is_vertical,
                    skew_angle,
                    bbox,
                    polygon,
                ) = crop_text_region(
                    working_img,
                    poly,
                    vertical_aspect_ratio_thresh=self.vertical_aspect_ratio_thresh,
                )
                if crop.size == 0 or w == 0 or h == 0:
                    continue

                # If box is vertical (h/w >= 1.5), rotate 90° CCW so a 90°-CW text line becomes horizontal 0°
                base_crop = np.rot90(crop, 1) if is_vertical else crop
                c_0 = np.ascontiguousarray(base_crop)
                c_180 = np.ascontiguousarray(cv2.rotate(base_crop, cv2.ROTATE_180))
                c_m0 = np.ascontiguousarray(cv2.flip(c_0, 1))
                c_m180 = np.ascontiguousarray(cv2.flip(c_180, 1))

                line_meta.append(
                    {
                        "is_vertical": is_vertical,
                        "skew_angle": skew_angle,
                        "bbox": bbox,
                        "polygon": polygon,
                    }
                )
                # 2 crops per line for textline orientation classifier: c_0 and c_m0
                ori_batch_crops.extend([c_0, c_m0])
                # 4 crops per line for text recognition: c_0, c_180, c_m0, c_m180
                rec_batch_crops.extend([c_0, c_180, c_m0, c_m180])

            # Step 4: Run batched orientation classification and text recognition
            ori_preds = self.orientation_engine.classify_textline_batch(ori_batch_crops)
            rec_preds = self.ocr_engine.recognize_batch(rec_batch_crops)

            # Step 5: Resolve each line's orientation and filter low-confidence noise
            resolved_lines: List[TextLineResult] = []
            valid_line_idx = 0

            for i, meta in enumerate(line_meta):
                ori_c0 = ori_preds[2 * i]
                ori_cm0 = ori_preds[2 * i + 1]

                rec_c0 = rec_preds[4 * i]
                rec_c180 = rec_preds[4 * i + 1]
                rec_cm0 = rec_preds[4 * i + 2]
                rec_cm180 = rec_preds[4 * i + 3]

                line_res = self.orientation_service.resolve_line_orientation(
                    line_id=valid_line_idx,
                    is_vertical=meta["is_vertical"],
                    skew_angle=meta["skew_angle"],
                    bbox=meta["bbox"],
                    polygon=meta["polygon"],
                    ori_c0=ori_c0,
                    ori_cm0=ori_cm0,
                    rec_c0=rec_c0,
                    rec_c180=rec_c180,
                    rec_cm0=rec_cm0,
                    rec_cm180=rec_cm180,
                )
                if line_res is not None and line_res.confidence >= self.score_thresh:
                    resolved_lines.append(line_res)
                    valid_line_idx += 1

            # Step 6: Aggregate document-level orientation and OK/NG judgement
            doc_info, judgement, reason = (
                self.orientation_service.aggregate_document_orientation(
                    lines=resolved_lines,
                    doc_model_angle=doc_angle,
                    doc_model_confidence=doc_conf,
                )
            )

            elapsed = (time.perf_counter() - t_start) * 1000.0
            success = len(resolved_lines) > 0

            result_obj = OCRInspectionResult(
                image=image_name,
                image_path=image_path_str,
                success=success,
                total_lines=len(resolved_lines),
                orientation=doc_info,
                texts=resolved_lines,
                result=judgement,
                reason=reason,
                processing_time_ms=round(elapsed, 2),
                error_message=None if success else "No text passed confidence threshold",
            )
            return result_obj, raw_img

        except Exception as exc:
            elapsed = (time.perf_counter() - t_start) * 1000.0
            logger.exception("Error during OCR inspection on %s: %s", image_name, exc)
            return (
                OCRInspectionResult(
                    image=image_name,
                    image_path=image_path_str,
                    success=False,
                    total_lines=0,
                    orientation=DocumentOrientationInfo(status="UNKNOWN"),
                    texts=[],
                    result=InspectionJudgement.NG.value,
                    reason=f"Lỗi xử lý OCR: {exc}",
                    processing_time_ms=round(elapsed, 2),
                    error_message=str(exc),
                ),
                raw_img,
            )
