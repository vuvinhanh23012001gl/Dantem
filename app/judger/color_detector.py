import numpy as np
from typing import Any
from app.engines.service.color_service import ColorService
from .base_ai import BaseJudgerAI, JudgmentResult


class ColorDetector(BaseJudgerAI):
    """Bộ kiểm tra màu ('ColorItemInspector') trên các khung ROI bằng thuật toán CIE2000."""

    INSPECTOR_NAME = "ColorItemInspector"

    def __init__(self, color_service: ColorService):
        super().__init__()
        self.color_service = color_service

    def define(self, img: np.ndarray, boxes: list[dict[str, Any]]) -> dict[str, Any]:
        """Đo màu trung bình và tính khoảng cách màu Delta E cho từng khung ROI."""
        if not isinstance(img, np.ndarray) or img.size == 0:
            raise ValueError("Ảnh đầu vào cho ColorDetector không được rỗng")
        if not isinstance(boxes, list) or not boxes:
            raise ValueError("Danh sách khung kiểm tra màu không được rỗng")

        res = self.color_service.inspect_color_boxes(
            image=img,
            boxes=boxes,
            width_canvas=None,
        )
        if not res.ok:
            raise ValueError(f"Không thể thực thi kiểm tra màu: {res.error}")
        return res.data

    def compare(self, standard_data: Any, runtime_data: Any) -> dict[str, Any]:
        """Đối chiếu sai lệch màu sắc từng vùng với ngưỡng kỹ thuật Delta E max."""
        if not isinstance(runtime_data, dict) or not isinstance(
            runtime_data.get("boxes"), list
        ):
            raise ValueError("runtime_data của ColorDetector không đúng cấu trúc")

        box_comparisons: list[dict[str, Any]] = []
        ok_boxes: list[str] = []
        ng_boxes: list[str] = []

        for idx, box in enumerate(runtime_data["boxes"]):
            if not isinstance(box, dict):
                continue
            box_name = str(box.get("name") or f"Màu {idx + 1}").strip() or f"Màu {idx + 1}"
            status = str(box.get("status", "NG")).upper()
            is_box_ok = status == "OK"

            if is_box_ok:
                ok_boxes.append(box_name)
            else:
                ng_boxes.append(box_name)

            box_comparisons.append(
                {
                    "id": box.get("id", idx),
                    "name": box_name,
                    "status": status,
                    "roi": box.get("roi", []),
                    "measured_rgb": box.get("measured_rgb", [0, 0, 0]),
                    "measured_lab": box.get("measured_lab", [0, 0, 0]),
                    "ref_rgb": box.get("ref_rgb", [0, 0, 0]),
                    "ref_lab": box.get("ref_lab", [0, 0, 0]),
                    "delta_e": box.get("delta_e", 0.0),
                    "delta_e76": box.get("delta_e76", 0.0),
                    "similarity_percent": box.get("similarity_percent", 0.0),
                    "max_delta_e": box.get("max_delta_e", 5.0),
                    "error": box.get("error"),
                    "ok": is_box_ok,
                }
            )

        return {
            "box_comparisons": box_comparisons,
            "ok_boxes": ok_boxes,
            "ng_boxes": ng_boxes,
            "total_boxes": len(box_comparisons),
            "overall": runtime_data.get("overall", False),
        }

    def judge(self, comparison_data: dict[str, Any]) -> JudgmentResult:
        """Phán định tổng cho item: tất cả vùng màu đạt -> OK; bất kỳ vùng nào vượt ngưỡng -> NG."""
        required_keys = {"box_comparisons", "ng_boxes", "total_boxes"}
        if not isinstance(comparison_data, dict) or not required_keys.issubset(
            comparison_data
        ):
            raise ValueError("comparison_data thiếu dữ liệu ColorDetector bắt buộc")

        total_boxes = int(comparison_data["total_boxes"])
        ng_boxes = list(comparison_data["ng_boxes"])
        ok_boxes = list(comparison_data.get("ok_boxes", []))
        box_comparisons = list(comparison_data["box_comparisons"])

        ok = total_boxes > 0 and len(ng_boxes) == 0
        errors: list[str] = []

        if total_boxes == 0:
            errors.append("[Kiểm tra màu] NG - Chưa cấu hình vùng màu nào")
        elif not ok:
            for box in box_comparisons:
                if not box["ok"]:
                    box_name = box["name"]
                    de = box.get("delta_e", 0.0)
                    mde = box.get("max_delta_e", 5.0)
                    err_msg = box.get("error") or f"Lệch màu ΔE={de} > {mde}"
                    errors.append(f"[Kiểm tra màu] NG - Khung \"{box_name}\" ({err_msg})")
        else:
            first_m = box_comparisons[0]
            sim = first_m.get("similarity_percent", 100.0)
            message = (
                f"[Kiểm tra màu] OK - Toàn bộ {total_boxes} vùng màu đạt chuẩn "
                f"(Độ tương đồng ~{sim}%)"
            )

        status_text = "OK" if ok else "NG"
        if not ok and not errors:
            errors.append(f"[Kiểm tra màu] NG - Có {len(ng_boxes)}/{total_boxes} vùng màu không đạt")

        message = (
            f"[Kiểm tra màu] OK - {len(ok_boxes)}/{total_boxes} vùng màu đạt chuẩn"
            if ok
            else "; ".join(errors)
        )

        return JudgmentResult(
            ok=ok,
            status=status_text,
            standard_data={"total_boxes": total_boxes},
            runtime_data={"box_comparisons": box_comparisons},
            comparison_data=comparison_data,
            message=message,
            errors=errors,
        )
