
import cv2
import numpy as np
from app.engines.model_AI import ModelPatchCore
from app.utils import Tool_OpenCv2

class FaceModelPatchCore:
    """Chạy PatchCore trên một ROI và quy đổi kết quả về ảnh gốc.
    ``ModelPatchCore`` xử lý một ảnh độc lập, còn lớp này đảm nhiệm việc crop
    vùng kiểm tra giống các frame processor của YOLO và dịch bounding box từ
    hệ tọa độ ROI về hệ tọa độ ảnh đầu vào.
    """
    def __init__(self, model: ModelPatchCore) -> None:
        """Khởi tạo frame processor.

        Input: ``model`` là instance ``ModelPatchCore`` đã load model.
        Output: Không trả về dữ liệu.
        Errors: ``TypeError`` nếu model không phải ``ModelPatchCore``.
        """
        if not isinstance(model, ModelPatchCore):
            raise TypeError("model phải là instance của ModelPatchCore")
        self.model = model

    def get_bounding_boxes(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> list[tuple[int, int, int, int]]:
        """Phát hiện vùng bất thường trong ROI và trả box theo ảnh gốc.

        Input:
            image: Ảnh đầu vào dạng NumPy.
            x1, y1, x2, y2: Tọa độ ROI trong ảnh gốc.
        Output:
            Danh sách box dạng ``(x, y, width, height)`` theo ảnh gốc.
        Errors:
            ``ValueError`` nếu ảnh rỗng hoặc ROI không hợp lệ; lỗi suy luận
            từ ``ModelPatchCore`` được truyền ra ngoài.
        """
        self._validate_roi(image, x1, y1, x2, y2)
        image_crop, left, top = Tool_OpenCv2.crop_image(image, x1, y1, x2, y2)
        image_crop_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
        boxes = self.model.get_bounding_boxes(image_crop_rgb)
        return self.convert_boxes_to_original_image(boxes, left, top)

    def predict(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> tuple[float, np.ndarray]:
        """Tính anomaly score và heatmap overlay trong một ROI.

        Input: Ảnh NumPy và tọa độ ROI theo ảnh gốc.
        Output: Tuple ``(score, overlay)``; overlay có kích thước ROI.
        Errors: ``ValueError`` nếu ảnh/ROI không hợp lệ; lỗi model được truyền
            ra ngoài.
        """
        self._validate_roi(image, x1, y1, x2, y2)
        image_crop, _, _ = Tool_OpenCv2.crop_image(image, x1, y1, x2, y2)
        image_crop_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
        return self.model.predict(image_crop_rgb)

    def predict_with_anomaly_boxes(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        threshold: float,
        min_area: int = 50,
    ) -> tuple[float, np.ndarray, list[tuple[int, int, int, int]]]:
        """Tính anomaly score, heatmap overlay và các bounding box của vùng bất thường theo ảnh gốc.

        Chỉ trích xuất bounding box cho các vùng trên anomaly map có giá trị vượt qua threshold cấu hình.
        Tọa độ bounding box trả về được quy đổi về hệ tọa độ ảnh gốc.

        Input:
            image: Ảnh đầu vào dạng NumPy (BGR).
            x1, y1, x2, y2: Tọa độ ROI trong ảnh gốc.
            threshold: Ngưỡng điểm bất thường thực tế.
            min_area: Diện tích tối thiểu (pixel) để coi là một vùng bất thường.

        Output:
            Tuple (score, overlay, anomaly_boxes_in_original_image).
        """
        self._validate_roi(image, x1, y1, x2, y2)
        image_crop, left, top = Tool_OpenCv2.crop_image(image, x1, y1, x2, y2)
        image_crop_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
        score, overlay, raw_boxes = self.model.predict_with_anomaly_boxes(
            image_crop_rgb, threshold=threshold, min_area=min_area
        )
        converted_boxes = self.convert_boxes_to_original_image(raw_boxes, left, top)
        return score, overlay, converted_boxes

    @staticmethod
    def convert_boxes_to_original_image(
        boxes: list[tuple[int, int, int, int]] | np.ndarray,
        left: int,
        top: int,
    ) -> list[tuple[int, int, int, int]]:
        """Dịch box từ hệ tọa độ ROI về hệ tọa độ ảnh gốc.

        Input: ``boxes`` dạng ``(x, y, width, height)`` và offset ROI.
        Output: Danh sách box nguyên tọa độ ảnh gốc.
        Errors: ``ValueError`` nếu box không có đúng bốn phần tử.
        """
        original_boxes = []
        for box in boxes:
            if len(box) != 4:
                raise ValueError("bounding box phải có dạng (x, y, width, height)")
            x, y, width, height = (int(value) for value in box)
            original_boxes.append((x + int(left), y + int(top), width, height))
        return original_boxes

    @staticmethod
    def _validate_roi(
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> None:
        """Kiểm tra ảnh và ROI trước khi crop.

        Input: Ảnh NumPy và bốn tọa độ ROI.
        Output: Không trả về dữ liệu.
        Errors: ``ValueError`` nếu dữ liệu rỗng hoặc ROI không hợp lệ.
        """
        if not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("image đầu vào không được rỗng")
        if not all(isinstance(value, (int, np.integer)) for value in (x1, y1, x2, y2)):
            raise ValueError("tọa độ ROI phải là số nguyên")
        if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
            raise ValueError("ROI phải có x2 > x1 và y2 > y1")
        height, width = image.shape[:2]
        if x2 > width or y2 > height:
            raise ValueError("ROI vượt quá kích thước ảnh")

FrameModelPatchCore = FaceModelPatchCore