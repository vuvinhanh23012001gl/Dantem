"""Bộ điều khiển giả lập thời gian trễ chuyển động của Robot."""

import threading
import time
from typing import Callable, Dict, Optional
from app_demorobot.config.settings import (
    DEFAULT_MOTION_DELAY_SEC,
    RESP_ARRIVED_HOME,
    RESP_ARRIVED_MOV,
)
from app_demorobot.core.robot_state import RobotState, StateEnum


class MotionSimulator:
    """Giả lập chu trình di chuyển của Robot với thời gian chờ cố định có thể cấu hình."""

    def __init__(self, robot_state: RobotState, on_arrived_callback: Optional[Callable[[str], None]] = None):
        self.robot_state = robot_state
        self.on_arrived_callback = on_arrived_callback
        self.delay_sec: float = DEFAULT_MOTION_DELAY_SEC
        
        self._current_timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def set_delay(self, seconds: float) -> None:
        """Cập nhật thời gian trễ di chuyển."""
        with self._lock:
            self.delay_sec = max(0.1, min(10.0, float(seconds)))

    def get_delay(self) -> float:
        """Lấy thời gian trễ hiện tại."""
        with self._lock:
            return self.delay_sec

    def start_move(self, target_pose: Dict[str, float]) -> bool:
        """Bắt đầu chu trình di chuyển theo lệnh MOV.
        
        Trả về True nếu bắt đầu thành công, False nếu Robot đang bận hoặc lỗi.
        """
        with self._lock:
            if self.robot_state.state in (StateEnum.BUSY_MOV, StateEnum.BUSY_HOME):
                return False
            if self.robot_state.state in (StateEnum.ERROR, StateEnum.STOPPED):
                return False

            self.cancel_motion()
            self._stop_event.clear()
            self.robot_state.set_busy_mov(target_pose)

            delay = self.delay_sec

            def _motion_worker():
                # Chờ hết thời gian delay hoặc bị hủy bởi stop_event
                is_cancelled = self._stop_event.wait(timeout=delay)
                if not is_cancelled:
                    self.robot_state.set_arrived_mov()
                    if self.on_arrived_callback:
                        self.on_arrived_callback(RESP_ARRIVED_MOV)

            self._current_timer_thread = threading.Thread(
                target=_motion_worker,
                name="MotionWorker-MOV",
                daemon=True,
            )
            self._current_timer_thread.start()
            return True

    def start_home(self) -> bool:
        """Bắt đầu chu trình di chuyển về vị trí Home."""
        with self._lock:
            if self.robot_state.state in (StateEnum.BUSY_MOV, StateEnum.BUSY_HOME):
                return False
            if self.robot_state.state in (StateEnum.ERROR, StateEnum.STOPPED):
                return False

            self.cancel_motion()
            self._stop_event.clear()
            self.robot_state.set_busy_home()

            delay = self.delay_sec

            def _home_worker():
                is_cancelled = self._stop_event.wait(timeout=delay)
                if not is_cancelled:
                    self.robot_state.set_arrived_home()
                    if self.on_arrived_callback:
                        self.on_arrived_callback(RESP_ARRIVED_HOME)

            self._current_timer_thread = threading.Thread(
                target=_home_worker,
                name="MotionWorker-HOME",
                daemon=True,
            )
            self._current_timer_thread.start()
            return True

    def cancel_motion(self) -> None:
        """Hủy chuyển động ngay lập tức."""
        self._stop_event.set()
        if self._current_timer_thread and self._current_timer_thread.is_alive():
            self._current_timer_thread.join(timeout=0.2)
        self._current_timer_thread = None
