import cv2
import numpy as np
from typing import Any
from app.core import Result, ErrorCode
from app.engines.model_AI.model_yolo_obb import ModelYoloOBB


class StampAlignmentService:
    """Dịch vụ thực thi kiểm tra độ lệch tem bằng mô hình YOLO OBB."""

    def __init__(self, model_obb: ModelYoloOBB):
        self.model_obb = model_obb

    def _clip_roi(
        self, w_img: int, h_img: int, x1: float, y1: float, x2: float, y2: float
    ) -> tuple[int, int, int, int]:
        left = max(0, min(int(round(min(x1, x2))), w_img))
        top = max(0, min(int(round(min(y1, y2))), h_img))
        right = max(0, min(int(round(max(x1, x2))), w_img))
        bottom = max(0, min(int(round(max(y1, y2))), h_img))
        return left, top, right, bottom

    def inspect_alignment_boxes(
        self,
        image: np.ndarray,
        boxes: list[dict[str, Any]],
        width_canvas: int | None = None,
    ) -> Result:
        """Kiểm tra độ lệch tem trên danh sách các khung ROI.

        Args:
            image: Ảnh gốc đầu vào (NumPy BGR).
            boxes: Danh sách khung ROI kèm cấu hình dung sai.
            width_canvas: Chiều rộng canvas hiển thị để quy đổi tỷ lệ.

        Returns:
            Result.Ok với data chứa:
                - boxes: Danh sách kết quả chi tiết từng khung (4 tiêu chí, OK/NG)
                - objects: Danh sách các đối tượng OBB (Frame, Stamp, vector lệch)
                - image_width: Chiều rộng ảnh gốc
                - image_height: Chiều cao ảnh gốc
        """
        if not isinstance(image, np.ndarray) or image.size == 0:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND)
        if not isinstance(boxes, list) or not boxes:
            return Result.Fail(ErrorCode.INVALID_INPUT)

        h_img, w_img = image.shape[:2]
        if width_canvas is not None:
            if width_canvas <= 0:
                return Result.Fail(ErrorCode.INVALID_INPUT)
            scale = w_img / float(width_canvas)
        else:
            scale = 1.0

        box_results: list[dict[str, Any]] = []
        all_objects: list[dict[str, Any]] = []

        for idx, raw_box in enumerate(boxes):
            if not isinstance(raw_box, dict):
                continue

            raw_x1 = raw_box.get("x1", raw_box.get("xStart", 0))
            raw_y1 = raw_box.get("y1", raw_box.get("yStart", 0))
            raw_x2 = raw_box.get("x2", raw_box.get("xEnd", 0))
            raw_y2 = raw_box.get("y2", raw_box.get("yEnd", 0))

            rx1, ry1, rx2, ry2 = self._clip_roi(
                w_img,
                h_img,
                float(raw_x1) * scale,
                float(raw_y1) * scale,
                float(raw_x2) * scale,
                float(raw_y2) * scale,
            )

            box_id = raw_box.get("id", idx)
            box_key = str(raw_box.get("key", box_id))
            box_name = str(
                raw_box.get("name") or f"Tem {idx + 1}"
            ).strip() or f"Tem {idx + 1}"

            # Ngưỡng dung sai (nhập theo đơn vị pixel của Canvas)
            user_max_du = float(raw_box.get("max_du", 15.0))
            user_max_dv = float(raw_box.get("max_dv", 15.0))
            user_max_deg = float(raw_box.get("max_deg", 3.0))
            user_margin = float(raw_box.get("margin", 5.0))

            if rx2 <= rx1 or ry2 <= ry1:
                box_results.append(
                    {
                        "id": box_id,
                        "key": box_key,
                        "name": box_name,
                        "status": "NG",
                        "error": "Khung ROI không hợp lệ",
                        "metrics": {
                            "du": 0.0,
                            "dv": 0.0,
                            "magnitude": 0.0,
                            "direction_deg": 0.0,
                            "delta_angle_deg": 0.0,
                            "is_contained": False,
                            "unit": "pixel",
                        },
                        "details": {
                            "pass_position_u": False,
                            "pass_position_v": False,
                            "pass_rotation": False,
                            "pass_containment": False,
                        },
                        "tolerances": {
                            "max_du": user_max_du,
                            "max_dv": user_max_dv,
                            "max_deg": user_max_deg,
                            "margin": user_margin,
                        },
                    }
                )
                continue

            roi_img = image[ry1:ry2, rx1:rx2]

            # Quy đổi dung sai sang không gian pixel của ảnh gốc để đánh giá
            tolerances_img_space = {
                "max_du": user_max_du * scale,
                "max_dv": user_max_dv * scale,
                "max_deg": user_max_deg,
                "margin": user_margin * scale,
            }

            eval_res = self.model_obb.inspect_alignment(
                roi_img, tolerances_img_space
            )

            # Quy đổi kết quả đo trở lại thang đo của Canvas (để người dùng thấy đúng số đo họ cấu hình)
            metrics = eval_res.get("metrics", {})
            du_canvas = round(float(metrics.get("du", 0.0)) / scale, 2)
            dv_canvas = round(float(metrics.get("dv", 0.0)) / scale, 2)
            mag_canvas = round(float(metrics.get("magnitude", 0.0)) / scale, 2)

            metrics_canvas = {
                "du": du_canvas,
                "dv": dv_canvas,
                "magnitude": mag_canvas,
                "direction_deg": metrics.get("direction_deg", 0.0),
                "delta_angle_deg": metrics.get("delta_angle_deg", 0.0),
                "is_contained": metrics.get("is_contained", False),
                "unit": "pixel",
            }

            # Chuyển đổi tọa độ các đỉnh OBB từ ROI sang tọa độ ảnh gốc
            frame_corners_global = []
            if "frame_corners" in eval_res:
                frame_corners_global = [
                    [float(pt[0] + rx1), float(pt[1] + ry1)]
                    for pt in eval_res["frame_corners"]
                ]

            stamp_corners_global = []
            if "stamp_corners" in eval_res:
                stamp_corners_global = [
                    [float(pt[0] + rx1), float(pt[1] + ry1)]
                    for pt in eval_res["stamp_corners"]
                ]

            box_eval = {
                "id": box_id,
                "key": box_key,
                "name": box_name,
                "bbox_roi": [rx1, ry1, rx2, ry2],
                "status": eval_res.get("status", "NG"),
                "error": eval_res.get("error"),
                "metrics": metrics_canvas,
                "details": eval_res.get("details", {}),
                "counts": eval_res.get("counts", {}),
                "tolerances": {
                    "max_du": user_max_du,
                    "max_dv": user_max_dv,
                    "max_deg": user_max_deg,
                    "margin": user_margin,
                },
                "frame_corners": frame_corners_global,
                "stamp_corners": stamp_corners_global,
            }
            box_results.append(box_eval)

            # Đối tượng vẽ OBB cho canvas
            if frame_corners_global:
                all_objects.append(
                    {
                        "roi_id": box_id,
                        "roi_name": box_name,
                        "type": "obb_frame",
                        "corners": frame_corners_global,
                        "color": "#00E676",  # Xanh lá sáng
                    }
                )
            if stamp_corners_global:
                is_ok = box_eval["status"] == "OK"
                all_objects.append(
                    {
                        "roi_id": box_id,
                        "roi_name": box_name,
                        "type": "obb_stamp",
                        "corners": stamp_corners_global,
                        "color": "#2979FF" if is_ok else "#FF1744",  # Xanh dương nếu OK, Đỏ nếu NG
                        "is_ok": is_ok,
                        "center_vector": {
                            "start": [
                                float(np.mean([pt[0] for pt in frame_corners_global])),
                                float(np.mean([pt[1] for pt in frame_corners_global])),
                            ] if frame_corners_global else [0, 0],
                            "end": [
                                float(np.mean([pt[0] for pt in stamp_corners_global])),
                                float(np.mean([pt[1] for pt in stamp_corners_global])),
                            ],
                        },
                    }
                )

        return Result.Ok(
            {
                "boxes": box_results,
                "objects": all_objects,
                "image_width": w_img,
                "image_height": h_img,
            }
        )
