import threading
from enum import Enum


class RuntimePipelineState(str, Enum):
    """Các trạng thái tổng quát của pipeline runtime."""

    WAIT_START = "WAIT_START"
    READY = "READY"
    RUNNING = "RUNNING"
    WARNING = "WARNING"
    ERROR = "ERROR"
    STOPPED = "STOPPED"


class RuntimeState:
    """Lưu trạng thái dùng chung giữa pipeline và các service.

    Input: không có.
    Output: trạng thái được đọc/ghi thread-safe qua các phương thức getter/setter.
    Errors: không phát sinh trong thao tác trạng thái; giá trị pipeline không hợp lệ
        sẽ bị từ chối bằng ``ValueError``.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._pipeline_state = RuntimePipelineState.WAIT_START
        self._com_connected = False
        self._tcp_connected = False
        self._camera_connected = False
        self._judgment_running = False
        self._product_result = None

    def set_pipeline_state(self, state: RuntimePipelineState) -> None:
        """Cập nhật trạng thái tổng thể của pipeline."""
        if not isinstance(state, RuntimePipelineState):
            raise ValueError("state phải là RuntimePipelineState")
        with self._lock:
            self._pipeline_state = state

    def get_pipeline_state(self) -> RuntimePipelineState:
        """Đọc trạng thái tổng thể hiện tại của pipeline."""
        with self._lock:
            return self._pipeline_state

    def set_connections(self, tcp_or_com_connected: bool, camera_connected: bool) -> None:
        """Cập nhật trạng thái kết nối mạng Ethernet TCP và camera."""
        with self._lock:
            self._tcp_connected = bool(tcp_or_com_connected)
            self._com_connected = bool(tcp_or_com_connected)
            self._camera_connected = bool(camera_connected)

    def get_connections(self) -> tuple[bool, bool]:
        """Trả về ``(com_connected, camera_connected)``."""
        with self._lock:
            return self._com_connected, self._camera_connected

    def set_judgment_running(self, value: bool) -> None:
        """Cập nhật cờ sản phẩm đang được phán định."""
        with self._lock:
            self._judgment_running = bool(value)

    def is_judgment_running(self) -> bool:
        """Đọc cờ sản phẩm đang được phán định."""
        with self._lock:
            return self._judgment_running

    def set_product_result(self, result) -> None:
        """Lưu kết quả sản phẩm cuối cùng cho stage export hoặc client."""
        with self._lock:
            self._product_result = result

    def get_product_result(self):
        """Đọc kết quả sản phẩm cuối cùng."""
        with self._lock:
            return self._product_result

    def request_stop(self) -> None:
        """Yêu cầu dừng pipeline và các stage đang chạy."""
        self._stop_event.set()

    def clear_stop(self) -> None:
        """Xóa yêu cầu dừng để chuẩn bị một chu kỳ mới."""
        self._stop_event.clear()

    def is_stop_requested(self) -> bool:
        """Kiểm tra yêu cầu dừng hiện tại."""
        return self._stop_event.is_set()


class AppContext:
    services = None
    runtime_state = RuntimeState()
context = AppContext()