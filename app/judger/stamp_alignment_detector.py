import numpy as np
from typing import Any
from app.engines.service.stamp_alignment_service import StampAlignmentService
from .base_ai import BaseJudgerAI, JudgmentResult


class StampAlignmentDetector(BaseJudgerAI):
    """Bộ kiểm tra độ lệch tem ('StampAlignmentInspector') trên các khung ROI bằng mô hình YOLO OBB."""

    INSPECTOR_NAME = "StampAlignmentInspector"

    def __init__(self, stamp_alignment_service: StampAlignmentService):
        super().__init__()
        self.stamp_alignment_service = stamp_alignment_service

    def define(self, img: np.ndarray, boxes: list[dict[str, Any]]) -> dict[str, Any]:
        """Nhận diện OBB và kiểm tra độ lệch tem trong từng khung ROI được cấu hình."""
        if not isinstance(img, np.ndarray) or img.size == 0:
            raise ValueError("Ảnh đầu vào cho StampAlignmentDetector không được rỗng")
        if not isinstance(boxes, list) or not boxes:
            raise ValueError("Danh sách khung kiểm tra lệch tem không được rỗng")

        res = self.stamp_alignment_service.inspect_alignment_boxes(
            image=img,
            boxes=boxes,
            width_canvas=None,
        )
        if not res.ok:
            raise ValueError(f"Không thể thực thi kiểm tra lệch tem: {res.error}")
        return res.data

    def compare(self, standard_data: Any, runtime_data: Any) -> dict[str, Any]:
        """Đối chiếu kết quả đo độ lệch của từng khung với tiêu chuẩn kỹ thuật."""
        if not isinstance(runtime_data, dict) or not isinstance(
            runtime_data.get("boxes"), list
        ):
            raise ValueError("runtime_data của StampAlignmentDetector không đúng cấu trúc")

        box_comparisons: list[dict[str, Any]] = []
        ok_boxes: list[str] = []
        ng_boxes: list[str] = []

        for idx, box in enumerate(runtime_data["boxes"]):
            if not isinstance(box, dict):
                continue
            box_name = str(box.get("name") or f"Tem {idx + 1}").strip() or f"Tem {idx + 1}"
            status = str(box.get("status", "NG")).upper()
            is_box_ok = status == "OK"

            if is_box_ok:
                ok_boxes.append(box_name)
            else:
                ng_boxes.append(box_name)

            box_comparisons.append(
                {
                    "id": box.get("id", idx),
                    "key": str(box.get("key", box.get("id", idx))),
                    "name": box_name,
                    "bbox_roi": box.get("bbox_roi", []),
                    "status": status,
                    "error": box.get("error"),
                    "metrics": box.get("metrics", {}),
                    "details": box.get("details", {}),
                    "tolerances": box.get("tolerances", {}),
                    "ok": is_box_ok,
                }
            )

        return {
            "box_comparisons": box_comparisons,
            "ok_boxes": ok_boxes,
            "ng_boxes": ng_boxes,
            "total_boxes": len(box_comparisons),
            "objects": runtime_data.get("objects", []),
            "image": runtime_data.get("image"),
        }

    def judge(self, comparison_data: dict[str, Any]) -> JudgmentResult:
        """Phán định tổng cho item: tất cả khung đạt (OK) -> OK; bất kỳ khung nào NG -> NG."""
        required_keys = {"box_comparisons", "ng_boxes", "total_boxes"}
        if not isinstance(comparison_data, dict) or not required_keys.issubset(
            comparison_data
        ):
            raise ValueError("comparison_data thiếu dữ liệu StampAlignmentDetector bắt buộc")

        total_boxes = int(comparison_data["total_boxes"])
        ng_boxes = list(comparison_data["ng_boxes"])
        ok_boxes = list(comparison_data.get("ok_boxes", []))
        box_comparisons = list(comparison_data["box_comparisons"])

        ok = total_boxes > 0 and len(ng_boxes) == 0
        errors: list[str] = []

        if total_boxes == 0:
            errors.append("[Kiểm tra lệch tem] NG - Chưa cấu hình khung kiểm tra nào")
        elif not ok:
            for box in box_comparisons:
                if not box["ok"]:
                    box_name = box["name"]
                    err_reason = box.get("error")
                    metrics = box.get("metrics", {})
                    if err_reason:
                        errors.append(f'[Kiểm tra lệch tem] NG - Khung "{box_name}": {err_reason}')
                    else:
                        details = box.get("details", {})
                        fail_parts = []
                        if not details.get("pass_position_u", True):
                            fail_parts.append(f"Lệch ngang Δu={metrics.get('du')}px")
                        if not details.get("pass_position_v", True):
                            fail_parts.append(f"Lệch dọc Δv={metrics.get('dv')}px")
                        if not details.get("pass_rotation", True):
                            fail_parts.append(f"Lệch góc Δθ={metrics.get('delta_angle_deg')}°")
                        if not details.get("pass_containment", True):
                            fail_parts.append("Vi phạm bao hàm (chạm viền)")
                        reason_str = ", ".join(fail_parts) if fail_parts else "Vượt ngưỡng dung sai"
                        errors.append(f'[Kiểm tra lệch tem] NG - Khung "{box_name}": {reason_str}')

        if ok:
            message = f"Tem chuẩn vị trí trên tất cả {total_boxes}/{total_boxes} khung"
        elif ng_boxes:
            ng_str = ", ".join(f'"{name}"' for name in ng_boxes)
            message = f"Tem lệch tại {len(ng_boxes)}/{total_boxes} khung ({ng_str})"
        else:
            message = "Chưa cấu hình khung kiểm tra độ lệch tem"

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
                "objects": comparison_data.get("objects", []),
                "image": comparison_data.get("image"),
            },
            comparison_data=comparison_data,
            message=message,
            errors=errors,
        )
