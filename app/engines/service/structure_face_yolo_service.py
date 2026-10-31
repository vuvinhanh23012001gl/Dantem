import cv2
import numpy as np
from app.engines.AI_model_process import FaceModelYoloObject, FrameModelYoloObject
from app.core import Result, ErrorCode


class StructureFaceYoloService:
    def __init__(self, frame_model: FrameModelYoloObject):
        """Khởi tạo StructureFaceYoloService.

        Args:
            frame_model (FrameModelYoloObject): Đối tượng thực hiện nhận diện YOLO.
        """
        if frame_model is None:
            raise ValueError("frame_model cho StructureFaceYoloService không được None")
        self.frame_model = frame_model
        self.face_model = frame_model

    @staticmethod
    def _clip_roi(
        w_img: int, h_img: int, x1: float, y1: float, x2: float, y2: float
    ) -> tuple[int, int, int, int]:
        """Chuẩn hóa và kẹp tọa độ ROI vào trong biên ảnh."""
        left = int(round(min(x1, x2)))
        right = int(round(max(x1, x2)))
        top = int(round(min(y1, y2)))
        bottom = int(round(max(y1, y2)))
        left = max(0, min(left, w_img - 1))
        top = max(0, min(top, h_img - 1))
        right = max(0, min(right, w_img))
        bottom = max(0, min(bottom, h_img))
        return left, top, right, bottom

    def search_stamp_in_roi(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        label: str = "stamp",
    ) -> tuple[bool, list[str], list[dict]]:
        """Tìm đối tượng nhãn 'stamp' bằng model YOLO thật trong 1 khung ROI (tọa độ ảnh gốc).

        Returns:
            tuple[bool, list[str], list[dict]]:
                - exists: Có phát hiện ít nhất 1 đối tượng tem trong ROI hay không.
                - messages: Danh sách thông báo chi tiết.
                - objects: Danh sách bounding box đã quy về hệ tọa độ ảnh gốc.
        """
        h_img, w_img = image.shape[:2]
        rx1, ry1, rx2, ry2 = self._clip_roi(w_img, h_img, x1, y1, x2, y2)
        if rx2 <= rx1 or ry2 <= ry1:
            return False, ["Khung ROI có kích thước không hợp lệ."], []

        if hasattr(self.frame_model, "get_objects") and hasattr(
            self.frame_model, "filter_objects_by_class_name"
        ):
            raw_objects, _ = self.frame_model.get_objects(image, rx1, ry1, rx2, ry2)
            objects, exists = self.frame_model.filter_objects_by_class_name(
                raw_objects, label
            )
            if exists:
                messages = [f"OK: Phát hiện {len(objects)} đối tượng '{label}'."]
            else:
                messages = [f"LỖI: Không phát hiện đối tượng '{label}'."]
            return exists, messages, objects

        _, messages, _, objects = self.frame_model.search(
            image, rx1, ry1, rx2, ry2, label
        )
        objects = list(objects) if isinstance(objects, list) else []
        return bool(objects), list(messages or []), objects

    def inspect_stamp_boxes(
        self,
        image: np.ndarray,
        boxes: list[dict],
        label: str = "stamp",
        width_canvas: int | None = None,
    ) -> Result:
        """Kiểm tra sự hiện diện của tem ('stamp') trên danh sách nhiều khung ROI."""
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

        annotated = image.copy()
        box_results: list[dict] = []
        all_objects: list[dict] = []

        for idx, raw_box in enumerate(boxes):
            if not isinstance(raw_box, dict):
                continue
            raw_x1 = raw_box.get("x1", raw_box.get("xStart"))
            raw_y1 = raw_box.get("y1", raw_box.get("yStart"))
            raw_x2 = raw_box.get("x2", raw_box.get("xEnd"))
            raw_y2 = raw_box.get("y2", raw_box.get("yEnd"))
            if None in (raw_x1, raw_y1, raw_x2, raw_y2):
                return Result.Fail(ErrorCode.INVALID_INPUT)

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
            box_name = str(raw_box.get("name") or f"Tem {idx + 1}").strip() or f"Tem {idx + 1}"

            exists, messages, detected_objs = self.search_stamp_in_roi(
                image, rx1, ry1, rx2, ry2, label=label
            )

            tagged_objs = []
            for obj in detected_objs:
                copied = dict(obj)
                copied["roi_id"] = box_id
                copied["roi_name"] = box_name
                tagged_objs.append(copied)

                bbox = copied.get("bbox") or {}
                ox1 = int(round(float(bbox.get("x1", 0))))
                oy1 = int(round(float(bbox.get("y1", 0))))
                ox2 = int(round(float(bbox.get("x2", 0))))
                oy2 = int(round(float(bbox.get("y2", 0))))
                cv2.rectangle(annotated, (ox1, oy1), (ox2, oy2), (255, 200, 0), 2)
                conf_pct = float(copied.get("confidence", 0.0)) * 100.0
                cv2.putText(
                    annotated,
                    f"{copied.get('class_name', label)} {conf_pct:.1f}%",
                    (ox1, max(16, oy1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 200, 0),
                    2,
                    cv2.LINE_AA,
                )

            all_objects.extend(tagged_objs)
            box_results.append(
                {
                    "id": box_id,
                    "key": box_key,
                    "name": box_name,
                    "bbox_roi": [rx1, ry1, rx2, ry2],
                    "exists": exists,
                    "count": len(tagged_objs),
                    "objects": tagged_objs,
                    "messages": messages,
                }
            )

        return Result.Ok(
            {
                "width": w_img,
                "height": h_img,
                "boxes": box_results,
                "objects": all_objects,
                "image": annotated,
            }
        )

    def get_objects_by_label(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        label: str,
        width_canvas: int,
    ) -> Result:
        """Lấy danh sách đối tượng theo label trong 1 vùng kiểm tra (tương thích API đơn khung)."""
        res = self.inspect_stamp_boxes(
            image=image,
            boxes=[{"id": 0, "name": label, "xStart": x1, "yStart": y1, "xEnd": x2, "yEnd": y2}],
            label=label,
            width_canvas=width_canvas,
        )
        if not res.ok:
            return res
        objects = res.data.get("objects", [])
        if not objects:
            return Result.Fail(ErrorCode.LABEL_NOT_FOUND)
        return Result.Ok(objects)


StructureFrameYoloService = StructureFaceYoloService
