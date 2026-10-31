"""Quản lý trạng thái vận hành và tọa độ 6-DOF của Robot Simulator."""

import enum
import threading
from typing import Any, Callable, Dict, Optional
from app_demorobot.config.settings import (
    HOME_POSE,
    RESP_ARRIVED_HOME,
    RESP_ARRIVED_MOV,
    RESP_BUSY_HOME,
    RESP_BUSY_MOV,
    RESP_ERROR_PREFIX,
    RESP_READY,
    RESP_STOPPED,
)


class StateEnum(enum.Enum):
    READY = "READY"
    BUSY_MOV = "BUSY_MOV"
    BUSY_HOME = "BUSY_HOME"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class RobotState:
    """Mô hình trạng thái Robot 6-DOF thread-safe với thông báo sự kiện (observer)."""

    def __init__(self, on_change_callback: Optional[Callable[["RobotState"], None]] = None):
        self._lock = threading.RLock()
        self.state: StateEnum = StateEnum.READY
        self.current_error_code: Optional[str] = None
        
        # Tọa độ 6-DOF hiện tại
        self.pose: Dict[str, float] = dict(HOME_POSE)
        # Tọa độ đích đang di chuyển tới
        self.target_pose: Dict[str, float] = dict(HOME_POSE)
        
        self.on_change_callback = on_change_callback

    def _notify(self) -> None:
        if self.on_change_callback:
            try:
                self.on_change_callback(self)
            except Exception:
                pass

    def get_status_string(self) -> str:
        """Trả về chuỗi trạng thái theo quy chuẩn truyền tin PLC -> PC."""
        with self._lock:
            if self.state == StateEnum.READY:
                return RESP_READY
            elif self.state == StateEnum.BUSY_MOV:
                return RESP_BUSY_MOV
            elif self.state == StateEnum.BUSY_HOME:
                return RESP_BUSY_HOME
            elif self.state == StateEnum.STOPPED:
                return RESP_STOPPED
            elif self.state == StateEnum.ERROR:
                err = self.current_error_code or "E01"
                return f"{RESP_ERROR_PREFIX}{err}"
            return RESP_READY

    def set_busy_mov(self, target: Dict[str, float]) -> None:
        """Chuyển sang trạng thái đang di chuyển theo lệnh MOV."""
        with self._lock:
            self.state = StateEnum.BUSY_MOV
            self.target_pose = dict(target)
            self.current_error_code = None
        self._notify()

    def set_arrived_mov(self) -> None:
        """Đã đến đích lệnh MOV: Cập nhật tọa độ hiện tại và quay về READY."""
        with self._lock:
            if self.state == StateEnum.BUSY_MOV:
                self.pose = dict(self.target_pose)
                self.state = StateEnum.READY
        self._notify()

    def set_busy_home(self) -> None:
        """Chuyển sang trạng thái đang di chuyển về vị trí Home."""
        with self._lock:
            self.state = StateEnum.BUSY_HOME
            self.target_pose = dict(HOME_POSE)
            self.current_error_code = None
        self._notify()

    def set_arrived_home(self) -> None:
        """Đã về đến vị trí Home: Cập nhật tọa độ và quay về READY."""
        with self._lock:
            if self.state == StateEnum.BUSY_HOME:
                self.pose = dict(HOME_POSE)
                self.state = StateEnum.READY
        self._notify()

    def set_stopped(self) -> None:
        """Dừng Robot ngay lập tức (do lệnh STOP hoặc nút dừng trên tủ)."""
        with self._lock:
            self.state = StateEnum.STOPPED
        self._notify()

    def set_error(self, code: str) -> None:
        """Gặp sự cố hoặc lỗi phần cứng."""
        with self._lock:
            self.state = StateEnum.ERROR
            self.current_error_code = code
        self._notify()

    def reset(self) -> None:
        """Xóa lỗi và phục hồi về READY."""
        with self._lock:
            self.state = StateEnum.READY
            self.current_error_code = None
        self._notify()

    def get_snapshot(self) -> Dict[str, Any]:
        """Lấy bản sao dữ liệu an toàn để hiển thị trên giao diện."""
        with self._lock:
            return {
                "state": self.state.value,
                "status_str": self.get_status_string(),
                "error_code": self.current_error_code,
                "pose": dict(self.pose),
                "target_pose": dict(self.target_pose),
                "tower_green": self.state in (StateEnum.READY, StateEnum.BUSY_MOV, StateEnum.BUSY_HOME),
                "tower_yellow": self.state == StateEnum.STOPPED,
                "tower_red": self.state == StateEnum.ERROR,
                "buzzer": self.state == StateEnum.ERROR,
            }
