# Community 59

> 27 nodes

## Key Concepts

- **RobotState** (28 connections) — `app_demorobot/core/robot_state.py`
- **._notify()** (8 connections) — `app_demorobot/core/robot_state.py`
- **.test_robot_state_lifecycle()** (8 connections) — `app_demorobot/tests/test_protocol.py`
- **.reset()** (6 connections) — `app_demorobot/core/robot_state.py`
- **.set_error()** (6 connections) — `app_demorobot/core/robot_state.py`
- **.get_snapshot()** (5 connections) — `app_demorobot/core/robot_state.py`
- **.set_stopped()** (5 connections) — `app_demorobot/core/robot_state.py`
- **.get_status_string()** (4 connections) — `app_demorobot/core/robot_state.py`
- **.set_arrived_mov()** (4 connections) — `app_demorobot/core/robot_state.py`
- **.set_busy_mov()** (4 connections) — `app_demorobot/core/robot_state.py`
- **._on_state_change()** (4 connections) — `app_demorobot/ui/main_window.py`
- **.set_arrived_home()** (3 connections) — `app_demorobot/core/robot_state.py`
- **.set_busy_home()** (3 connections) — `app_demorobot/core/robot_state.py`
- **.__init__()** (2 connections) — `app_demorobot/core/motion_sim.py`
- **.__init__()** (1 connections) — `app_demorobot/core/robot_state.py`
- **Any** (1 connections)
- **Gặp sự cố hoặc lỗi phần cứng.** (1 connections) — `app_demorobot/core/robot_state.py`
- **Xóa lỗi và phục hồi về READY.** (1 connections) — `app_demorobot/core/robot_state.py`
- **Lấy bản sao dữ liệu an toàn để hiển thị trên giao diện.** (1 connections) — `app_demorobot/core/robot_state.py`
- **Mô hình trạng thái Robot 6-DOF thread-safe với thông báo sự kiện (observer).** (1 connections) — `app_demorobot/core/robot_state.py`
- **Trả về chuỗi trạng thái theo quy chuẩn truyền tin PLC -> PC.** (1 connections) — `app_demorobot/core/robot_state.py`
- **Chuyển sang trạng thái đang di chuyển theo lệnh MOV.** (1 connections) — `app_demorobot/core/robot_state.py`
- **Đã đến đích lệnh MOV: Cập nhật tọa độ hiện tại và quay về READY.** (1 connections) — `app_demorobot/core/robot_state.py`
- **Chuyển sang trạng thái đang di chuyển về vị trí Home.** (1 connections) — `app_demorobot/core/robot_state.py`
- **Đã về đến vị trí Home: Cập nhật tọa độ và quay về READY.** (1 connections) — `app_demorobot/core/robot_state.py`
- *... and 2 more nodes in this community*

## Relationships

- [Community 34](Community_34.md) (9 shared connections)
- [Community 73](Community_73.md) (5 shared connections)
- [Community 43](Community_43.md) (3 shared connections)
- [Community 33](Community_33.md) (2 shared connections)
- [Community 114](Community_114.md) (2 shared connections)

## Source Files

- `app_demorobot/core/motion_sim.py`
- `app_demorobot/core/robot_state.py`
- `app_demorobot/tests/test_protocol.py`
- `app_demorobot/ui/main_window.py`

## Audit Trail

- EXTRACTED: 46 (74%)
- INFERRED: 16 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*