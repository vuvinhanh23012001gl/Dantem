"""Máy chủ TCP Socket Socket mô phỏng cổng mạng PLC kết nối với PC Vision."""

import logging
import queue
import socket
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app_demorobot.config.settings import (
    CMD_GET_STATUS,
    CMD_HOME,
    CMD_MOV,
    CMD_RESET,
    CMD_STOP,
    DEFAULT_HOST,
    DEFAULT_PORT,
    ENCODING,
    RESP_ARRIVED_HOME,
    RESP_ARRIVED_MOV,
    RESP_BUSY_HOME,
    RESP_BUSY_MOV,
    RESP_READY,
    RESP_STOPPED,
)
from app_demorobot.core.motion_sim import MotionSimulator
from app_demorobot.core.protocol import CommandParser
from app_demorobot.core.robot_state import RobotState, StateEnum

logger = logging.getLogger("PLC_Simulator")


class PLCTCPServer:
    """TCP Server mô phỏng PLC lắng nghe kết nối từ phần mềm Vision PC."""

    def __init__(
        self,
        robot_state: RobotState,
        motion_sim: MotionSimulator,
        event_queue: queue.Queue,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
    ):
        self.robot_state = robot_state
        self.motion_sim = motion_sim
        self.event_queue = event_queue
        self.host = host
        self.port = port

        # Đăng ký callback khi robot đến đích từ MotionSimulator
        self.motion_sim.on_arrived_callback = self._on_motion_arrived

        self._server_socket: Optional[socket.socket] = None
        self._server_thread: Optional[threading.Thread] = None
        self._is_running = False

        self._clients_lock = threading.Lock()
        self._connected_clients: Dict[socket.socket, Tuple[str, int]] = {}

    def _log(self, level: str, message: str) -> None:
        """Đưa log vào hàng đợi để UI hiển thị."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.event_queue.put({
            "type": "LOG",
            "level": level,
            "message": message,
            "timestamp": ts,
        })

    def _emit_server_status(self) -> None:
        """Gửi trạng thái server hiện tại vào queue."""
        with self._clients_lock:
            client_count = len(self._connected_clients)
            client_list = [f"{ip}:{port}" for ip, port in self._connected_clients.values()]
        self.event_queue.put({
            "type": "SERVER_STATUS",
            "running": self._is_running,
            "host": self.host,
            "port": self.port,
            "client_count": client_count,
            "clients": client_list,
        })

    def start(self, host: Optional[str] = None, port: Optional[int] = None) -> Tuple[bool, str]:
        """Khởi động TCP Server trên host và port chỉ định."""
        if self._is_running:
            return False, "Server đang chạy."

        if host:
            self.host = host
        if port:
            self.port = port

        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(5)
            self._server_socket.settimeout(0.5)  # Timeout để luồng server có thể thoát mượt mà
            self._is_running = True

            self._server_thread = threading.Thread(
                target=self._accept_loop,
                name="PLCTCPServer-Listener",
                daemon=True,
            )
            self._server_thread.start()

            msg = f"PLC TCP Server đã mở cổng lắng nghe tại {self.host}:{self.port}"
            self._log("INFO", msg)
            self._emit_server_status()
            return True, msg
        except Exception as e:
            self._is_running = False
            err_msg = f"Không thể mở cổng Server {self.host}:{self.port}: {e}"
            self._log("ERROR", err_msg)
            self._emit_server_status()
            return False, err_msg

    def stop(self) -> None:
        """Dừng TCP Server và đóng mọi kết nối client."""
        if not self._is_running:
            return

        self._is_running = False
        self._log("INFO", f"Đang dừng PLC TCP Server ({self.host}:{self.port})...")

        # Đóng tất cả client sockets
        with self._clients_lock:
            for sock in list(self._connected_clients.keys()):
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    sock.close()
                except Exception:
                    pass
            self._connected_clients.clear()

        # Đóng server socket
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None

        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=1.0)
        self._server_thread = None

        self._log("INFO", "PLC TCP Server đã dừng hoàn toàn.")
        self._emit_server_status()

    def is_running(self) -> bool:
        return self._is_running

    def _accept_loop(self) -> None:
        """Luồng chấp nhận các kết nối mới từ Client."""
        while self._is_running:
            try:
                client_sock, client_addr = self._server_socket.accept()
                client_sock.settimeout(0.5)

                with self._clients_lock:
                    self._connected_clients[client_sock] = client_addr

                self._log("SUCCESS", f"Client mới kết nối thành công: {client_addr[0]}:{client_addr[1]}")
                self._emit_server_status()

                client_thread = threading.Thread(
                    target=self._client_handler_loop,
                    args=(client_sock, client_addr),
                    name=f"ClientHandler-{client_addr[0]}:{client_addr[1]}",
                    daemon=True,
                )
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._is_running:
                    self._log("WARN", f"Lỗi trong accept loop: {e}")
                break

    def _client_handler_loop(self, client_sock: socket.socket, client_addr: Tuple[str, int]) -> None:
        """Luồng xử lý nhận và phản hồi dữ liệu cho từng client."""
        client_str = f"{client_addr[0]}:{client_addr[1]}"
        buffer = ""

        try:
            while self._is_running:
                try:
                    data = client_sock.recv(1024)
                    if not data:
                        # Client đã ngắt kết nối
                        break
                    
                    text = data.decode(ENCODING, errors="ignore")
                    buffer += text

                    # Phân tách gói tin kết thúc bằng \r\n (CRLF)
                    while "\r\n" in buffer:
                        line, buffer = buffer.split("\r\n", 1)
                        line = line.strip()
                        if line:
                            self._handle_single_command(client_sock, client_str, line)

                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break
                except Exception as e:
                    if self._is_running:
                        self._log("WARN", f"Lỗi đọc socket từ {client_str}: {e}")
                    break
        finally:
            with self._clients_lock:
                if client_sock in self._connected_clients:
                    del self._connected_clients[client_sock]
            try:
                client_sock.close()
            except Exception:
                pass
            self._log("INFO", f"Client {client_str} đã ngắt kết nối.")
            self._emit_server_status()

    def _handle_single_command(self, client_sock: socket.socket, client_str: str, raw_cmd: str) -> None:
        """Xử lý một câu lệnh nhận được từ Client."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Ghi nhận vào bảng Lệnh Nhận
        self.event_queue.put({
            "type": "CMD_RECV",
            "timestamp": ts,
            "client": client_str,
            "command": raw_cmd,
        })
        self._log("CMD_IN", f"[{client_str}] -> PC gửi: {raw_cmd}")

        is_valid, cmd_name, params, err_msg = CommandParser.parse_command(raw_cmd)
        if not is_valid:
            self._log("WARN", f"Lệnh không hợp lệ từ {client_str}: {err_msg}")
            err_resp = CommandParser.format_error("E05")
            self._send_to_client(client_sock, client_str, err_resp)
            return

        # Phân nhánh theo lệnh
        if cmd_name == CMD_GET_STATUS:
            resp = self.robot_state.get_status_string()
            self._send_to_client(client_sock, client_str, resp)

        elif cmd_name == CMD_STOP:
            self.motion_sim.cancel_motion()
            self.robot_state.set_stopped()
            self._send_to_client(client_sock, client_str, RESP_STOPPED)

        elif cmd_name == CMD_RESET:
            self.motion_sim.cancel_motion()
            self.robot_state.reset()
            self._send_to_client(client_sock, client_str, RESP_READY)

        elif cmd_name == CMD_MOV:
            # Kiểm tra trạng thái an toàn
            current_status = self.robot_state.get_status_string()
            if self.robot_state.state == StateEnum.ERROR:
                self._send_to_client(client_sock, client_str, current_status)
                return
            if self.robot_state.state == StateEnum.STOPPED:
                self._send_to_client(client_sock, client_str, RESP_STOPPED)
                return
            if self.robot_state.state in (StateEnum.BUSY_MOV, StateEnum.BUSY_HOME):
                self._send_to_client(client_sock, client_str, current_status)
                return

            # Gửi phản hồi ngay lập tức: BUSY,MOV
            self._send_to_client(client_sock, client_str, RESP_BUSY_MOV)
            
            # Bắt đầu mô phỏng chuyển động
            success = self.motion_sim.start_move(params)
            if not success:
                self._send_to_client(client_sock, client_str, self.robot_state.get_status_string())

        elif cmd_name == CMD_HOME:
            current_status = self.robot_state.get_status_string()
            if self.robot_state.state == StateEnum.ERROR:
                self._send_to_client(client_sock, client_str, current_status)
                return
            if self.robot_state.state == StateEnum.STOPPED:
                self._send_to_client(client_sock, client_str, RESP_STOPPED)
                return
            if self.robot_state.state in (StateEnum.BUSY_MOV, StateEnum.BUSY_HOME):
                self._send_to_client(client_sock, client_str, current_status)
                return

            # Gửi phản hồi ngay lập tức: BUSY,HOME
            self._send_to_client(client_sock, client_str, RESP_BUSY_HOME)
            
            # Bắt đầu mô phỏng về gốc
            success = self.motion_sim.start_home()
            if not success:
                self._send_to_client(client_sock, client_str, self.robot_state.get_status_string())

    def _send_to_client(self, client_sock: socket.socket, client_str: str, response_text: str) -> bool:
        """Gửi chuỗi phản hồi tới client cụ thể qua socket."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        packet = CommandParser.format_packet(response_text)
        try:
            client_sock.sendall(packet)
            
            # Ghi nhận vào bảng Lệnh Gửi
            self.event_queue.put({
                "type": "CMD_SENT",
                "timestamp": ts,
                "client": client_str,
                "response": response_text,
            })
            self._log("CMD_OUT", f"[{client_str}] <- PLC gửi: {response_text}")
            return True
        except Exception as e:
            self._log("ERROR", f"Không thể gửi dữ liệu tới {client_str}: {e}")
            return False

    def broadcast_message(self, response_text: str) -> None:
        """Gửi một thông điệp tới tất cả các client đang kết nối."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        packet = CommandParser.format_packet(response_text)
        with self._clients_lock:
            for sock, addr in list(self._connected_clients.items()):
                client_str = f"{addr[0]}:{addr[1]}"
                try:
                    sock.sendall(packet)
                    self.event_queue.put({
                        "type": "CMD_SENT",
                        "timestamp": ts,
                        "client": client_str,
                        "response": response_text,
                    })
                except Exception as e:
                    self._log("WARN", f"Lỗi phát broadcast tới {client_str}: {e}")

    def _on_motion_arrived(self, arrived_signal: str) -> None:
        """Callback được kích hoạt khi robot hoàn thành hành trình di chuyển."""
        self._log("SUCCESS", f"Robot đã đến đích ổn định. Tín hiệu phát đi: {arrived_signal}")
        self.broadcast_message(arrived_signal)
