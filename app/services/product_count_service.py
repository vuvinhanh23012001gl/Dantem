import threading
from typing import Dict
from app.repository.product_count_repository import ProductCountRepository


class ProductCountService:
    """
    Dịch vụ quản lý số lượng sản phẩm OK, NG và Tổng đếm chạy trong runtime.
    Đảm bảo an toàn luồng (thread-safe) khi các stage phán định và router đồng thời truy xuất.
    """

    def __init__(self, repository: ProductCountRepository) -> None:
        self.repository = repository
        self._lock = threading.Lock()

    def get_counts(self) -> Dict[str, int]:
        """
        Lấy số lượng sản phẩm hiện tại.

        Returns:
            Dict[str, int]: Dictionary chứa {"ok": int, "ng": int, "total": int}.
        """
        with self._lock:
            return self.repository.read_counts()

    def record_result(self, is_ok: bool) -> Dict[str, int]:
        """
        Ghi nhận kết quả phán định sản phẩm (OK/NG) và cập nhật tổng số.

        Args:
            is_ok (bool): True nếu sản phẩm đạt tiêu chuẩn OK, False nếu lỗi NG.

        Returns:
            Dict[str, int]: Số đếm mới nhất sau khi cập nhật.
        """
        with self._lock:
            return self.repository.increment_count(is_ok)

    def reset_counts(self) -> Dict[str, int]:
        """
        Đặt lại toàn bộ số đếm OK = 0, NG = 0, Tổng = 0 khi người dùng bấm nút Đặt lại.

        Returns:
            Dict[str, int]: {"ok": 0, "ng": 0, "total": 0}.
        """
        with self._lock:
            return self.repository.reset_counts()
