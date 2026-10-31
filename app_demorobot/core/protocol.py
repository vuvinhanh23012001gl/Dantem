"""Module phân tích cú pháp và đóng gói gói tin chuẩn TCP Socket giữa PC và PLC."""

from typing import Any, Dict, Optional, Tuple
from app_demorobot.config.settings import (
    CMD_GET_STATUS,
    CMD_HOME,
    CMD_MOV,
    CMD_RESET,
    CMD_STOP,
    DELIMITER,
    ENCODING,
    RESP_ERROR_PREFIX,
    TERMINATOR,
)


class CommandParser:
    """Xử lý phân tích chuỗi lệnh nhận được từ PC và định dạng phản hồi chuẩn PLC."""

    @staticmethod
    def parse_command(raw_text: str) -> Tuple[bool, str, Dict[str, Any], str]:
        """Phân tích một dòng lệnh văn bản nhận từ PC.
        
        Args:
            raw_text: Chuỗi lệnh thô nhận từ socket (ví dụ: 'MOV,450.50,-120.25,210,180,0,45\\r\\n')
            
        Returns:
            Tuple[is_valid, cmd_name, params_dict, error_message]
        """
        # Cắt bỏ ký tự xuống dòng và khoảng trắng thừa
        clean_text = raw_text.strip("\r\n").strip()
        if not clean_text:
            return False, "", {}, "Dữ liệu lệnh rỗng"

        tokens = [t.strip() for t in clean_text.split(DELIMITER)]
        cmd_name = tokens[0].upper()

        if cmd_name == CMD_MOV:
            if len(tokens) != 7:
                return (
                    False,
                    cmd_name,
                    {},
                    f"Cú pháp MOV không hợp lệ: Yêu cầu 6 tọa độ (X, Y, Z, Rx, Ry, Rz), nhận được {len(tokens)-1}",
                )
            try:
                x = float(tokens[1])
                y = float(tokens[2])
                z = float(tokens[3])
                rx = float(tokens[4])
                ry = float(tokens[5])
                rz = float(tokens[6])
                params = {
                    "x": x,
                    "y": y,
                    "z": z,
                    "rx": rx,
                    "ry": ry,
                    "rz": rz,
                }
                return True, cmd_name, params, ""
            except ValueError as e:
                return (
                    False,
                    cmd_name,
                    {},
                    f"Giá trị tọa độ trong lệnh MOV phải là số thực hợp lệ: {e}",
                )

        elif cmd_name == CMD_HOME:
            return True, cmd_name, {}, ""

        elif cmd_name == CMD_GET_STATUS:
            return True, cmd_name, {}, ""

        elif cmd_name == CMD_STOP:
            return True, cmd_name, {}, ""

        elif cmd_name == CMD_RESET:
            return True, cmd_name, {}, ""

        else:
            return False, cmd_name, {}, f"Lệnh không xác định: '{clean_text}'"

    @staticmethod
    def format_packet(payload: str) -> bytes:
        """Đóng gói chuỗi phản hồi kèm ký tự kết thúc \\r\\n và mã hóa ASCII."""
        # Đảm bảo chuỗi không chứa sẵn \r\n trước khi ghép
        clean = payload.strip("\r\n")
        return (clean + TERMINATOR).encode(ENCODING)

    @staticmethod
    def format_error(error_code: str) -> str:
        """Tạo chuỗi lỗi chuẩn PLC (ví dụ: 'ERROR,E01')."""
        return f"{RESP_ERROR_PREFIX}{error_code}"
