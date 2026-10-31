from fastapi.testclient import TestClient

from app.config.robot_config import RobotConfig
from app.main import app

client = TestClient(app)


def test_robot_config_defaults():
    """Kiểm tra nạp cấu hình mặc định."""
    defaults = RobotConfig.get_default_config()
    assert "connection" in defaults
    assert "safety_limits" in defaults
    assert defaults["connection"]["protocol"] == "TCP_SOCKET"
    assert defaults["connection"]["plc_port"] == 2000
    assert defaults["safety_limits"]["x_min"] == 100.0
    assert defaults["safety_limits"]["x_max"] == 800.0
    assert defaults["safety_limits"]["z_min"] == 50.0


def test_robot_config_validation():
    """Kiểm tra logic chặn các giá trị không hợp lệ."""
    # 1. IP không hợp lệ
    valid, msg = RobotConfig.validate_config({"connection": {"plc_ip": "999.999.999.9999"}})
    assert not valid
    assert "IP" in msg

    # 2. Port không hợp lệ
    valid, msg = RobotConfig.validate_config({"connection": {"plc_port": 99999}})
    assert not valid
    assert "Port" in msg

    # 3. X_min >= X_max
    valid, msg = RobotConfig.validate_config({"safety_limits": {"x_min": 500, "x_max": 200}})
    assert not valid
    assert "Trục X" in msg

    # 4. Z_min < 0 (Chống đâm bàn)
    valid, msg = RobotConfig.validate_config({"safety_limits": {"z_min": -10, "z_max": 100}})
    assert not valid
    assert "Z_min" in msg


def test_is_pose_safe():
    """Kiểm tra hàm phán định an toàn trước khi gửi lệnh MOV."""
    cfg = RobotConfig()
    # Tọa độ hợp lệ trong vùng
    safe, msg = cfg.is_pose_safe(450.0, -120.0, 210.0, 180.0, 0.0, 45.0)
    assert safe

    # Tọa độ đâm bàn (Z < z_min)
    safe, msg = cfg.is_pose_safe(450.0, -120.0, 20.0, 180.0, 0.0, 45.0)
    assert not safe
    assert "Z=" in msg

    # Tọa độ quá tầm với cánh tay (X=700, Y=450 -> R=832.16mm > max_reach 800mm)
    safe, msg = cfg.is_pose_safe(700.0, 450.0, 210.0, 180.0, 0.0, 45.0)
    assert not safe
    assert "tầm với" in msg

    # Góc xoay Rz vặn xoắn quá 180 độ
    safe, msg = cfg.is_pose_safe(450.0, -120.0, 210.0, 180.0, 0.0, 270.0)
    assert not safe
    assert "Rz=" in msg


def test_api_robot_get_config():
    """Kiểm tra endpoint GET /api/robot/config."""
    resp = client.get("/api/robot/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] is True
    assert "connection" in data["data"]
    assert "safety_limits" in data["data"]


def test_api_robot_get_defaults():
    """Kiểm tra endpoint GET /api/robot/defaults."""
    resp = client.get("/api/robot/defaults")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] is True
    assert data["data"]["connection"]["plc_ip"] == "192.168.1.10"


def test_api_robot_save_config():
    """Kiểm tra endpoint POST /api/robot/config với payload hợp lệ."""
    payload = {
        "connection": {
            "plc_ip": "192.168.1.15",
            "plc_port": 2005,
            "timeout_ms": 2000
        },
        "safety_limits": {
            "x_min": 120.0,
            "x_max": 750.0
        }
    }
    resp = client.post("/api/robot/config", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] is True
    assert data["data"]["connection"]["plc_ip"] == "192.168.1.15"
    assert data["data"]["safety_limits"]["x_min"] == 120.0

    # Khôi phục lại về 192.168.1.10 để không ảnh hưởng dữ liệu chuẩn
    client.post("/api/robot/config", json=RobotConfig.get_default_config())


def test_api_validate_pose():
    """Kiểm tra endpoint POST /api/robot/validate_pose."""
    # Điểm an toàn
    resp = client.post("/api/robot/validate_pose", json={
        "x": 400.0, "y": 0.0, "z": 200.0, "rx": 180.0, "ry": 0.0, "rz": 0.0
    })
    assert resp.status_code == 200
    assert resp.json()["is_safe"] is True

    # Điểm ngoài vùng
    resp = client.post("/api/robot/validate_pose", json={
        "x": 2000.0, "y": 0.0, "z": 200.0, "rx": 180.0, "ry": 0.0, "rz": 0.0
    })
    assert resp.status_code == 200
    assert resp.json()["is_safe"] is False


def test_api_test_connection_unreachable():
    """Kiểm tra endpoint POST /api/robot/test_connection khi không có thiết bị thật."""
    resp = client.post("/api/robot/test_connection", json={
        "plc_ip": "127.0.0.1",
        "plc_port": 59999,
        "timeout_ms": 200
    })
    assert resp.status_code == 200
    # Phải bắt được lỗi từ chối kết nối hoặc timeout và trả về status=False chứ không crash app
    assert resp.json()["status"] is False
    assert "error" in resp.json()
