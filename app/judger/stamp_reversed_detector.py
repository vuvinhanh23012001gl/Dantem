from typing import Any
import numpy as np
from app.engines.service.stamp_reversed_service import StampReversedService
from .base_ai import BaseJudgerAI, JudgmentResult


class StampReversedDetector(BaseJudgerAI):
    """
    Bộ kiểm tra tem in ngược ('StampReversedInspector') trên các khung ROI bằng mô hình YOLO OBB + PaddleOCR.
    """

    INSPECTOR_NAME = "StampReversedInspector"

    def __init__(self, stamp_reversed_service: StampReversedService):
        super().__init__()
        self.stamp_reversed_service = stamp_reversed_service

    def define(self, img: np.ndarray, boxes: list[dict[str, Any]]) -> dict[str, Any]:
        """Xác định hướng chữ và hướng tem trong từng khung ROI."""
        if not isinstance(img, np.ndarray) or img.size == 0:
            raise ValueError("Ảnh đầu vào cho StampReversedDetector không được rỗng")
        if not isinstance(boxes, list) or not boxes:
            raise ValueError("Danh sách khung kiểm tra tem in ngược không được rỗng")

        return self.stamp_reversed_service.inspect_boxes(image=img, boxes=boxes)

    def compare(self, standard_data: Any, runtime_data: Any) -> dict[str, Any]:
        """Đối chiếu kết quả kiểm tra với tiêu chuẩn kỹ thuật."""
        if not isinstance(runtime_data, dict) or not isinstance(
            runtime_data.get("boxes"), list
        ):
            raise ValueError("runtime_data của StampReversedDetector không đúng cấu trúc")

        box_comparisons: list[dict[str, Any]] = []
        ok_boxes: list[str] = []
        ng_boxes: list[str] = []

        for idx, box in enumerate(runtime_data["boxes"]):
            if not isinstance(box, dict):
                continue
            box_name = str(box.get("name") or f"Tem ngược {idx + 1}").strip()
            status = str(box.get("status", "NG")).upper()
            is_box_ok = (status == "OK")

            if is_box_ok:
                ok_boxes.append(box_name)
            else:
                ng_boxes.append(box_name)

            box_comparisons.append({
                "id": box.get("id", idx),
                "name": box_name,
                "status": status,
                "error_code": box.get("error_code", "NONE"),
                "message": box.get("message", ""),
                "text_angle": box.get("text_angle", 0),
                "obb_angle": box.get("obb_angle", 0.0),
                "text_preview": box.get("text_preview", ""),
                "confidence": box.get("confidence", 0.0),
                "ok": is_box_ok,
            })

        return {
            "box_comparisons": box_comparisons,
            "ok_boxes": ok_boxes,
            "ng_boxes": ng_boxes,
            "total_boxes": len(box_comparisons),
        }

    def judge(self, comparison_data: dict[str, Any]) -> JudgmentResult:
        """Phán định tổng cho item: toàn bộ khung OK -> OK; bất kỳ khung nào NG/UNKNOWN -> NG."""
        required_keys = {"box_comparisons", "ng_boxes", "total_boxes"}
        if not isinstance(comparison_data, dict) or not required_keys.issubset(comparison_data):
            raise ValueError("comparison_data thiếu dữ liệu StampReversedDetector bắt buộc")

        total_boxes = int(comparison_data["total_boxes"])
        ng_boxes = list(comparison_data["ng_boxes"])
        ok_boxes = list(comparison_data.get("ok_boxes", []))
        box_comparisons = list(comparison_data["box_comparisons"])

        ok = total_boxes > 0 and len(ng_boxes) == 0
        errors: list[str] = []

        if total_boxes == 0:
            errors.append("[Kiểm tra tem in ngược] NG - Chưa cấu hình khung kiểm tra nào")
        elif not ok:
            for box in box_comparisons:
                if not box["ok"]:
                    box_name = box["name"]
                    err_code = box.get("error_code", "NG")
                    msg = box.get("message", "")
                    errors.append(f"[Kiểm tra tem in ngược] NG - Khung '{box_name}': {msg} ({err_code})")

        if ok:
            message = f"Tem in đúng chiều trên tất cả {total_boxes}/{total_boxes} khung"
        elif ng_boxes:
            ng_str = ", ".join(f'"{name}"' for name in ng_boxes)
            message = f"Phát hiện lỗi tem in ngược/lệch tại {len(ng_boxes)}/{total_boxes} khung ({ng_str})"
        else:
            message = "Chưa cấu hình khung kiểm tra tem in ngược"

        return JudgmentResult(
            ok=ok,
            status="OK" if ok else "NG",
            standard_data={
                "expected_all_ok": True,
                "total_boxes": total_boxes,
            },
            runtime_data={
                "ok_count": len(ok_boxes),
                "ng_count": len(ng_boxes),
                "ok_boxes": ok_boxes,
                "ng_boxes": ng_boxes,
                "boxes": box_comparisons,
            },
            comparison_data=comparison_data,
            message=message,
            errors=errors,
        )
