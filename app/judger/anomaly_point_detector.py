import threading
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.engines.AI_model_process.frame_patch_core_process import FrameModelPatchCore
from app.utils.opencv_tool import Tool_OpenCv2
from .base_ai import BaseJudgerAI, JudgmentResult


class AnomalyPointDetector(BaseJudgerAI):
    """Bộ phán định Điểm bất thường đa vùng (Multi-ROI PatchCore).

    Cho phép cấu hình nhiều khung chữ nhật trên cùng 1 item. Mỗi khung có tên,
    ngưỡng điểm bất thường (threshold) và model PatchCore độc lập (theo roi_id).
    """

    INSPECTOR_NAME = "AnomalyPointInspector"

    def __init__(
        self,
        anomaly_point_model: Optional[FrameModelPatchCore] = None,
        anomaly_point_service: Optional[Any] = None,
    ) -> None:
        """Khởi tạo detector kiểm tra điểm bất thường đa vùng.

        Args:
            anomaly_point_model: Instance FrameModelPatchCore cố định (phục vụ test đơn lập).
            anomaly_point_service: Service nạp động model PatchCore theo (product_id, frame_id, item_id, roi_id).
        """
        super().__init__()
        if anomaly_point_model is None and anomaly_point_service is None:
            raise TypeError("anomaly_point_model hoặc anomaly_point_service phải được cung cấp")
        if anomaly_point_model is not None and not hasattr(
            anomaly_point_model, "predict_with_anomaly_boxes"
        ):
            raise TypeError(
                "anomaly_point_model phải có phương thức predict_with_anomaly_boxes"
            )
        self.anomaly_point_model = anomaly_point_model
        self.anomaly_point_service = anomaly_point_service

    @staticmethod
    def _normalize_boxes_input(
        boxes_or_x1: Sequence[Mapping[str, Any]] | int,
        legacy_coords: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Chuẩn hóa tham số đầu vào thành danh sách cấu hình các khung ROI."""
        if isinstance(boxes_or_x1, (int, float, np.integer)):
            if len(legacy_coords) < 3:
                raise ValueError("Thiếu tọa độ ROI (x1, y1, x2, y2)")
            x1 = int(boxes_or_x1)
            y1, x2, y2 = (int(v) for v in legacy_coords[:3])
            roi_id = kwargs.get("roi_id", 0)
            return [
                {
                    "id": roi_id,
                    "key": str(roi_id),
                    "name": str(kwargs.get("name") or "Điểm bất thường 1"),
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "threshold": float(kwargs.get("threshold", 0.2)),
                    "saveRuntimeImages": bool(kwargs.get("saveRuntimeImages", False)),
                }
            ]

        if not isinstance(boxes_or_x1, Sequence) or isinstance(boxes_or_x1, (str, bytes)):
            raise ValueError("boxes phải là danh sách các khung kiểm tra điểm bất thường")

        normalized: List[Dict[str, Any]] = []
        for idx, raw_box in enumerate(boxes_or_x1):
            if not isinstance(raw_box, Mapping):
                continue
            x1 = int(raw_box.get("x1", raw_box.get("xStart", 0)))
            y1 = int(raw_box.get("y1", raw_box.get("yStart", 0)))
            x2 = int(raw_box.get("x2", raw_box.get("xEnd", 0)))
            y2 = int(raw_box.get("y2", raw_box.get("yEnd", 0)))
            if x2 <= x1 or y2 <= y1:
                raise ValueError(
                    f"Tọa độ ROI không hợp lệ tại khung #{idx + 1}: x1={x1}, y1={y1}, x2={x2}, y2={y2}"
                )
            roi_id = raw_box.get("id", raw_box.get("key", idx))
            box_name = str(raw_box.get("name") or f"Điểm bất thường {idx + 1}").strip()
            if not box_name:
                box_name = f"Điểm bất thường {idx + 1}"
            threshold = float(raw_box.get("threshold", kwargs.get("threshold", 0.2)))
            if not np.isfinite(threshold) or not 0 <= threshold <= 1:
                raise ValueError(
                    f"Ngưỡng bất thường của vùng {box_name} phải nằm trong khoảng 0 đến 1"
                )
            save_runtime = str(
                raw_box.get("saveRuntimeImages", kwargs.get("saveRuntimeImages", False))
            ).lower() == "true"
            normalized.append(
                {
                    "id": roi_id,
                    "key": str(raw_box.get("key", roi_id)),
                    "name": box_name,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "threshold": threshold,
                    "saveRuntimeImages": save_runtime,
                }
            )
        if not normalized:
            raise ValueError("Danh sách khung kiểm tra điểm bất thường không được rỗng")
        return normalized

    def define(
        self,
        img: np.ndarray,
        boxes: Sequence[Mapping[str, Any]] | int,
        *legacy_coords: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Chạy PatchCore cho toàn bộ các khung bất thường được cấu hình trên item."""
        if not isinstance(img, np.ndarray) or img.size == 0:
            raise ValueError("img đầu vào không được rỗng")

        normalized_boxes = self._normalize_boxes_input(boxes, legacy_coords, kwargs)
        product_id = kwargs.get("product_id")
        frame_id = kwargs.get("frame_id")
        item_id = kwargs.get("item_id")

        annotated_image = img.copy()
        evaluated_boxes: List[Dict[str, Any]] = []
        all_anomaly_boxes: List[Tuple[int, int, int, int]] = []
        max_score = 0.0
        defect_counter = 0

        for box in normalized_boxes:
            roi_id = box["id"]
            x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
            threshold = float(box["threshold"])
            box_name = box["name"]

            model = self.anomaly_point_model
            missing_model = False
            if model is None and self.anomaly_point_service is not None:
                if product_id is None or frame_id is None or item_id is None:
                    raise ValueError(
                        f"Thiếu thông tin product_id, frame_id, item_id để nạp mô hình PatchCore: {kwargs}"
                    )
                try:
                    model = self.anomaly_point_service.get_patchcore_frame(
                        product_id, frame_id, item_id, roi_id=roi_id
                    )
                except FileNotFoundError:
                    missing_model = True

            if missing_model or model is None:
                evaluated_boxes.append(
                    {
                        "id": roi_id,
                        "key": box["key"],
                        "name": box_name,
                        "bbox_roi": [x1, y1, x2, y2],
                        "threshold": threshold,
                        "score": None,
                        "anomaly_boxes": [],
                        "missing_model": True,
                    }
                )
                continue

            score, _heatmap, anomaly_boxes = model.predict_with_anomaly_boxes(
                img, x1, y1, x2, y2, threshold=threshold
            )
            score_val = float(score)
            if score_val > max_score:
                max_score = score_val

            if box["saveRuntimeImages"] and self.anomaly_point_service is not None:
                if product_id is not None and frame_id is not None and item_id is not None:
                    roi_img = img[y1:y2, x1:x2].copy()
                    threading.Thread(
                        target=self.anomaly_point_service.save_runtime_image_for_training,
                        args=(product_id, frame_id, item_id, roi_img, roi_id),
                        daemon=True,
                    ).start()

            for abox in anomaly_boxes:
                defect_counter += 1
                px, py, pw, ph = (int(v) for v in abox)
                all_anomaly_boxes.append((px, py, pw, ph))
                Tool_OpenCv2.draw_labeled_roi(
                    annotated_image,
                    (px, py, px + pw, py + ph),
                    f"Vùng lỗi {defect_counter}",
                    (0, 215, 255),
                    thickness=2,
                )

            evaluated_boxes.append(
                {
                    "id": roi_id,
                    "key": box["key"],
                    "name": box_name,
                    "bbox_roi": [x1, y1, x2, y2],
                    "threshold": threshold,
                    "score": score_val,
                    "anomaly_boxes": list(anomaly_boxes),
                    "missing_model": False,
                }
            )

        return {
            "boxes": evaluated_boxes,
            "score": max_score,
            "max_score": max_score,
            "anomaly_boxes": all_anomaly_boxes,
            "image": annotated_image,
        }

    def compare(
        self,
        standard_data: Any,
        runtime_data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """So sánh điểm bất thường thực tế của từng khung với ngưỡng riêng của khung đó."""
        if not isinstance(runtime_data, dict) or "boxes" not in runtime_data:
            raise ValueError("runtime_data phải là dict chứa trường 'boxes'")

        std_config = {}
        if isinstance(standard_data, Mapping):
            raw_std = standard_data.get(self.INSPECTOR_NAME, standard_data)
            if isinstance(raw_std, Mapping):
                std_config = dict(raw_std)

        box_comparisons: List[Dict[str, Any]] = []
        failed_boxes: List[Dict[str, Any]] = []
        ok_count = 0

        for item in runtime_data.get("boxes", []):
            if not isinstance(item, Mapping):
                continue
            key = str(item.get("key", item.get("id", "")))
            std_box = std_config.get(key) if isinstance(std_config.get(key), Mapping) else {}
            threshold = float(std_box.get("threshold", item.get("threshold", 0.2)))
            name = str(std_box.get("name") or item.get("name") or f"Điểm bất thường {key}")
            missing_model = bool(item.get("missing_model", False))
            score = item.get("score")
            score_val = float(score) if score is not None else None

            if missing_model or score_val is None:
                box_ok = False
                box_msg = f'Chưa tạo model PatchCore cho vùng "{name}"'
            elif score_val <= threshold:
                box_ok = True
                box_msg = "Không phát hiện sự bất thường"
                ok_count += 1
            else:
                box_ok = False
                box_msg = "Phát hiện sự bất thường"

            comp_entry = {
                "id": item.get("id"),
                "key": key,
                "name": name,
                "bbox_roi": item.get("bbox_roi"),
                "threshold": threshold,
                "score": score_val,
                "anomaly_boxes": item.get("anomaly_boxes", []),
                "missing_model": missing_model,
                "ok": box_ok,
                "message": box_msg,
            }
            box_comparisons.append(comp_entry)
            if not box_ok:
                failed_boxes.append(comp_entry)

        total_boxes = len(box_comparisons)
        overall_ok = total_boxes > 0 and len(failed_boxes) == 0
        if overall_ok:
            message = f"Không phát hiện sự bất thường trên tất cả {ok_count}/{total_boxes} vùng"
        else:
            failed_names = ", ".join(f'"{b["name"]}"' for b in failed_boxes)
            message = f"Phát hiện bất thường tại {len(failed_boxes)}/{total_boxes} vùng ({failed_names})"

        return {
            "ok": overall_ok,
            "total_boxes": total_boxes,
            "ok_count": ok_count,
            "max_score": float(runtime_data.get("max_score", 0.0)),
            "box_comparisons": box_comparisons,
            "failed_boxes": failed_boxes,
            "anomaly_boxes": runtime_data.get("anomaly_boxes", []),
            "message": message,
            "image": runtime_data.get("image"),
        }

    def judge(self, comparison_data: Dict[str, Any]) -> JudgmentResult:
        """Kết luận phán định cuối cùng trả về JudgmentResult cho toàn bộ item."""
        required_keys = {"ok", "total_boxes", "ok_count", "box_comparisons", "message"}
        if not required_keys.issubset(comparison_data):
            raise ValueError("comparison_data thiếu các trường bắt buộc")

        ok = bool(comparison_data["ok"])
        total_boxes = int(comparison_data["total_boxes"])
        ok_count = int(comparison_data["ok_count"])
        max_score = float(comparison_data.get("max_score", 0.0))
        message = str(comparison_data["message"])
        errors: List[str] = []

        for failed in comparison_data.get("failed_boxes", []):
            b_name = failed.get("name", "Điểm bất thường")
            b_thresh = float(failed.get("threshold", 0.2))
            if failed.get("missing_model"):
                errors.append(
                    f'[Điểm bất thường] NG - "{b_name}" - Quy định:"<= {b_thresh:.3f}" - Thực tế :"Chưa tạo model PatchCore"'
                )
            else:
                b_score = float(failed.get("score") or 0.0)
                errors.append(
                    f'[Điểm bất thường] NG - "{b_name}" - Quy định:"<= {b_thresh:.3f}" - Thực tế :"{b_score:.3f} (Phát hiện sự bất thường)"'
                )

        return JudgmentResult(
            ok=ok,
            status="OK" if ok else "NG",
            standard_data={
                "total_boxes": total_boxes,
                "boxes": [
                    {
                        "id": b.get("id"),
                        "name": b.get("name"),
                        "threshold": b.get("threshold"),
                        "bbox_roi": b.get("bbox_roi"),
                    }
                    for b in comparison_data["box_comparisons"]
                ],
            },
            runtime_data={
                "ok_count": ok_count,
                "score": max_score,
                "max_score": max_score,
                "boxes": comparison_data["box_comparisons"],
                "anomaly_boxes": comparison_data.get("anomaly_boxes", []),
                "image": comparison_data.get("image"),
            },
            message=message,
            errors=errors,
        )
