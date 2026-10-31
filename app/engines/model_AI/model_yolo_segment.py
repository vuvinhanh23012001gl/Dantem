import threading
from pathlib import Path
from typing import Any
from ultralytics import YOLO
from ultralytics.engine.results import Results
from app.config import YoloSegmentConfig
from app.model import BaseAI
import numpy as np
import gc
# pyrefly: ignore [missing-import]
import torch
from typing import Any
import cv2

class ModelYoloSegment(BaseAI):
    """YOLO Segment sử dụng Ultralytics."""
    def __init__(self, config: YoloSegmentConfig):
        """Khởi tạo mô hình.
        Args:
            config: Cấu hình mô hình.
        Returns:
            None
        """
        self.config = config
        self.model: YOLO | None = None
        self._predict_lock = threading.Lock()
        self.load_model()
        

    def load_model(self) -> None: 
        """Tải mô hình.
        Args:
            None
        Returns:
            None
        """
        self.model = YOLO(str(Path(self.config.path_model)))
        self.model.to(self.config.device)
        self.warmup()
        # Hàm này chạy đầu tiên khi tạo model


    def preprocess(self, image: Any) -> Any:
        """Tiền xử lý ảnh.
        Args:
            image: Ảnh đầu vào.
        Returns:
            Any: Ảnh sau tiền xử lý.
        """
        return image


    def predict(self, image: Any) -> Results:
        """Thực hiện suy luận.
        Args:
            image: Ảnh đầu vào.
        Returns:
            Results: Kết quả suy luận.
        """
        if self.model is None:
            raise RuntimeError("Model chưa được load.")
        image = self.preprocess(image)
        with self._predict_lock:
            return self.model.predict(
                source=image,
                imgsz=self.config.image_size,
                conf=self.config.confidence,
                iou=self.config.iou,
                device=self.config.device,
                verbose=False,
            )[0]
    
    def get_result(self, image: Any) -> list[dict]:
        """Lấy danh sách kết quả segment.
        Args:
            image: Ảnh đầu vào.
        Returns:
            list[dict]: Danh sách kết quả segment.
        """
        result = self.predict(image)
        outputs: list[dict] = []
        if result.masks is None:
            return outputs
        image_height, image_width = result.orig_shape
        polygons = result.masks.xy
        masks = result.masks.data.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)
        scores = result.boxes.conf.cpu().numpy()
        for polygon, mask, cls, score in zip(
            polygons,
            masks,
            classes,
            scores,
        ):
            outputs.append(
                {
                    "class_id": int(cls),
                    "class_name": result.names[int(cls)],
                    "confidence": float(score),
                    "image_width": image_width,
                    "image_height": image_height,
                    "polygon": polygon.tolist(),
                    "mask": mask,
                }
            )
        return outputs
    def warmup(self) -> None:
        """Warmup mô hình.
        Args:
            None
        Returns:
            None
        """
        if self.model is None:
            raise RuntimeError("Model chưa được load.")

        warmup_image = np.zeros(
            (self.config.image_size, self.config.image_size, 3),
            dtype=np.uint8,
        )

        self.model.predict(
            source=warmup_image,
            imgsz=self.config.image_size,
            conf=self.config.confidence,
            iou=self.config.iou,
            device=self.config.device,
            verbose=False,
        )


    def unload(self) -> None:
        """Giải phóng mô hình.
        Args:
            None
        Returns:
            None
        """
        self.model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def draw_segments(self, image: np.ndarray, segments: list[dict], color: tuple[int, int, int] = (0, 255, 0), thickness: int = 2, show_label: bool = True) -> np.ndarray:
        """Vẽ polygon của các segment lên ảnh.
        Args:
            image: Ảnh đầu vào.
            segments: Danh sách segment.
            color: Màu đường viền (BGR).
            thickness: Độ dày đường vẽ.
            show_label: Hiển thị tên class và confidence.
        Returns:
            np.ndarray: Ảnh sau khi vẽ.
        """
        image = image.copy()

        for segment in segments:
            polygon = np.asarray(segment["polygon"], dtype=np.int32)
            cv2.polylines(image, [polygon], True, color, thickness)

            if show_label:
                x, y = polygon[0]
                label = f'{segment["class_name"]} {segment["confidence"]:.2f}'
                cv2.putText(image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return image
    
    def predict_draw(self, image: np.ndarray, show_label: bool = True, color: tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """Thực hiện suy luận và vẽ kết quả lên ảnh.
        Args:
            image: Ảnh đầu vào.
            show_label: Hiển thị tên class và confidence.
            color: Màu đường viền (BGR).
            thickness: Độ dày đường vẽ.
        Returns:
            np.ndarray: Ảnh sau khi vẽ.
        """
        segments = self.get_result(image)
        return self.draw_segments(image, segments, color, thickness, show_label)
    
    def show(self, image: np.ndarray, window_name: str = "Result") -> None:
        """Hiển thị ảnh.
        Args:
            image: Ảnh cần hiển thị.
            window_name: Tên cửa sổ.
        Returns:
            None
        """
        cv2.imshow(window_name, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()