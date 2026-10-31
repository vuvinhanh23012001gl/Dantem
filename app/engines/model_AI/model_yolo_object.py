import threading
from app.model import BaseAI
from app.config import YoloDetectObjectConfig
from ultralytics import YOLO
import numpy as np
import gc
# pyrefly: ignore [missing-import]
import torch


class ModelYoloObject(BaseAI):
    def __init__(self, config: YoloDetectObjectConfig):
        self.config = config
        self.model: YOLO | None = None
        self._predict_lock = threading.Lock()
        self.load_model()
        self.warmup()

    def load_model(self) -> None:
        """Load YOLO model."""
        if self.model is None:
            self.model = YOLO(self.config.path_model)

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess input image.
        Args:
            image: Input image.
        Returns:
            Preprocessed image.
        """
        return image

    def predict(self, image: np.ndarray):
        """Run object detection.
        Args:
            image: Input image.

        Returns:
            YOLO prediction result.
        """
        if self.model is None:
            raise RuntimeError("Model has not been loaded.")
        image = self.preprocess(image)
        with self._predict_lock:
            return self.model.predict(
                source=image,
                imgsz=self.config.image_size,
                conf=self.config.confidence,
                iou=self.config.iou,
                device=self.config.device,
                verbose=False,
            )

    def unload(self) -> None:
        """Release model from memory."""
        self.model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def warmup(self) -> None:
        """Warm up model."""
        if self.model is None:
            raise RuntimeError("Model has not been loaded.")
        dummy = np.zeros(
            (self.config.image_size, self.config.image_size, 3),
            dtype=np.uint8,
        )
        self.predict(dummy)

    def get_result(self, image: np.ndarray, kx: int = 0, ky: int = 0) -> list[dict]:
        """Lấy danh sách kết quả detect và kiểm tra chạm biên trục X, Y.
        Args:
            image: Ảnh đầu vào.
            kx: Khoảng cách an toàn tính từ biên trái/phải (mặc định 0).
            ky: Khoảng cách an toàn tính từ biên trên/dưới (mặc định 0).

        Returns:
            list[dict]: Danh sách kết quả kèm trạng thái chạm biên touch_x, touch_y.
        """
        result = self.predict(image)[0]
        outputs: list[dict] = []
        # Kiểm tra an toàn xem có boxes nào không
        if result.boxes is None or len(result.boxes) == 0:
            return outputs
        image_height, image_width = result.orig_shape
        # Trích xuất dữ liệu tensor một lần để tối ưu hiệu năng chuyển đổi CPU
        boxes = result.boxes.xyxy.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)
        scores = result.boxes.conf.cpu().numpy()
        for box, cls, score in zip(boxes, classes, scores):
            x1, y1, x2, y2 = box.tolist()
            # --- LOGIC KIỂM TRA CHẠM BIÊN TRỤC X & TRỤC Y ---
            # Chạm trục X khi sát biên trái (<= kx) HOẶC sát biên phải (>= width - kx)
            touch_x = (x1 <= kx) or (x2 >= (image_width - kx))
            # Chạm trục Y khi sát biên trên (<= ky) HOẶC sát biên dưới (>= height - ky)
            touch_y = (y1 <= ky) or (y2 >= (image_height - ky))
            # ------------------------------------------------
            outputs.append(
                {
                    "class_id": int(cls),
                    "class_name": result.names[int(cls)],
                    "confidence": float(score),
                    "image_width": image_width,
                    "image_height": image_height,
                    "touch_x": touch_x,  # True nếu chạm trục X
                    "touch_y": touch_y,  # True nếu chạm trục Y
                    "bbox": {
                        "x1": float(x1),
                        "y1": float(y1),
                        "x2": float(x2),
                        "y2": float(y2),
                    },
                }
            )
        return outputs
