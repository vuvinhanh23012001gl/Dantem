import logging
import socket
import time
from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException, status

from app.config.robot_config import RobotConfig

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/robot",
    tags=["Robot Configuration"]
)


@router.get("/config")
def get_robot_config():
    """Lấy cấu hình hiện tại của Robot và kết nối PLC từ storage/config/robot.json."""
    try:
        cfg = RobotConfig()
        return {
            "status": True,
            "data": cfg.to_dict(),
            "message": "Nạp cấu hình robot thành công"
        }
    except Exception as e:
        logger.error("Lỗi khi đọc cấu hình robot: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể đọc cấu hình robot: {str(e)}"
        )


@router.post("/config")
def save_robot_config(payload: Dict[str, Any] = Body(...)):
    """Lưu và đồng bộ cấu hình Robot vào storage/config/robot.json với kiểm tra ràng buộc an toàn."""
    try:
        cfg = RobotConfig()
        success, message = cfg.update(payload)
        if not success:
            return {
                "status": False,
                "message": message
            }
        return {
            "status": True,
            "data": cfg.to_dict(),
            "message": "Đã lưu cấu hình robot thành công"
        }
    except Exception as e:
        logger.error("Lỗi khi lưu cấu hình robot: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lưu cấu hình robot: {str(e)}"
        )


@router.get("/defaults")
def get_robot_defaults():
    """Lấy bộ thông số cấu hình mặc định an toàn của Robot."""
    return {
        "status": True,
        "data": RobotConfig.get_default_config(),
        "message": "Đã lấy cấu hình mặc định an toàn"
    }


@router.post("/test_connection")
def test_robot_connection(payload: Dict[str, Any] = Body(...)):
    """Kiểm tra thông tuyến mạng TCP Socket thực tế tới PLC (Ping Socket handshake)."""
    plc_ip = payload.get("plc_ip", "192.168.1.10")
    try:
        plc_port = int(payload.get("plc_port", 2000))
    except (ValueError, TypeError):
        return {
            "status": False,
            "error": "Cổng kết nối PLC (Port) không hợp lệ"
        }

    timeout_ms = payload.get("timeout_ms", 1500)
    timeout_sec = max(0.2, float(timeout_ms) / 1000.0)

    sock = None
    start_time = time.perf_counter()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout_sec)
        sock.connect((plc_ip, plc_port))
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "status": True,
            "message": f"Kết nối TCP tới PLC ({plc_ip}:{plc_port}) thành công! Độ trễ: {elapsed_ms:.1f} ms",
            "latency_ms": round(elapsed_ms, 2)
        }
    except socket.timeout:
        return {
            "status": False,
            "error": f"Hết thời gian chờ kết nối (Timeout > {timeout_ms}ms) tới {plc_ip}:{plc_port}."
        }
    except ConnectionRefusedError:
        return {
            "status": False,
            "error": f"PLC từ chối kết nối (Connection Refused) tại {plc_ip}:{plc_port}. Hãy kiểm tra xem PLC đã mở cổng Server chưa."
        }
    except OSError as e:
        return {
            "status": False,
            "error": f"Lỗi mạng socket: {str(e)}"
        }
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


@router.post("/validate_pose")
def validate_pose(payload: Dict[str, Any] = Body(...)):
    """Kiểm tra trước tọa độ xem có vi phạm vùng an toàn Bounding Box hoặc góc xoay không."""
    try:
        x = float(payload["x"])
        y = float(payload["y"])
        z = float(payload["z"])
        rx = float(payload.get("rx", 180.0))
        ry = float(payload.get("ry", 0.0))
        rz = float(payload.get("rz", 0.0))
    except (KeyError, ValueError, TypeError) as e:
        return {
            "status": False,
            "is_safe": False,
            "message": f"Dữ liệu tọa độ không hợp lệ: {e}"
        }

    cfg = RobotConfig()
    is_safe, msg = cfg.is_pose_safe(x, y, z, rx, ry, rz)
    return {
        "status": True,
        "is_safe": is_safe,
        "message": msg
    }
