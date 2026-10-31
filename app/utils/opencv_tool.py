import cv2
import os
import numpy as np
import base64
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from app.config.path_config import PATH_FOLDER_OUTPUT_RETRAIN
from PIL import Image, ImageDraw, ImageFont

class Tool_OpenCv2:
    RETRAIN_INPUT_ROOT = PATH_FOLDER_OUTPUT_RETRAIN

    @staticmethod
    def save_training_input(
        image: np.ndarray,
        inspector_name: str,
        sample_name: str,
        output_root: Path | None = None,
    ) -> Path:
        """Lưu ảnh thực sự đưa vào model theo folder riêng inspector.

        Input: Ảnh BGR đã crop hoặc full-frame, tên inspector và nhãn mẫu.
        Output: Đường dẫn JPG trong output/retrain/<inspector>/DD_MM_YYYY.
        Errors: ``ValueError`` nếu ảnh rỗng; ``OSError`` nếu không ghi được ảnh.
        """
        if not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Ảnh retrain không được rỗng")

        def safe_component(value: Any) -> str:
            return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._") or "unknown"

        root = output_root or Tool_OpenCv2.RETRAIN_INPUT_ROOT
        now = datetime.now(timezone.utc)
        directory = root / safe_component(inspector_name) / now.strftime("%d_%m_%Y")
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = now.strftime("%H%M%S_%fZ")
        image_path = directory / f"{timestamp}_{safe_component(sample_name)}.jpg"
        if not cv2.imwrite(
            str(image_path),
            image,
            [cv2.IMWRITE_JPEG_QUALITY, 95],
        ):
            raise OSError(f"Không ghi được ảnh retrain: {image_path}")
        return image_path

    @staticmethod
    def draw_labeled_roi(
        image: np.ndarray,
        box: tuple[int, int, int, int],
        label: str,
        color: tuple[int, int, int] = (255, 0, 0),
        thickness: int | None = None,
        draw_border: bool = True,
    ) -> np.ndarray:
        """Vẽ ROI có nhãn Unicode dễ đọc trực tiếp lên ảnh BGR.

        Input: Ảnh BGR, box (x1, y1, x2, y2), nhãn và màu BGR.
            ``draw_border=False`` cho phép chỉ vẽ nhãn mà không vẽ viền ROI.
        Output: Chính ảnh đầu vào sau khi đã vẽ khung và nhãn.
        Errors: ``ValueError`` nếu ảnh không hợp lệ hoặc box không có bốn tọa độ.
        """
        if not isinstance(image, np.ndarray) or image.ndim not in (2, 3):
            raise ValueError("image phải là ndarray ảnh hợp lệ")
        if len(box) != 4:
            raise ValueError("box phải gồm x1, y1, x2, y2")
        x1, y1, x2, y2 = (int(value) for value in box)
        if draw_border:
            line_width = thickness or max(4, min(image.shape[:2]) // 300)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, line_width)
        if image.ndim != 3 or image.shape[2] != 3 or not label.strip():
            return image

        font_size = max(24, round(min(image.shape[:2]) / 45))
        font = None
        for font_path in (
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
        ):
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except OSError:
                continue
        if font is None:
            font = ImageFont.load_default()

        rgb_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(rgb_image)
        text_bounds = draw.textbbox((0, 0), label, font=font)
        text_width = text_bounds[2] - text_bounds[0]
        text_height = text_bounds[3] - text_bounds[1]
        padding = max(6, font_size // 6)
        label_width = min(image.shape[1], text_width + padding * 2)
        label_height = min(image.shape[0], text_height + padding * 2)
        left = min(max(0, x1), image.shape[1] - label_width)
        top = y1 if y1 + label_height <= image.shape[0] else max(0, y1 - label_height)
        draw.rectangle(
            (left, top, left + label_width, top + label_height),
            fill=tuple(reversed(color)),
        )
        draw.text(
            (left + padding - text_bounds[0], top + padding - text_bounds[1]),
            label,
            font=font,
            fill=(255, 255, 255),
        )
        image[:] = cv2.cvtColor(np.asarray(rgb_image), cv2.COLOR_RGB2BGR)
        return image
    
    @staticmethod
    def save_image(image, save_path):
        """
        image: Dữ liệu ảnh (numpy array)
        save_path: Đường dẫn đầy đủ bao gồm tên file (vd: 'data/img/sanpham1.jpg')
        """
        try:
            # Lấy thư mục cha từ đường dẫn để kiểm tra tồn tại
            directory = os.path.dirname(save_path)
            
            # Nếu thư mục chưa tồn tại thì tạo mới
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Đã tạo thư mục: {directory}")

            # Tiến hành lưu ảnh
            # cv2.imwrite trả về True nếu thành công, False nếu thất bại
            result = cv2.imwrite(save_path, image)
            if result:
                print(f"Lưu ảnh thành công tại: {save_path}")
                return True
            else:
                print("Lưu ảnh thất bại. Kiểm tra lại định dạng file.")
                return False
                
        except Exception as e:
            print(f"Có lỗi xảy ra: {e}")
            return False
    
    @staticmethod   
    def delete_image(image_path):
        """
        image_path: Đường dẫn đầy đủ tới file ảnh cần xoá
        """
        try:
            # Kiểm tra file có tồn tại không
            if not os.path.exists(image_path):
                print(f"❌ Không tìm thấy file ảnh: {image_path}")
                return False

            # Kiểm tra đúng là file (không phải thư mục)
            if not os.path.isfile(image_path):
                print(f"❌ Đường dẫn không phải file: {image_path}")
                return False

            os.remove(image_path)
            print(f"🗑️ Đã xoá ảnh: {image_path}")
            return True

        except Exception as e:
            print(f"❌ Có lỗi xảy ra khi xoá ảnh: {e}")
            return False
        
    @staticmethod
    def create_black_image(width, height, channels=3):
        """
        Tạo ảnh màu đen
        channels = 1 : ảnh grayscale
        channels = 3 : ảnh BGR (OpenCV)
        """
        if channels == 1:
            return np.zeros((height, width), dtype=np.uint8)
        elif channels == 3:
            return np.zeros((height, width, 3), dtype=np.uint8)
        else:
            raise ValueError("channels chỉ hỗ trợ 1 hoặc 3")
    @staticmethod   
    def show_img(img, win_name="Image", wait=0):
        cv2.imshow(win_name, img)
        cv2.waitKey(wait)
        cv2.destroyAllWindows()
    @staticmethod
    def convert_frame_to_base64(frame):
        """
        Convert OpenCV frame sang base64 để gửi cho client
        """
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            return None
        
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        return frame_base64


    @staticmethod
    def bytes_to_ndarray(
        contents: bytes
    ) -> np.ndarray | None:
        if not contents:
            return None
        try:
            nparr = np.frombuffer(
                contents,
                np.uint8
            )
            img = cv2.imdecode(
                nparr,
                cv2.IMREAD_COLOR
            )
            if img is None:
                return None
            return img
        except Exception as e:
            print(
                f"bytes_to_ndarray error: {e}"
            )
            return None
    @staticmethod
    def crop_image(image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> tuple[np.ndarray, int, int]:
        """Cắt ảnh theo hai điểm chéo.
        Args:
            image: Ảnh đầu vào.
            x1: Góc trái trên X.
            y1: Góc trái trên Y.
            x2: Góc phải dưới X.
            y2: Góc phải dưới Y.
        Returns:
            tuple[np.ndarray, int, int]: Ảnh crop, tọa độ left, top.
        """
        image_height, image_width = image.shape[:2]

        left = max(0, min(x1, x2))
        top = max(0, min(y1, y2))
        right = min(image_width, max(x1, x2))
        bottom = min(image_height, max(y1, y2))
        if left >= right or top >= bottom:
            raise ValueError(
                "Vùng crop không hợp lệ."
            )

        return (
            image[top:bottom, left:right],
            left,
            top
        )
    
    @staticmethod
    def convert_canvas_to_image(
        x_start: int,
        y_start: int,
        x_end: int,
        y_end: int,
        canvas_width: int,
        img,
    ):
        """
        Chuyển tọa độ từ Canvas sang ảnh gốc.

        Args:
            x_start, y_start, x_end, y_end: tọa độ trên Canvas
            canvas_width: chiều rộng Canvas hiển thị
            img: ảnh gốc (cv2.imread)

        Returns:
            (x_start, y_start, x_end, y_end) trên ảnh gốc
        """

        img_height, img_width = img.shape[:2]

        scale = img_width / canvas_width

        x_start = int(round(x_start * scale))
        y_start = int(round(y_start * scale))
        x_end = int(round(x_end * scale))
        y_end = int(round(y_end * scale))

        x_start = max(0, min(x_start, img_width - 1))
        x_end = max(0, min(x_end, img_width - 1))
        y_start = max(0, min(y_start, img_height - 1))
        y_end = max(0, min(y_end, img_height - 1))

        return x_start, y_start, x_end, y_end