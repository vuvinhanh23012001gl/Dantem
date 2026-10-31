import os
import threading
import time
from typing import Any

import cv2
import numpy as np


class OCRTextService:
    """Thread-safe OCR wrapper adapted from the OCR demo's PaddleOCR engines."""

    def __init__(self, models: Any = None, score_threshold: float = 0.35) -> None:
        self._models = models
        self._score_threshold = float(score_threshold)
        self._lock = threading.Lock()

    def _get_models(self) -> Any:
        if self._models is None:
            os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
            from paddleocr import (
                TextDetection,
                TextLineOrientationClassification,
                TextRecognition,
            )

            self._models = type(
                "OCRModels",
                (),
                {
                    "detector": TextDetection(
                        model_name="PP-OCRv6_medium_det",
                        device=None,
                    ),
                    "recognizer": TextRecognition(
                        model_name="PP-OCRv6_medium_rec",
                        device=None,
                    ),
                    "orientation": TextLineOrientationClassification(
                        model_name="PP-LCNet_x1_0_textline_ori",
                        device=None,
                    ),
                },
            )()
        return self._models

    def inspect_image(self, image: np.ndarray) -> dict[str, Any]:
        """Recognize text lines and report their confidence and source orientation."""
        if not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Ảnh ROI OCR không được rỗng")
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("Ảnh ROI OCR phải có 1 hoặc 3 kênh màu")

        started_at = time.perf_counter()
        with self._lock:
            models = self._get_models()
            detections = list(models.detector.predict(image))
            detection = detections[0] if detections else {}
            polygons = detection.get("dt_polys", [])
            scores = detection.get("dt_scores", [])
            indexed_polygons = sorted(
                enumerate(polygons),
                key=lambda entry: (
                    float(np.mean(np.asarray(entry[1])[:, 1])) // 15,
                    float(np.min(np.asarray(entry[1])[:, 0])),
                ),
            )

            line_inputs: list[dict[str, Any]] = []
            recognition_crops: list[np.ndarray] = []
            orientation_crops: list[np.ndarray] = []
            for polygon_index, polygon in indexed_polygons:
                crop, is_vertical, skew_angle, bbox, ordered_polygon = (
                    self._crop_text_region(image, polygon)
                )
                if crop.size == 0:
                    continue
                base_crop = np.rot90(crop, 1) if is_vertical else crop
                crop_0 = np.ascontiguousarray(base_crop)
                crop_180 = np.ascontiguousarray(
                    cv2.rotate(base_crop, cv2.ROTATE_180)
                )
                line_inputs.append(
                    {
                        "detection_score": float(scores[polygon_index])
                        if polygon_index < len(scores)
                        else 1.0,
                        "is_vertical": is_vertical,
                        "skew_angle": skew_angle,
                        "bbox": bbox,
                        "polygon": ordered_polygon,
                    }
                )
                orientation_crops.append(crop_0)
                recognition_crops.extend((crop_0, crop_180))

            orientation_predictions = (
                list(models.orientation.predict(orientation_crops))
                if orientation_crops
                else []
            )
            recognition_predictions = (
                list(models.recognizer.predict(recognition_crops))
                if recognition_crops
                else []
            )

            lines: list[dict[str, Any]] = []
            for index, line_input in enumerate(line_inputs):
                result_0 = recognition_predictions[index * 2]
                result_180 = recognition_predictions[index * 2 + 1]
                text_0 = str(result_0.get("rec_text", "")).strip()
                text_180 = str(result_180.get("rec_text", "")).strip()
                score_0 = float(result_0.get("rec_score", 0.0))
                score_180 = float(result_180.get("rec_score", 0.0))

                orientation = orientation_predictions[index]
                orientation_label = str(
                    orientation.get("label_names", ["0_degree"])[0]
                )
                orientation_score = float(orientation.get("scores", [0.0])[0])
                if abs(score_0 - score_180) >= 0.22:
                    use_180 = score_180 > score_0
                else:
                    use_180 = "180" in orientation_label

                text = text_180 if use_180 else text_0
                confidence = score_180 if use_180 else score_0
                if not text or confidence < self._score_threshold:
                    continue
                cardinal_angle = 90 if line_input["is_vertical"] else 0
                if use_180:
                    cardinal_angle = (cardinal_angle + 180) % 360
                lines.append(
                    {
                        "line_id": len(lines),
                        "text": text,
                        "confidence": round(confidence, 4),
                        "angle": cardinal_angle,
                        "orientation_confidence": round(
                            max(orientation_score, confidence), 4
                        ),
                        "skew_angle": line_input["skew_angle"],
                        "bbox": line_input["bbox"],
                        "polygon": line_input["polygon"],
                    }
                )

        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        return {
            "success": bool(lines),
            "total_lines": len(lines),
            "text": "\n".join(line["text"] for line in lines),
            "lines": lines,
            "processing_time_ms": round(elapsed_ms, 2),
            "error_message": None if lines else "No text passed confidence threshold",
        }

    @staticmethod
    def _crop_text_region(
        image: np.ndarray,
        polygon: np.ndarray | list,
    ) -> tuple[np.ndarray, bool, float, list[int], list[list[int]]]:
        points = np.asarray(polygon, dtype=np.float32).reshape(-1, 2)
        if len(points) < 4:
            return np.empty((0, 0, 3), dtype=np.uint8), False, 0.0, [], []

        rectangle = cv2.boxPoints(cv2.minAreaRect(points))
        ordered = sorted(rectangle, key=lambda point: point[0])
        if ordered[1][1] > ordered[0][1]:
            index_a, index_d = 0, 1
        else:
            index_a, index_d = 1, 0
        if ordered[3][1] > ordered[2][1]:
            index_b, index_c = 2, 3
        else:
            index_b, index_c = 3, 2
        quad = np.asarray(
            [ordered[index_a], ordered[index_b], ordered[index_c], ordered[index_d]],
            dtype=np.float32,
        )

        width = max(
            int(np.linalg.norm(quad[0] - quad[1])),
            int(np.linalg.norm(quad[2] - quad[3])),
            1,
        )
        height = max(
            int(np.linalg.norm(quad[0] - quad[3])),
            int(np.linalg.norm(quad[1] - quad[2])),
            1,
        )
        transform = cv2.getPerspectiveTransform(
            quad,
            np.asarray(
                [[0, 0], [width, 0], [width, height], [0, height]],
                dtype=np.float32,
            ),
        )
        crop = cv2.warpPerspective(
            image,
            transform,
            (width, height),
            borderMode=cv2.BORDER_REPLICATE,
            flags=cv2.INTER_CUBIC,
        )
        is_vertical = height / max(width, 1) >= 1.5

        if not is_vertical:
            dx, dy = float(quad[1][0] - quad[0][0]), float(
                quad[1][1] - quad[0][1]
            )
        else:
            dx, dy = float(quad[3][0] - quad[0][0]), float(
                quad[3][1] - quad[0][1]
            )
        skew_angle = float(np.degrees(np.arctan2(dy, dx)))
        if is_vertical:
            skew_angle -= 90.0
        while skew_angle <= -45.0:
            skew_angle += 90.0
        while skew_angle > 45.0:
            skew_angle -= 90.0

        image_height, image_width = image.shape[:2]
        bbox = [
            max(0, int(np.floor(np.min(points[:, 0])))),
            max(0, int(np.floor(np.min(points[:, 1])))),
            min(image_width, int(np.ceil(np.max(points[:, 0])))),
            min(image_height, int(np.ceil(np.max(points[:, 1])))),
        ]
        ordered_points = [
            [int(round(point[0])), int(round(point[1]))] for point in quad
        ]
        return crop, is_vertical, round(skew_angle, 2), bbox, ordered_points
