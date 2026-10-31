"""Client TCP thử nghiệm tích hợp sẵn (Built-in Test Client) để gửi lệnh từ giao diện."""

import socket
import threading
import time
from typing import Callable, Optional, Tuple

from app_demorobot.config.settings import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    ENCODING,
    TERMINATOR,
)


class TestClient:
    """TCP Client tiện ích giúp người dùng giả lập các lệnh từ phía PC Vision."""

    def __init__(self, on_response_callback: Optional[Callable[[str], None]] = None):
        self.on_response_callback = on_response_callback
        self.sock: Optional[socket.socket] = None
        self._is_connected = False
        self._listener_thread: Optional[threading.Thread] = None

    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> Tuple[bool, str]:
        """Kết nối tới PLC TCP Server."""
        if self._is_connected:
            return True, "Đã kết nối sẵn."

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0)
            self.sock.connect((host, port))
            self._is_connected = True

            # Khởi động luồng nhận phản hồi từ PLC
            self._listener_thread = threading.Thread(
                target=self._recv_loop,
                name="TestClient-Receiver",
                daemon=True,
            )
            self._listener_thread.start()
            return True, f"Đã kết nối tới PLC tại {host}:{port}"
        except Exception as e:
            self._is_connected = False
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            return False, f"Không thể kết nối tới {host}:{port}: {e}"

    def disconnect(self) -> None:
        """Ngắt kết nối."""
        self._is_connected = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def send_command(self, cmd_text: str) -> Tuple[bool, str]:
        """Gửi lệnh tới PLC với ký tự kết thúc \\r\\n."""
        if not self._is_connected or not self.sock:
            return False, "Chưa kết nối tới PLC Server."

        clean = cmd_text.strip("\r\n")
        packet = (clean + TERMINATOR).encode(ENCODING)
        try:
            self.sock.sendall(packet)
            return True, f"Đã gửi: {clean}"
        except Exception as e:
            self.disconnect()
            return False, f"Lỗi gửi dữ liệu: {e}"

    def _recv_loop(self) -> None:
        """Luồng liên tục nhận phản hồi từ PLC."""
        buffer = ""
        while self._is_connected and self.sock:
            try:
                self.sock.settimeout(0.5)
                data = self.sock.recv(1024)
                if not data:
                    break
                text = data.decode(ENCODING, errors="ignore")
                buffer += text

                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    line = line.strip()
                    if line and self.on_response_callback:
                        self.on_response_callback(line)
            except socket.timeout:
                continue
            except Exception:
                break
        self.disconnect()
