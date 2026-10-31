from app.engines.model_AI import ModelYoloSegment
import numpy as np
import cv2
from app.utils import Tool_OpenCv2

class FaceModelYoloSegment:
    def __init__(self, model: ModelYoloSegment):
        self.model = model


    def get_segments(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> list[dict]:
        """Lấy segment trên ảnh gốc.
        Args:
            image: Ảnh đầu vào.
            x1: Góc trái trên X.
            y1: Góc trái trên Y.
            x2: Góc phải dưới X.
            y2: Góc phải dưới Y.
        Returns:
            list[dict]: Danh sách segment.
        """
        image_crop, left, top = Tool_OpenCv2.crop_image(
            image,
            x1,
            y1,
            x2,
            y2
        )
        # self.model.show(image_crop)
        segments = self.model.get_result(
            image_crop
        )
        return self.convert_segments_to_original_image(
            segments,
            left,
            top,
            image.shape[1],
            image.shape[0]
        )




    def convert_segments_to_original_image(
        self,
        segments: list[dict],
        left: int,
        top: int,
        image_width: int,
        image_height: int
    ) -> list[dict]:
        """Chuyển tọa độ segment về ảnh gốc.
        Args:
            segments: Danh sách segment.
            left: Tọa độ trái vùng crop.
            top: Tọa độ trên vùng crop.
            image_width: Chiều rộng ảnh gốc.
            image_height: Chiều cao ảnh gốc.
        Returns:
            list[dict]: Danh sách segment.
        """
        for segment in segments:

            segment["polygon"] = [
                (
                    point[0] + left,
                    point[1] + top
                )
                for point in segment["polygon"]
            ]

            segment["image_width"] = image_width
            segment["image_height"] = image_height

        return segments


    def show(
        self,
        image: np.ndarray,
        segments: list[dict],
        window_name: str = "Result"
    ) -> None:
        """Hiển thị ảnh cùng các segment.
        Args:
            image: Ảnh gốc.
            segments: Danh sách segment.
            window_name: Tên cửa sổ.
        Returns:
            None
        """
        image_draw = image.copy()

        for segment in segments:

            polygon = np.asarray(
                segment["polygon"],
                dtype=np.int32
            )

            if len(polygon) == 0:
                continue

            cv2.polylines(
                image_draw,
                [polygon],
                True,
                (0, 255, 0),
                2
            )
            x, y = polygon[0]
            cv2.putText(
                image_draw,
                f'{segment["class_name"]} {segment["confidence"]:.2f}',
                (x, max(20, y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )
        cv2.imshow(
            window_name,
            image_draw
        )
        cv2.waitKey(0)
        cv2.destroyAllWindows()

FrameModelYoloSegment = FaceModelYoloSegment