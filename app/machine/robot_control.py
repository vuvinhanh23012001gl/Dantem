"""Module điều khiển Robot / Cobot 6-DOF qua giao thức Ethernet TCP Socket."""

import logging
import socket
import threading
import time
from typing import Dict, List, Optional, Tuple

from app.config.robot_config import RobotConfig

logger = logging.getLogger(__name__)


class RobotControl:
    """Quản lý kết nối TCP Socket và gửi các lệnh điều khiển Cobot 6-DOF tới PLC."""

    def __init__(self, robot_config: Optional[RobotConfig] = None):
        self.robot_config = robot_config or RobotConfig()
        self._lock = threading.RLock()
        self._sock: Optional[socket.socket] = None

    def _get_connection_params(self) -> Tuple[str, int, float, str, str]:
        """Lấy thông số mạng từ robot_config."""
        cfg = self.robot_config.to_dict()
        conn = cfg.get("connection", {})
        ip = conn.get("plc_ip", "127.0.0.1")
        port = int(conn.get("plc_port", 2000))
        timeout_ms = float(conn.get("timeout_ms", 1500))
        encoding = conn.get("encoding", "ASCII").lower()
        terminator = conn.get("terminator", "\r\n")
        return ip, port, timeout_ms / 1000.0, encoding, terminator

    def is_connected(self) -> bool:
        """Kiểm tra xem socket có đang kết nối không."""
        with self._lock:
            return self._sock is not None

    def connect(self) -> Tuple[bool, str]:
        """Khởi tạo kết nối TCP Socket tới PLC."""
        with self._lock:
            if self._sock:
                return True, "Đã kết nối sẵn sàng."

            ip, port, timeout_sec, _, _ = self._get_connection_params()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout_sec)
                sock.connect((ip, port))
                self._sock = sock
                logger.info("Kết nối TCP Socket tới PLC (%s:%d) thành công.", ip, port)
                return True, f"Kết nối PLC ({ip}:{port}) thành công."
            except Exception as e:
                self._sock = None
                logger.warning("Không thể kết nối TCP Socket tới PLC (%s:%d): %s", ip, port, e)
                return False, f"Không thể kết nối PLC ({ip}:{port}): {str(e)}"

    def disconnect(self) -> None:
        """Đóng kết nối socket an toàn."""
        with self._lock:
            if self._sock:
                try:
                    self._sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self._sock.close()
                except Exception:
                    pass
                self._sock = None
                logger.info("Đã ngắt kết nối TCP Socket tới PLC.")

    def _send_and_wait(
        self,
        command_text: str,
        expected_final: List[str],
        total_timeout_sec: float = 10.0,
    ) -> Tuple[bool, str]:
        """Gửi lệnh và chờ nhận phản hồi kết thúc (kết thúc bằng CRLF)."""
        with self._lock:
            # Đảm bảo kết nối
            if not self._sock:
                ok, msg = self.connect()
                if not ok:
                    return False, f"❌ {msg}"

            _, _, conn_timeout, encoding, terminator = self._get_connection_params()
            clean_cmd = command_text.strip("\r\n")
            packet = (clean_cmd + terminator).encode(encoding)

            try:
                self._sock.sendall(packet)
                logger.debug("Đã gửi tới PLC: %s", clean_cmd)
            except Exception as e:
                self.disconnect()
                return False, f"❌ Lỗi gửi lệnh qua socket: {str(e)}"

            # Chờ nhận phản hồi
            buffer = ""
            start_time = time.time()

            while time.time() - start_time < total_timeout_sec:
                try:
                    self._sock.settimeout(1.0)
                    chunk = self._sock.recv(1024)
                    if not chunk:
                        self.disconnect()
                        return False, "❌ PLC đã đóng kết nối socket bất ngờ."
                    
                    buffer += chunk.decode(encoding, errors="ignore")

                    while terminator in buffer:
                        line, buffer = buffer.split(terminator, 1)
                        line = line.strip()
                        if not line:
                            continue

                        logger.debug("Nhận từ PLC: %s", line)

                        # Nếu nhận lỗi hoặc dừng
                        if line.startswith("ERROR"):
                            return False, f"❌ PLC báo lỗi: {line}"
                        if line == "STOPPED" and "STOPPED" not in expected_final:
                            return False, "⚠️ Robot đã bị dừng (STOPPED)."

                        # Kiểm tra xem có phải tín hiệu kết thúc mong đợi không
                        if any(line == exp or line.startswith(exp) for exp in expected_final):
                            return True, line

                        # Tín hiệu BUSY -> tiếp tục chờ
                        if line.startswith("BUSY"):
                            continue

                except socket.timeout:
                    continue
                except Exception as e:
                    self.disconnect()
                    return False, f"❌ Lỗi nhận dữ liệu từ PLC: {str(e)}"

            return False, f"❌ Hết thời gian chờ phản hồi ({total_timeout_sec}s) từ PLC cho lệnh '{clean_cmd}'."

    def move_to_point(
        self,
        x: float,
        y: float,
        z: float,
        rx: float = 180.0,
        ry: float = 0.0,
        rz: float = 0.0,
        timeout_sec: float = 12.0,
    ) -> Tuple[bool, str]:
        """Gửi lệnh MOV điều khiển Cobot đến tọa độ đích 6-DOF (mm và độ)."""
        # 1. Kiểm tra an toàn trước khi gửi
        is_safe, safe_msg = self.robot_config.is_pose_safe(x, y, z, rx, ry, rz)
        if not is_safe:
            return False, f"❌ Tọa độ vi phạm giới hạn an toàn: {safe_msg}"

        # 2. Định dạng lệnh: MOV,X,Y,Z,Rx,Ry,Rz
        cmd = f"MOV,{x:.2f},{y:.2f},{z:.2f},{rx:.2f},{ry:.2f},{rz:.2f}"
        ok, resp = self._send_and_wait(
            cmd,
            expected_final=["ARRIVED,MOV", "READY"],
            total_timeout_sec=timeout_sec,
        )
        if ok:
            return True, f"✅ Robot đã đến đích: X={x:.2f}, Y={y:.2f}, Z={z:.2f}, Rx={rx:.2f}, Ry={ry:.2f}, Rz={rz:.2f}"
        return False, resp

    def home(self, timeout_sec: float = 15.0) -> Tuple[bool, str]:
        """Gửi lệnh HOME đưa Robot về vị trí an toàn ban đầu."""
        ok, resp = self._send_and_wait(
            "HOME",
            expected_final=["ARRIVED,HOME", "READY"],
            total_timeout_sec=timeout_sec,
        )
        if ok:
            return True, "✅ Robot đã về vị trí gốc (Home) thành công."
        return False, resp

    def stop(self) -> Tuple[bool, str]:
        """Gửi lệnh STOP dừng robot ngay lập tức."""
        ok, resp = self._send_and_wait(
            "STOP",
            expected_final=["STOPPED"],
            total_timeout_sec=3.0,
        )
        if ok:
            return True, "⏹ Đã dừng chuyển động Robot thành công."
        return False, resp

    def reset(self) -> Tuple[bool, str]:
        """Gửi lệnh RESET xóa trạng thái lỗi."""
        ok, resp = self._send_and_wait(
            "RESET",
            expected_final=["READY"],
            total_timeout_sec=3.0,
        )
        if ok:
            return True, "🔄 Đã reset lỗi, Robot trở về trạng thái READY."
        return False, resp

    def get_status(self) -> Tuple[bool, str]:
        """Truy vấn trạng thái tức thời của Robot."""
        ok, resp = self._send_and_wait(
            "GET_STATUS",
            expected_final=["READY", "BUSY", "STOPPED", "ERROR"],
            total_timeout_sec=2.0,
        )
        return ok, resp
