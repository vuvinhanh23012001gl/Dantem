import numpy as np
from typing import Any
from app.config import ClassNameObjectStructureDetectConfig
from app.engines.AI_model_process import FrameModelYoloObject
from app.engines.service import StructureFaceYoloService
from .base_ai import BaseJudgerAI, JudgmentResult


class StampDetector(BaseJudgerAI):
    """Bộ kiểm tra sự hiện diện Có/Không tem ('stamp') trên nhiều khung ROI của một item."""

    INSPECTOR_NAME = "StampItemInspector"

    def __init__(
        self,
        stamp_model_or_service: StructureFaceYoloService | FrameModelYoloObject,
    ):
        super().__init__()
        if isinstance(stamp_model_or_service, StructureFaceYoloService):
            self.stamp_service = stamp_model_or_service
        else:
            self.stamp_service = StructureFaceYoloService(stamp_model_or_service)

    def define(self, img: np.ndarray, boxes: list[dict[str, Any]]) -> dict[str, Any]:
        """Nhận diện đối tượng nhãn 'stamp' bên trong từng khung vuông được cấu hình.

        Args:
            img: Ảnh gốc đầu vào (NumPy BGR).
            boxes: Danh sách dict khung ROI ``[{id, key, name, x1, y1, x2, y2}, ...]``.

        Returns:
            dict chứa kết quả nhận diện theo từng khung, danh sách objects tổng và ảnh minh họa.
        """
        if not isinstance(img, np.ndarray) or img.size == 0:
            raise ValueError("Ảnh đầu vào cho StampDetector không được rỗng")
        if not isinstance(boxes, list) or not boxes:
            raise ValueError("Danh sách khung kiểm tra tem không được rỗng")

        res = self.stamp_service.inspect_stamp_boxes(
            image=img,
            boxes=boxes,
            label=ClassNameObjectStructureDetectConfig.STAMP.value,
            width_canvas=None,
        )
        if not res.ok:
            raise ValueError(f"Không thể thực thi nhận diện tem: {res.error}")
        return res.data

    def compare(self, standard_data: Any, runtime_data: Any) -> dict[str, Any]:
        """Đối chiếu kết quả nhận diện từng khung với quy định chuẩn 'Phải có tem'."""
        if not isinstance(runtime_data, dict) or not isinstance(
            runtime_data.get("boxes"), list
        ):
            raise ValueError("runtime_data của StampDetector không đúng cấu trúc")

        box_comparisons: list[dict[str, Any]] = []
        present_boxes: list[str] = []
        missing_boxes: list[str] = []

        for idx, box in enumerate(runtime_data["boxes"]):
            if not isinstance(box, dict):
                continue
            box_name = str(box.get("name") or f"Tem {idx + 1}").strip() or f"Tem {idx + 1}"
            runtime_exists = bool(box.get("exists", False))
            runtime_count = int(box.get("count", 0))
            standard_exists = True  # Mặc định mọi khung đều bắt buộc phải có tem
            is_box_ok = runtime_exists == standard_exists

            if is_box_ok:
                present_boxes.append(box_name)
            else:
                missing_boxes.append(box_name)

            box_comparisons.append(
                {
                    "id": box.get("id", idx),
                    "key": str(box.get("key", box.get("id", idx))),
                    "name": box_name,
                    "bbox_roi": box.get("bbox_roi", []),
                    "standard_exists": standard_exists,
                    "runtime_exists": runtime_exists,
                    "runtime_count": runtime_count,
                    "ok": is_box_ok,
                }
            )

        return {
            "box_comparisons": box_comparisons,
            "present_boxes": present_boxes,
            "missing_boxes": missing_boxes,
            "total_boxes": len(box_comparisons),
            "objects": runtime_data.get("objects", []),
            "image": runtime_data.get("image"),
        }

    def judge(self, comparison_data: dict[str, Any]) -> JudgmentResult:
        """Phán định tổng cho item: tất cả khung có tem -> OK; thiếu >= 1 khung -> NG."""
        required_keys = {"box_comparisons", "missing_boxes", "total_boxes"}
        if not isinstance(comparison_data, dict) or not required_keys.issubset(
            comparison_data
        ):
            raise ValueError("comparison_data thiếu dữ liệu StampDetector bắt buộc")

        total_boxes = int(comparison_data["total_boxes"])
        missing_boxes = list(comparison_data["missing_boxes"])
        present_boxes = list(comparison_data.get("present_boxes", []))
        box_comparisons = list(comparison_data["box_comparisons"])

        ok = total_boxes > 0 and len(missing_boxes) == 0
        errors: list[str] = []

        if total_boxes == 0:
            errors.append("[Kiểm tra tem] NG - Chưa cấu hình khung kiểm tra tem nào")
        elif not ok:
            for box_name in missing_boxes:
                errors.append(
                    f'[Kiểm tra tem] NG - Khung "{box_name}" - Quy định: "Có tem" - Thực tế: "Không có tem"'
                )

        if ok:
            message = f"Đủ tem trên tất cả {total_boxes}/{total_boxes} khung"
        elif missing_boxes:
            missing_str = ", ".join(f'"{name}"' for name in missing_boxes)
            message = (
                f"Thiếu tem tại {len(missing_boxes)}/{total_boxes} khung ({missing_str})"
            )
        else:
            message = "Chưa cấu hình khung kiểm tra tem"

        return JudgmentResult(
            ok=ok,
            status="OK" if ok else "NG",
            standard_data={
                "expected_all_present": True,
                "total_boxes": total_boxes,
            },
            runtime_data={
                "present_count": len(present_boxes),
                "missing_count": len(missing_boxes),
                "present_boxes": present_boxes,
                "missing_boxes": missing_boxes,
                "boxes": box_comparisons,
                "objects": comparison_data.get("objects", []),
                "image": comparison_data.get("image"),
            },
            comparison_data=comparison_data,
            message=message,
            errors=errors,
        )
