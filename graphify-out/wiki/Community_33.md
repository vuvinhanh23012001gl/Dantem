# Community 33

> 33 nodes

## Key Concepts

- **PLCTCPServer** (25 connections) — `app_demorobot/network/tcp_server.py`
- **._log()** (10 connections) — `app_demorobot/network/tcp_server.py`
- **.broadcast_message()** (9 connections) — `app_demorobot/network/tcp_server.py`
- **._handle_single_command()** (8 connections) — `app_demorobot/network/tcp_server.py`
- **.test_tcp_server_integration()** (8 connections) — `app_demorobot/tests/test_protocol.py`
- **socket** (8 connections)
- **.stop()** (7 connections) — `app_demorobot/network/tcp_server.py`
- **._client_handler_loop()** (6 connections) — `app_demorobot/network/tcp_server.py`
- **._emit_server_status()** (6 connections) — `app_demorobot/network/tcp_server.py`
- **._send_to_client()** (6 connections) — `app_demorobot/network/tcp_server.py`
- **.start()** (6 connections) — `app_demorobot/network/tcp_server.py`
- **.format_packet()** (5 connections) — `app_demorobot/core/protocol.py`
- **.toggle_server()** (5 connections) — `app_demorobot/ui/main_window.py`
- **._accept_loop()** (4 connections) — `app_demorobot/network/tcp_server.py`
- **._on_motion_arrived()** (4 connections) — `app_demorobot/network/tcp_server.py`
- **.format_error()** (3 connections) — `app_demorobot/core/protocol.py`
- **.is_running()** (2 connections) — `app_demorobot/network/tcp_server.py`
- **.test_format_packet()** (2 connections) — `app_demorobot/tests/test_protocol.py`
- **Đóng gói chuỗi phản hồi kèm ký tự kết thúc \\r\\n và mã hóa ASCII.** (1 connections) — `app_demorobot/core/protocol.py`
- **Tạo chuỗi lỗi chuẩn PLC (ví dụ: 'ERROR,E01').** (1 connections) — `app_demorobot/core/protocol.py`
- **Dừng TCP Server và đóng mọi kết nối client.** (1 connections) — `app_demorobot/network/tcp_server.py`
- **Luồng chấp nhận các kết nối mới từ Client.** (1 connections) — `app_demorobot/network/tcp_server.py`
- **Luồng xử lý nhận và phản hồi dữ liệu cho từng client.** (1 connections) — `app_demorobot/network/tcp_server.py`
- **Xử lý một câu lệnh nhận được từ Client.** (1 connections) — `app_demorobot/network/tcp_server.py`
- **Gửi chuỗi phản hồi tới client cụ thể qua socket.** (1 connections) — `app_demorobot/network/tcp_server.py`
- *... and 8 more nodes in this community*

## Relationships

- [Community 34](Community_34.md) (12 shared connections)
- [Community 43](Community_43.md) (6 shared connections)
- [Community 114](Community_114.md) (4 shared connections)
- [Community 73](Community_73.md) (4 shared connections)
- [Community 59](Community_59.md) (2 shared connections)
- [Community 85](Community_85.md) (1 shared connections)
- [Community 52](Community_52.md) (1 shared connections)
- [Community 24](Community_24.md) (1 shared connections)

## Source Files

- `app_demorobot/core/protocol.py`
- `app_demorobot/network/tcp_server.py`
- `app_demorobot/tests/test_protocol.py`
- `app_demorobot/ui/main_window.py`

## Audit Trail

- EXTRACTED: 68 (80%)
- INFERRED: 17 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*