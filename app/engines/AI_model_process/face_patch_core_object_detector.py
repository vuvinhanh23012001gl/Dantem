import numpy as np

from app.engines.AI_model_process.face_patch_core_process import FaceModelPatchCore, FrameModelPatchCore
from app.engines.model_AI import ModelYoloObject
from app.utils import Tool_OpenCv2


class FacePatchCoreObjectDetector:
    """Chạy PatchCore để tìm vùng bất thường, rồi infer bằng YOLO Object trên từng vùng đó.

    Lớp này chỉ thực hiện inference và trả về thông tin vùng bất thường cùng kết quả
    nhận diện đối tượng. Không tham gia phán định OK/NG.
    """

    def __init__(
        self,
        patch_core_frame: FrameModelPatchCore,
        yolo_object_model: ModelYoloObject,
    ) -> None:
        """Khởi tạo detector.

        Input:
            patch_core_frame: instance ``FrameModelPatchCore`` đã được khởi tạo.
            yolo_object_model: instance ``ModelYoloObject`` đã load model.
        Output:
            Không trả về dữ liệu.
        Errors:
            ``TypeError`` nếu tham số đầu vào không đúng kiểu.
        """
        if not isinstance(patch_core_frame, FrameModelPatchCore):
            raise TypeError("patch_core_frame phải là instance của FrameModelPatchCore")
        if not hasattr(yolo_object_model, "get_result"):
            raise TypeError("yolo_object_model phải có phương thức get_result()")

        self.patch_core_frame = patch_core_frame
        self.yolo_object_model = yolo_object_model

    def detect_anomaly_objects(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        anomaly_boxes: list[tuple[int, int, int, int]] | None = None,
    ) -> list[dict]:
        """Tìm vùng bất thường bằng PatchCore và infer YOLO trên từng vùng đó.

        Input:
            image: Ảnh đầu vào dạng NumPy.
            x1, y1, x2, y2: Vùng ROI làm đầu vào cho PatchCore.
            anomaly_boxes: Box PatchCore đã tính theo ảnh đầu vào. Nếu không
                truyền, detector sẽ tự tính box bằng PatchCore.
        Output:
            Danh sách dict, mỗi dict chứa thông tin về box bất thường PatchCore và
            các đối tượng YOLO nhận diện trong box đó.
        Errors:
            ``ValueError`` nếu ROI không hợp lệ hoặc ảnh rỗng; lỗi model được truyền ra ngoài.
        """
        if anomaly_boxes is None:
            anomaly_boxes = self.patch_core_frame.get_bounding_boxes(image, x1, y1, x2, y2)
        results: list[dict] = []

        for box in anomaly_boxes:
            patch_x, patch_y, patch_w, patch_h = (int(value) for value in box)
            padding = 15
            roi_x1 = max(0, patch_x - padding)
            roi_y1 = max(0, patch_y - padding)
            roi_x2 = min(image.shape[1], patch_x + patch_w + padding)
            roi_y2 = min(image.shape[0], patch_y + patch_h + padding)

            if roi_x2 <= roi_x1 or roi_y2 <= roi_y1:
                continue

            image_crop, left, top = Tool_OpenCv2.crop_image(
                image,
                roi_x1,
                roi_y1,
                roi_x2,
                roi_y2,
            )
            yolo_results = self.yolo_object_model.get_result(image_crop)

            for result in yolo_results:
                bbox = result.get("bbox", {})
                if not bbox:
                    continue

                shifted_bbox = {
                    "x1": float(bbox.get("x1", 0.0)) + float(left),
                    "y1": float(bbox.get("y1", 0.0)) + float(top),
                    "x2": float(bbox.get("x2", 0.0)) + float(left),
                    "y2": float(bbox.get("y2", 0.0)) + float(top),
                }

                results.append(
                    {
                        "patchcore_box": (patch_x, patch_y, patch_w, patch_h),
                        "patchcore_roi": {
                            "x1": roi_x1,
                            "y1": roi_y1,
                            "x2": roi_x2,
                            "y2": roi_y2,
                        },
                        "class_id": result.get("class_id"),
                        "class_name": result.get("class_name"),
                        "confidence": float(result.get("confidence", 0.0)),
                        "bbox": shifted_bbox,
                        "image_width": image.shape[1],
                        "image_height": image.shape[0],
                    }
                )

        return results

    def detect_anomaly_objects_with_heatmap(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        threshold: float | None = None,
    ) -> dict:
        """Trả về score PatchCore, heatmap và danh sách đối tượng YOLO chỉ trên các vùng bất thường.

        Vùng đưa vào YOLO nhận diện đối tượng là những vùng bất thường do PatchCore khoanh,
        chứ không phải toàn bộ vùng ảnh kiểm tra ROI ban đầu.

        Input:
            image: Ảnh gốc dạng NumPy.
            x1, y1, x2, y2: Vùng ROI cần kiểm tra sự bất thường.
            threshold: Tham số cũ được giữ để tương thích, không dùng để chặn YOLO.
        Output:
            dict chứa ``score``, ``heatmap``, ``detections``, ``anomaly_boxes``.
        Errors:
            ``ValueError`` nếu ROI không hợp lệ; lỗi model được truyền ra ngoài.
        """
        score, heatmap = self.patch_core_frame.predict(image, x1, y1, x2, y2)
        anomaly_boxes = self.patch_core_frame.get_bounding_boxes(image, x1, y1, x2, y2)

        score_float = float(score)

        if not anomaly_boxes:
            detections = []
        else:
            detections = self.detect_anomaly_objects(
                image, x1, y1, x2, y2, anomaly_boxes=anomaly_boxes
            )

        return {
            "score": score_float,
            "heatmap": heatmap,
            "detections": detections,
            "anomaly_boxes": anomaly_boxes,
        }

 
FramePatchCoreObjectDetector = FacePatchCoreObjectDetector
