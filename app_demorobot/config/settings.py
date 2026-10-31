"""Cấu hình và thông số mặc định cho phần mềm PLC Robot Simulator."""

from typing import Dict, Any

# Cấu hình mạng TCP Socket mặc định (Theo Bang_Giao_Tiep_Robot_PLC_PROD4.xlsx)
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 2000
ENCODING: str = "ascii"
DELIMITER: str = ","
TERMINATOR: str = "\r\n"
DEFAULT_TIMEOUT_MS: int = 1500

# Thời gian trễ giả lập chuyển động (giây)
DEFAULT_MOTION_DELAY_SEC: float = 1.5
MIN_MOTION_DELAY_SEC: float = 0.1
MAX_MOTION_DELAY_SEC: float = 10.0

# Vị trí gốc chuẩn (Home Pose)
HOME_POSE: Dict[str, float] = {
    "x": 300.00,
    "y": 0.00,
    "z": 250.00,
    "rx": 180.00,
    "ry": 0.00,
    "rz": 0.00,
}

# Danh mục mã lỗi mô phỏng (Sheet 2 - Tap_Lenh_Giao_Tiep)
ERROR_CODES: Dict[str, str] = {
    "E01": "E01 - Quá tải động cơ trục Servo (Overload)",
    "E02": "E02 - Vượt giới hạn hành trình 6-DOF (Stroke Limit)",
    "E03": "E03 - Cửa an toàn máy mở (Safety Door Opened)",
    "E04": "E04 - Áp suất khí nén tụt dưới ngưỡng (Low Air Pressure)",
    "E05": "E05 - Cú pháp lệnh hoặc số lượng tham số sai (Syntax Error)",
}

# Danh sách lệnh chuẩn từ PC gửi tới PLC
CMD_MOV: str = "MOV"
CMD_HOME: str = "HOME"
CMD_GET_STATUS: str = "GET_STATUS"
CMD_STOP: str = "STOP"
CMD_RESET: str = "RESET"

# Danh sách phản hồi chuẩn từ PLC gửi về PC
RESP_READY: str = "READY"
RESP_BUSY_MOV: str = "BUSY,MOV"
RESP_ARRIVED_MOV: str = "ARRIVED,MOV"
RESP_BUSY_HOME: str = "BUSY,HOME"
RESP_ARRIVED_HOME: str = "ARRIVED,HOME"
RESP_STOPPED: str = "STOPPED"
RESP_ERROR_PREFIX: str = "ERROR,"
