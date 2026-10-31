from datetime import datetime
import unicodedata
import re

class Aggregate:
    @staticmethod
    def normalize_folder_name(text: str) -> str:
        """
        Chuyển tiếng Việt sang không dấu, thay khoảng trắng bằng '_',
        chỉ giữ [a-z0-9_], dùng cho tên folder.
        """
        if not isinstance(text, str):
            return ""
        # Bỏ khoảng trắng đầu cuối
        text = text.strip().lower()

        # Chuẩn hóa unicode → bỏ dấu tiếng Việt
        text = unicodedata.normalize("NFD", text)
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")

        # Thay khoảng trắng & nhiều dấu cách thành _
        text = re.sub(r"\s+", "_", text)

        # Loại bỏ ký tự đặc biệt
        text = re.sub(r"[^a-z0-9_]", "", text)

        # Tránh __
        text = re.sub(r"_+", "_", text)

        return text
    
    @staticmethod
    def get_today(mode: int = 1) -> str:
        formats = {
            1: "%d-%m-%Y",  # 20-01-2026
            2: "%d/%m/%Y",  # 20/01/2026
            3: "%Y%m%d"     # 20260120
        }
        fmt = formats.get(mode)
        if not fmt:
            raise ValueError("mode phải là 1, 2 hoặc 3")

        return datetime.now().strftime(fmt)
        

    @staticmethod        
    def replace_drive(path: str, target_drive: str = "D:\\") -> str:
        """
        Nếu gặp ':\\' trong đường dẫn thì loại bỏ và chèn target_drive vào.
        Ví dụ: C:\\App\\Log -> D:\\App\\Log
        """
        # Tìm vị trí ':\' đầu tiên
        idx = path.find(":\\")
        if idx != -1:
            # Bỏ phần trước ':\' và thay bằng target_drive
            new_path = target_drive + path[idx+2:]
            return new_path
        else:
            # Nếu không có ':\' thì coi như đường dẫn không hợp lệ
            raise ValueError("Đường dẫn không chứa ':\\'")

    # # Ví dụ sử dụng
    # original_path = r"C:\App_Line_Measurement_Check\Log\date_21-01-2026\log_img"
    # converted_path = replace_drive(original_path, "D:")
    # print(converted_path)
