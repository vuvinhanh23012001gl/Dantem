from datetime import datetime
import logging
from pathlib import Path
import shutil
import time
from typing import Any
import cv2

logger = logging.getLogger(__name__)


class Log_Img:
    """Quản lý lưu trữ hình ảnh kiểm tra và phán định.

    Hỗ trợ các chế độ lưu:
    - ALL: Lưu toàn bộ ảnh phán định (cả OK và NG)
    - NG_ONLY: Chỉ lưu ảnh sản phẩm NG (tiết kiệm dung lượng ổ đĩa)
    - OFF: Tắt tính năng lưu ảnh
    """

    extension = "jpg"

    def __init__(
        self,
        path_img: str | Path,
        open_log_img: bool = True,
        save_mode: str = "NG_ONLY",
        jpeg_quality: int = 90,
    ):
        self.path_base = Path(path_img)
        self.open_log = open_log_img
        self.save_mode = str(save_mode).upper()
        self.jpeg_quality = max(10, min(100, int(jpeg_quality)))

    def set_save_mode(self, mode: str) -> None:
        """Cập nhật chế độ lưu ảnh: ALL, NG_ONLY, OFF."""
        self.save_mode = str(mode).upper()

    def set_enable(self, enable: bool) -> None:
        self.open_log = bool(enable)

    def save(
        self,
        img: Any,
        file_name: str,
        status: str = "OK",
        product_name: str = "DEFAULT_PRODUCT",
        sub_dir: str | None = None,
        source_file: str | Path | None = None,
    ) -> Path | None:
        """Lưu hình ảnh phán định xuống đĩa cứng theo chính sách cấu hình.

        Args:
            img: Ma trận ảnh numpy (BGR).
            file_name: Tên tệp (không cần phần mở rộng).
            status: Trạng thái phán định ("OK" hoặc "NG").
            product_name: Tên sản phẩm để phân nhóm thư mục.
            sub_dir: Tùy chọn chỉ định thư mục con cụ thể.
            source_file: Đường dẫn tệp ảnh đã lưu sẵn (nếu có) để copy nhanh, tránh encode lại.

        Returns:
            Path của ảnh đã lưu, hoặc None nếu bị bỏ qua/lỗi.
        """
        if not self.open_log or self.save_mode == "OFF":
            return None

        status_upper = str(status).upper()
        # Bộ lọc lưu trữ: Nếu cấu hình NG_ONLY mà sản phẩm OK thì bỏ qua
        if self.save_mode == "NG_ONLY" and status_upper != "NG":
            return None

        if img is None or not hasattr(img, "shape"):
            return None

        if not file_name or not isinstance(file_name, str):
            return None

        clean_file_name = file_name.strip().replace(" ", "_")

        # Đảm bảo tên file ảnh luôn bắt đầu bằng OK_ hoặc NG_
        if not (clean_file_name.startswith("OK_") or clean_file_name.startswith("NG_")):
            clean_file_name = f"{status_upper}_{clean_file_name}"

        # Thư mục đích: nếu sub_dir được chỉ định thì ghép thêm, mặc định lưu thẳng vào path_base (Log_img)
        if sub_dir:
            target_dir = self.path_base / sub_dir
        else:
            target_dir = self.path_base

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / f"{clean_file_name}.{self.extension}"

            # Tối ưu hóa: Nếu có ảnh nguồn đã lưu sẵn (từ output phán định), copy trực tiếp thay vì nén JPEG lại từ đầu
            if source_file:
                src_path = Path(source_file)
                # Đợi tối đa 50ms nếu file nguồn đang được ghi bởi luồng output saver
                for _ in range(5):
                    if src_path.exists() and src_path.is_file() and src_path.stat().st_size > 0:
                        try:
                            shutil.copy2(str(src_path), str(target_file))
                            return target_file
                        except Exception as copy_err:
                            logger.debug("[Log_Img] Không thể copy từ %s, fallback cv2.imwrite: %s", src_path, copy_err)
                            break
                    time.sleep(0.01)

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            success = cv2.imwrite(str(target_file), img, encode_param)
            if success:
                return target_file
            else:
                logger.warning("[Log_Img] cv2.imwrite trả về False cho: %s", target_file)
                return None
        except Exception as e:
            logger.error("[Log_Img] Lỗi khi lưu hình ảnh %s: %s", clean_file_name, e)
            return None