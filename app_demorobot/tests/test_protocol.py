"""Unit tests và Integration tests kiểm tra Parser giao thức và TCP Server sử dụng unittest tiêu chuẩn."""

import queue
import socket
import sys
import time
import unittest
from pathlib import Path

# Thêm đường dẫn dự án
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app_demorobot.config.settings import (
    CMD_GET_STATUS,
    CMD_HOME,
    CMD_MOV,
    CMD_RESET,
    CMD_STOP,
    RESP_ARRIVED_MOV,
    RESP_BUSY_MOV,
    RESP_READY,
    RESP_STOPPED,
)
from app_demorobot.core.motion_sim import MotionSimulator
from app_demorobot.core.protocol import CommandParser
from app_demorobot.core.robot_state import RobotState, StateEnum
from app_demorobot.network.tcp_server import PLCTCPServer


class TestProtocolAndServer(unittest.TestCase):

    def test_command_parser_mov_valid(self):
        raw = "MOV,450.50,-120.25,210.00,180.00,0.00,45.00\r\n"
        is_valid, cmd, params, err = CommandParser.parse_command(raw)
        self.assertTrue(is_valid)
        self.assertEqual(cmd, CMD_MOV)
        self.assertEqual(params["x"], 450.50)
        self.assertEqual(params["y"], -120.25)
        self.assertEqual(params["z"], 210.00)
        self.assertEqual(params["rx"], 180.00)
        self.assertEqual(params["ry"], 0.00)
        self.assertEqual(params["rz"], 45.00)
        self.assertEqual(err, "")

    def test_command_parser_mov_invalid_params(self):
        raw = "MOV,450.50,-120.25\r\n"
        is_valid, cmd, params, err = CommandParser.parse_command(raw)
        self.assertFalse(is_valid)
        self.assertIn("Yêu cầu 6 tọa độ", err)

        raw_bad_type = "MOV,450.50,INVALID,210.00,180.00,0.00,45.00\r\n"
        is_valid, cmd, params, err = CommandParser.parse_command(raw_bad_type)
        self.assertFalse(is_valid)
        self.assertIn("số thực hợp lệ", err)

    def test_command_parser_standard_commands(self):
        for cmd_str in ["HOME", "GET_STATUS", "STOP", "RESET"]:
            is_valid, cmd, _, _ = CommandParser.parse_command(f"{cmd_str}\r\n")
            self.assertTrue(is_valid)
            self.assertEqual(cmd, cmd_str)

    def test_command_parser_unknown(self):
        is_valid, cmd, _, err = CommandParser.parse_command("INVALID_CMD\r\n")
        self.assertFalse(is_valid)
        self.assertIn("Lệnh không xác định", err)

    def test_format_packet(self):
        data = CommandParser.format_packet("ARRIVED,MOV")
        self.assertEqual(data, b"ARRIVED,MOV\r\n")

    def test_robot_state_lifecycle(self):
        state = RobotState()
        self.assertEqual(state.get_status_string(), RESP_READY)

        state.set_busy_mov({"x": 100, "y": 200, "z": 300, "rx": 180, "ry": 0, "rz": 0})
        self.assertEqual(state.get_status_string(), RESP_BUSY_MOV)

        state.set_arrived_mov()
        self.assertEqual(state.get_status_string(), RESP_READY)
        self.assertEqual(state.pose["x"], 100)

        state.set_stopped()
        self.assertEqual(state.get_status_string(), RESP_STOPPED)

        state.reset()
        self.assertEqual(state.get_status_string(), RESP_READY)

        state.set_error("E03")
        self.assertEqual(state.get_status_string(), "ERROR,E03")

    def test_tcp_server_integration(self):
        """Kiểm tra toàn trình (End-to-End) socket TCP Server và Client thực tế."""
        test_port = 29995
        eq = queue.Queue()
        state = RobotState()
        motion = MotionSimulator(state)
        motion.set_delay(0.2)  # Delay ngắn cho test nhanh

        server = PLCTCPServer(
            robot_state=state,
            motion_sim=motion,
            event_queue=eq,
            host="127.0.0.1",
            port=test_port,
        )
        ok, msg = server.start()
        self.assertTrue(ok)

        try:
            time.sleep(0.1)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(2.0)
            client.connect(("127.0.0.1", test_port))

            # 1. Test GET_STATUS
            client.sendall(b"GET_STATUS\r\n")
            resp = client.recv(1024).decode("ascii")
            self.assertEqual(resp, "READY\r\n")

            # 2. Test MOV command
            client.sendall(b"MOV,500.0,0.0,200.0,180.0,0.0,0.0\r\n")
            # Phải nhận được BUSY,MOV trước
            resp1 = client.recv(1024).decode("ascii")
            self.assertEqual(resp1, "BUSY,MOV\r\n")

            # Sau delay 0.2s phải nhận được ARRIVED,MOV
            time.sleep(0.3)
            resp2 = client.recv(1024).decode("ascii")
            self.assertIn("ARRIVED,MOV\r\n", resp2)

            # 3. Test STOP
            client.sendall(b"STOP\r\n")
            resp_stop = client.recv(1024).decode("ascii")
            self.assertEqual(resp_stop, "STOPPED\r\n")

            # 4. Test RESET
            client.sendall(b"RESET\r\n")
            resp_reset = client.recv(1024).decode("ascii")
            self.assertEqual(resp_reset, "READY\r\n")

            client.close()
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
