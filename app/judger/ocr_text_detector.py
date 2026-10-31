from collections.abc import Mapping
from typing import Any

import numpy as np

from app.engines.ocr_text_service import OCRTextService
from .base_ai import BaseJudgerAI, JudgmentResult


class OCRTextDetector(BaseJudgerAI):
    INSPECTOR_NAME = "OCRTextInspector"

    def __init__(self, ocr_service: OCRTextService | None = None) -> None:
        super().__init__()
        self.ocr_service = ocr_service or OCRTextService()

    def define(
        self,
        image: np.ndarray,
        boxes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Ảnh đầu vào OCR không được rỗng")
        if not isinstance(boxes, list) or not boxes:
            raise ValueError("Chưa cấu hình khung OCR")

        height, width = image.shape[:2]
        results: list[dict[str, Any]] = []
        for index, box in enumerate(boxes, start=1):
            try:
                x1 = int(box["x1"])
                y1 = int(box["y1"])
                x2 = int(box["x2"])
                y2 = int(box["y2"])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"Tọa độ khung OCR {index} không hợp lệ") from error
            if x1 < 0 or y1 < 0 or x2 > width or y2 > height or x2 <= x1 or y2 <= y1:
                raise ValueError(f"Tọa độ khung OCR {index} nằm ngoài ảnh")

            recognized = self.ocr_service.inspect_image(image[y1:y2, x1:x2])
            results.append(
                {
                    "id": box.get("id", index - 1),
                    "key": str(box.get("key", box.get("id", index - 1))),
                    "name": str(box.get("name") or f"Vùng OCR {index}"),
                    "bbox_roi": [x1, y1, x2, y2],
                    "expected_text": str(box.get("expected_text") or ""),
                    "text": str(recognized.get("text") or ""),
                    "lines": recognized.get("lines", []),
                    "confidence": self._average_confidence(recognized.get("lines", [])),
                    "processing_time_ms": float(
                        recognized.get("processing_time_ms", 0.0)
                    ),
                    "has_text": bool(recognized.get("success")),
                    "error_message": recognized.get("error_message"),
                }
            )
        return {"boxes": results}

    def compare(
        self,
        standard_data: Any,
        runtime_data: Any,
    ) -> dict[str, Any]:
        if not isinstance(runtime_data, dict) or not isinstance(
            runtime_data.get("boxes"), list
        ):
            raise ValueError("runtime_data của OCRTextDetector không đúng cấu trúc")

        standard_regions = self._standard_regions(standard_data)
        comparisons: list[dict[str, Any]] = []
        for box in runtime_data["boxes"]:
            key = str(box.get("key", box.get("id", "")))
            standard_region = standard_regions.get(key, {})
            if not isinstance(standard_region, Mapping):
                standard_region = {}
            expected_text = str(
                standard_region.get("expected_text", box.get("expected_text", ""))
                or ""
            ).strip()
            recognized_text = str(box.get("text") or "").strip()
            has_text = bool(box.get("has_text")) and bool(recognized_text)
            is_match = bool(expected_text) and has_text and (
                expected_text == recognized_text
            )
            comparisons.append(
                {
                    **box,
                    "expected_text": expected_text,
                    "text": recognized_text,
                    "has_text": has_text,
                    "ok": is_match,
                }
            )

        return {
            "box_comparisons": comparisons,
            "matched_count": sum(1 for box in comparisons if box["ok"]),
            "total_boxes": len(comparisons),
        }

    def judge(self, comparison_data: dict[str, Any]) -> JudgmentResult:
        required_keys = {"box_comparisons", "total_boxes", "matched_count"}
        if not isinstance(comparison_data, dict) or not required_keys.issubset(
            comparison_data
        ):
            raise ValueError("comparison_data thiếu dữ liệu OCR bắt buộc")

        boxes = list(comparison_data["box_comparisons"])
        ok = bool(boxes) and all(box.get("ok") is True for box in boxes)
        errors: list[str] = []
        for box in boxes:
            if box.get("ok"):
                continue
            name = str(box.get("name") or "Vùng OCR")
            expected = str(box.get("expected_text") or "")
            actual = str(box.get("text") or "")
            reason = (
                str(box.get("error_message"))
                if not box.get("has_text")
                else f"thực tế: {actual!r}"
            )
            if not expected:
                reason = "chưa cấu hình nội dung OCR bắt buộc"
            errors.append(
                f'[OCR] NG - Khung "{name}" - Quy định: {expected!r} - {reason}'
            )

        total = len(boxes)
        matched = int(comparison_data["matched_count"])
        message = (
            f"Nhận diện đúng {matched}/{total} khung OCR"
            if total
            else "Chưa cấu hình khung OCR"
        )
        return JudgmentResult(
            ok=ok,
            status="OK" if ok else "NG",
            standard_data={
                "total_boxes": total,
                "expected_texts": {
                    str(box.get("key", box.get("id", index))): box.get(
                        "expected_text", ""
                    )
                    for index, box in enumerate(boxes)
                },
            },
            runtime_data={
                "matched_count": matched,
                "total_boxes": total,
                "boxes": boxes,
            },
            comparison_data=comparison_data,
            message=message,
            errors=errors,
        )

    def evaluate_roi(
        self,
        image: np.ndarray,
        region: Mapping[str, Any],
    ) -> JudgmentResult:
        """Run OCR for exactly one configured region, as used by the manual API."""
        key = str(region.get("key", region.get("id", 0)))
        box = {
            "id": region.get("id", key),
            "key": key,
            "name": region.get("name", "Vùng OCR"),
            "x1": region.get("x1", region.get("xStart")),
            "y1": region.get("y1", region.get("yStart")),
            "x2": region.get("x2", region.get("xEnd")),
            "y2": region.get("y2", region.get("yEnd")),
            "expected_text": region.get("expected_text", ""),
        }
        runtime_data = self.define(image, [box])
        standard_data = {self.INSPECTOR_NAME: {key: dict(region)}}
        comparison_data = self.compare(standard_data, runtime_data)
        return self.judge(comparison_data)

    @staticmethod
    def _standard_regions(standard_data: Any) -> dict[str, Any]:
        if not isinstance(standard_data, Mapping):
            return {}
        regions = standard_data.get(OCRTextDetector.INSPECTOR_NAME, standard_data)
        if not isinstance(regions, Mapping):
            return {}
        if any(key in regions for key in ("xStart", "x1")):
            return {str(regions.get("id", 0)): regions}
        return {str(key): value for key, value in regions.items()}

    @staticmethod
    def _average_confidence(lines: Any) -> float:
        if not isinstance(lines, list) or not lines:
            return 0.0
        scores = [
            float(line.get("confidence", 0.0))
            for line in lines
            if isinstance(line, Mapping)
        ]
        return round(sum(scores) / len(scores), 4) if scores else 0.0
