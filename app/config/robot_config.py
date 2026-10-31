import json
import logging
import math
import os
import re
from typing import Any, Dict, Optional, Tuple
from pathlib import Path

from .base_config import BaseConfig
from app.config.path_config import PATH_FILE_DATA_CONFIG_ROBOT

logger = logging.getLogger(__name__)


class RobotConfig(BaseConfig):
    """Quản lý cấu hình kết nối mạng Ethernet + TCP Socket và giới hạn an toàn 6-DOF của Robot."""

    DEFAULT_CONFIG: Dict[str, Any] = {
        "connection": {
            "protocol": "TCP_SOCKET",
            "plc_role": "SERVER",
            "plc_ip": "192.168.1.10",
            "plc_port": 2000,
            "pc_role": "CLIENT",
            "pc_ip": "192.168.1.100",
            "subnet_mask": "255.255.255.0",
            "timeout_ms": 1500,
            "encoding": "ASCII",
            "delimiter": ",",
            "terminator": "\r\n",
        },
        "safety_limits": {
            "x_min": 100.0,
            "x_max": 800.0,
            "y_min": -500.0,
            "y_max": 500.0,
            "z_min": 50.0,
            "z_max": 450.0,
            "z_safe": 250.0,
            "max_reach": 800.0,
            "min_deadzone": 150.0,
            "rx_min": 170.0,
            "rx_max": 190.0,
            "ry_min": -10.0,
            "ry_max": 10.0,
            "rz_min": -180.0,
            "rz_max": 180.0,
        },
        "commands": {
            "move": "MOV",
            "home": "HOME",
            "stop": "STOP",
            "reset": "RESET",
            "get_status": "GET_STATUS",
        },
    }

    def __init__(self, path_config: Optional[str] = None):
        self.path_config = path_config or PATH_FILE_DATA_CONFIG_ROBOT
        self.config_data: Dict[str, Any] = {}
        self.load()

    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Trả về bản sao cấu hình mặc định an toàn của Robot."""
        import copy
        return copy.deepcopy(cls.DEFAULT_CONFIG)

    def load(self) -> None:
        """Đọc file cấu hình JSON. Nếu chưa có hoặc lỗi, khởi tạo từ mặc định."""
        p = Path(self.path_config)
        if not p.exists():
            logger.info("File cấu hình %s chưa tồn tại. Đang tạo từ mặc định.", self.path_config)
            self.config_data = self.get_default_config()
            self.save()
            return

        try:
            with open(p, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict) and "connection" in loaded and "safety_limits" in loaded:
                    self.config_data = loaded
                else:
                    logger.warning("Cấu trúc file %s không hợp lệ. Khôi phục mặc định.", self.path_config)
                    self.config_data = self.get_default_config()
                    self.save()
        except Exception as e:
            logger.error("Lỗi khi đọc %s: %s. Dùng mặc định.", self.path_config, e)
            self.config_data = self.get_default_config()

    def save(self) -> bool:
        """Lưu cấu hình hiện tại vào file JSON."""
        try:
            p = Path(self.path_config)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            logger.info("Đã lưu cấu hình robot vào %s", self.path_config)
            return True
        except Exception as e:
            logger.error("Lỗi khi lưu cấu hình robot vào %s: %s", self.path_config, e)
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Xuất dữ liệu cấu hình dưới dạng dictionary."""
        return self.config_data

    def update(self, new_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Cập nhật dữ liệu cấu hình mới sau khi đã validate chặt chẽ."""
        is_valid, msg = self.validate_config(new_data)
        if not is_valid:
            return False, msg

        # Hợp nhất sâu (deep merge) connection, safety_limits, commands
        for section in ["connection", "safety_limits", "commands"]:
            if section in new_data and isinstance(new_data[section], dict):
                if section not in self.config_data:
                    self.config_data[section] = {}
                self.config_data[section].update(new_data[section])

        ok = self.save()
        if ok:
            return True, "Lưu cấu hình robot thành công"
        return False, "Lỗi khi ghi file cấu hình robot"

    @staticmethod
    def validate_config(data: Dict[str, Any]) -> Tuple[bool, str]:
        """Kiểm tra tính hợp lệ của toàn bộ dữ liệu cấu hình."""
        if not isinstance(data, dict):
            return False, "Dữ liệu cấu hình phải là dictionary"

        conn = data.get("connection", {})
        if conn:
            plc_ip = conn.get("plc_ip")
            if plc_ip and not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", str(plc_ip)):
                return False, f"Địa chỉ IP PLC không hợp lệ: {plc_ip}"

            port = conn.get("plc_port")
            if port is not None:
                try:
                    port_val = int(port)
                    if not (1 <= port_val <= 65535):
                        return False, f"Cổng Port phải nằm trong khoảng 1 - 65535: {port_val}"
                except ValueError:
                    return False, f"Cổng Port không phải số nguyên: {port}"

            timeout = conn.get("timeout_ms")
            if timeout is not None:
                try:
                    t_val = int(timeout)
                    if t_val < 100:
                        return False, "Timeout tối thiểu phải là 100ms"
                except ValueError:
                    return False, "Timeout phải là số nguyên (ms)"

        limits = data.get("safety_limits", {})
        if limits:
            # Check min < max
            pairs = [
                ("x_min", "x_max", "Trục X"),
                ("y_min", "y_max", "Trục Y"),
                ("z_min", "z_max", "Trục Z"),
                ("rx_min", "rx_max", "Góc Rx"),
                ("ry_min", "ry_max", "Góc Ry"),
                ("rz_min", "rz_max", "Góc Rz"),
            ]
            for min_key, max_key, label in pairs:
                if min_key in limits and max_key in limits:
                    try:
                        v_min = float(limits[min_key])
                        v_max = float(limits[max_key])
                        if v_min >= v_max:
                            return False, f"{label}: Giá trị Min ({v_min}) phải nhỏ hơn Max ({v_max})"
                    except ValueError:
                        return False, f"{label}: Tọa độ phải là số thực"

            # Check Z_min >= 0
            if "z_min" in limits and float(limits["z_min"]) < 0:
                return False, "Z_min phải lớn hơn hoặc bằng 0mm để chống đâm mặt bàn"

            # Check Reach
            if "max_reach" in limits and float(limits["max_reach"]) <= 0:
                return False, "Tầm với tối đa MAX_REACH phải lớn hơn 0"

        return True, "Cấu hình hợp lệ"

    def is_pose_safe(self, x: float, y: float, z: float, rx: float, ry: float, rz: float) -> Tuple[bool, str]:
        """Kiểm tra một tọa độ 6-DOF cụ thể có nằm trong vùng an toàn trước khi gửi lệnh MOV."""
        lim = self.config_data.get("safety_limits", {})
        if not lim:
            return True, "Không có giới hạn cấu hình"

        # 1. Hộp không gian
        if not (lim.get("x_min", -9999) <= x <= lim.get("x_max", 9999)):
            return False, f"Tọa độ X={x:.2f} ngoài giới hạn [{lim.get('x_min')}, {lim.get('x_max')}]"

        if not (lim.get("y_min", -9999) <= y <= lim.get("y_max", 9999)):
            return False, f"Tọa độ Y={y:.2f} ngoài giới hạn [{lim.get('y_min')}, {lim.get('y_max')}]"

        if not (lim.get("z_min", 0) <= z <= lim.get("z_max", 9999)):
            return False, f"Tọa độ Z={z:.2f} ngoài giới hạn an toàn [{lim.get('z_min')}, {lim.get('z_max')}] (Cảnh báo đâm bàn)"

        # 2. Bán kính tầm với
        radius = math.sqrt(x * x + y * y)
        max_reach = lim.get("max_reach", 9999)
        if radius > max_reach:
            return False, f"Bán kính tầm với R={radius:.2f}mm vượt quá tầm với tối đa {max_reach}mm"

        min_deadzone = lim.get("min_deadzone", 0)
        if radius < min_deadzone:
            return False, f"Bán kính R={radius:.2f}mm rơi vào vùng chết sát chân đế ({min_deadzone}mm)"

        # 3. Góc xoay
        if not (lim.get("rx_min", -360) <= rx <= lim.get("rx_max", 360)):
            return False, f"Góc Rx={rx:.2f}° ngoài giới hạn [{lim.get('rx_min')}, {lim.get('rx_max')}]"

        if not (lim.get("ry_min", -360) <= ry <= lim.get("ry_max", 360)):
            return False, f"Góc Ry={ry:.2f}° ngoài giới hạn [{lim.get('ry_min')}, {lim.get('ry_max')}]"

        if not (lim.get("rz_min", -360) <= rz <= lim.get("rz_max", 360)):
            return False, f"Góc Rz={rz:.2f}° ngoài giới hạn [{lim.get('rz_min')}, {lim.get('rz_max')}] (Bảo vệ cáp)"

        return True, "Tọa độ hợp lệ và an toàn"
