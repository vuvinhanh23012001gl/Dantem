# Community 65

> 23 nodes

## Key Concepts

- **RobotControl** (17 connections) — `app/machine/robot_control.py`
- **._send_and_wait()** (10 connections) — `app/machine/robot_control.py`
- **.connect()** (4 connections) — `app/machine/robot_control.py`
- **.disconnect()** (4 connections) — `app/machine/robot_control.py`
- **._get_connection_params()** (4 connections) — `app/machine/robot_control.py`
- **.get_status()** (3 connections) — `app/machine/robot_control.py`
- **.home()** (3 connections) — `app/machine/robot_control.py`
- **.is_connected()** (3 connections) — `app/machine/robot_control.py`
- **.move_to_point()** (3 connections) — `app/machine/robot_control.py`
- **.reset()** (3 connections) — `app/machine/robot_control.py`
- **.stop()** (3 connections) — `app/machine/robot_control.py`
- **.__init__()** (2 connections) — `app/machine/robot_control.py`
- **Quản lý kết nối TCP Socket và gửi các lệnh điều khiển Cobot 6-DOF tới PLC.** (1 connections) — `app/machine/robot_control.py`
- **Gửi lệnh MOV điều khiển Cobot đến tọa độ đích 6-DOF (mm và độ).** (1 connections) — `app/machine/robot_control.py`
- **Gửi lệnh HOME đưa Robot về vị trí an toàn ban đầu.** (1 connections) — `app/machine/robot_control.py`
- **Gửi lệnh STOP dừng robot ngay lập tức.** (1 connections) — `app/machine/robot_control.py`
- **Gửi lệnh RESET xóa trạng thái lỗi.** (1 connections) — `app/machine/robot_control.py`
- **Truy vấn trạng thái tức thời của Robot.** (1 connections) — `app/machine/robot_control.py`
- **Lấy thông số mạng từ robot_config.** (1 connections) — `app/machine/robot_control.py`
- **Kiểm tra xem socket có đang kết nối không.** (1 connections) — `app/machine/robot_control.py`
- **Khởi tạo kết nối TCP Socket tới PLC.** (1 connections) — `app/machine/robot_control.py`
- **Đóng kết nối socket an toàn.** (1 connections) — `app/machine/robot_control.py`
- **Gửi lệnh và chờ nhận phản hồi kết thúc (kết thúc bằng CRLF).** (1 connections) — `app/machine/robot_control.py`

## Relationships

- [Community 78](Community_78.md) (2 shared connections)
- [Community 80](Community_80.md) (1 shared connections)
- [Community 134](Community_134.md) (1 shared connections)
- [Community 52](Community_52.md) (1 shared connections)
- [Community 175](Community_175.md) (1 shared connections)
- [Community 100](Community_100.md) (1 shared connections)
- [Community 167](Community_167.md) (1 shared connections)

## Source Files

- `app/machine/robot_control.py`

## Audit Trail

- EXTRACTED: 35 (90%)
- INFERRED: 4 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*