from collections.abc import Mapping
from typing import Any, List, Dict, Optional
import numpy as np

from app.engines.service.barcode_qr_service import BarcodeQRService
from .base_ai import BaseJudgerAI, JudgmentResult


class BarcodeDetector(BaseJudgerAI):
    """Detector kiểm tra mã vạch Barcode 1D (BarcodeItemInspector)."""

    INSPECTOR_NAME = "BarcodeItemInspector"

    def __init__(self, barcode_service: Optional[BarcodeQRService] = None) -> None:
        super().__init__()
        self.barcode_service = barcode_service or BarcodeQRService()

    def define(
        self,
        image: np.ndarray,
        boxes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Ảnh đầu vào Barcode không được rỗng")
        if not isinstance(boxes, list) or not boxes:
            raise ValueError("Chưa cấu hình khung Barcode")

        height, width = image.shape[:2]
        results: List[Dict[str, Any]] = []
        for index, box in enumerate(boxes, start=1):
            try:
                x1 = int(box.get("x1", box.get("xStart", 0)))
                y1 = int(box.get("y1", box.get("yStart", 0)))
                x2 = int(box.get("x2", box.get("xEnd", 0)))
                y2 = int(box.get("y2", box.get("yEnd", 0)))
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"Tọa độ khung Barcode {index} không hợp lệ") from error

            if x1 < 0 or y1 < 0 or x2 > width or y2 > height or x2 <= x1 or y2 <= y1:
                raise ValueError(f"Tọa độ khung Barcode {index} nằm ngoài ảnh")

            recognized = self.barcode_service.scan_barcode_roi(image, box)
            results.append(
                {
                    "id": box.get("id", index - 1),
                    "key": str(box.get("key", box.get("id", index - 1))),
                    "name": str(box.get("name") or f"Barcode {index}"),
                    "bbox_roi": [x1, y1, x2, y2],
                    "expected_text": str(box.get("expected_text") or ""),
                    "text": str(recognized.get("text") or ""),
                    "format": str(recognized.get("format") or ""),
                    "processing_time_ms": float(recognized.get("processing_time_ms", 0.0)),
                    "has_barcode": bool(recognized.get("success")),
                    "error_message": recognized.get("error_message"),
                }
            )
        return {"boxes": results}

    def compare(
        self,
        standard_data: Any,
        runtime_data: Any,
    ) -> Dict[str, Any]:
        if not isinstance(runtime_data, dict) or not isinstance(
            runtime_data.get("boxes"), list
        ):
            raise ValueError("runtime_data của BarcodeDetector không đúng cấu trúc")

        standard_regions = self._standard_regions(standard_data)
        comparisons: List[Dict[str, Any]] = []
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
            has_barcode = bool(box.get("has_barcode")) and bool(recognized_text)
            is_match = bool(expected_text) and has_barcode and (
                expected_text == recognized_text
            )
            comparisons.append(
                {
                    **box,
                    "expected_text": expected_text,
                    "text": recognized_text,
                    "has_barcode": has_barcode,
                    "ok": is_match,
                }
            )

        return {
            "box_comparisons": comparisons,
            "matched_count": sum(1 for box in comparisons if box["ok"]),
            "total_boxes": len(comparisons),
        }

    def judge(self, comparison_data: Dict[str, Any]) -> JudgmentResult:
        required_keys = {"box_comparisons", "total_boxes", "matched_count"}
        if not isinstance(comparison_data, dict) or not required_keys.issubset(
            comparison_data
        ):
            raise ValueError("comparison_data thiếu dữ liệu Barcode bắt buộc")

        boxes = list(comparison_data["box_comparisons"])
        ok = bool(boxes) and all(box.get("ok") is True for box in boxes)
        errors: List[str] = []
        for box in boxes:
            if box.get("ok"):
                continue
            name = str(box.get("name") or "Khung Barcode")
            expected = str(box.get("expected_text") or "")
            actual = str(box.get("text") or "")
            reason = (
                str(box.get("error_message"))
                if not box.get("has_barcode")
                else f"thực tế: {actual!r}"
            )
            if not expected:
                reason = "chưa cấu hình nội dung Barcode bắt buộc"
            errors.append(
                f'[Barcode] NG - Khung "{name}" - Quy định: {expected!r} - {reason}'
            )

        total = len(boxes)
        matched = int(comparison_data["matched_count"])
        message = (
            f"Nhận diện đúng {matched}/{total} khung Barcode"
            if total
            else "Chưa cấu hình khung Barcode"
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
        """Đo thử 1 vùng ROI cho Barcode phục vụ API chạy thử."""
        key = str(region.get("key", region.get("id", 0)))
        box = {
            "id": region.get("id", key),
            "key": key,
            "name": region.get("name", "Khung Barcode"),
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
    def _standard_regions(standard_data: Any) -> Dict[str, Any]:
        if isinstance(standard_data, dict):
            if isinstance(standard_data.get("boxes"), list):
                return {
                    str(box.get("key", box.get("id", index))): box
                    for index, box in enumerate(standard_data["boxes"])
                    if isinstance(box, dict)
                }
            if isinstance(standard_data.get("expected_texts"), dict):
                return {
                    str(key): {"expected_text": value}
                    for key, value in standard_data["expected_texts"].items()
                }
        return {}
