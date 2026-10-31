# MainWindow

> God node · 43 connections · `app_demorobot/ui/main_window.py`

**Community:** [Community 43](Community_43.md)

## Connections by Relation

### calls
- main() `EXTRACTED`

### contains
- app_demorobot/ui/main_window.py `EXTRACTED`

### imports
- run_simulator.py `EXTRACTED`
- app_demorobot/ui/__init__.py `EXTRACTED`

### method
- ._build_layout() `EXTRACTED`
- ._ensure_test_connected() `EXTRACTED`
- .__init__() `EXTRACTED`
- .trigger_estop() `EXTRACTED`
- .trigger_inject_error() `EXTRACTED`
- ._build_pose_card() `EXTRACTED`
- ._build_history_and_logs() `EXTRACTED`
- ._poll_events() `EXTRACTED`
- .trigger_stop() `EXTRACTED`
- .trigger_reset() `EXTRACTED`
- ._current_time_str() `EXTRACTED`
- ._build_status_card() `EXTRACTED`
- ._build_hardware_controls_card() `EXTRACTED`
- ._render_state() `EXTRACTED`
- .toggle_server() `EXTRACTED`
- .trigger_start() `EXTRACTED`
- .toggle_test_client_connection() `EXTRACTED`
- ._build_server_card() `EXTRACTED`
- ._build_test_client_card() `EXTRACTED`
- ._on_state_change() `EXTRACTED`
- *…and 9 more `method` connection(s) not listed (lowest-degree first to go)*

### rationale_for
- Quản lý toàn bộ giao diện và liên kết các thành phần lõi của ứng dụng giả lập. `EXTRACTED`

### uses
- RobotState `INFERRED`
- PLCTCPServer `INFERRED`
- MotionSimulator `INFERRED`
- TestClient `INFERRED`
- CommandHistoryTable `INFERRED`
- LogViewerWidget `INFERRED`
- StateEnum `INFERRED`
- TowerLightWidget `INFERRED`
- PoseCardWidget `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*