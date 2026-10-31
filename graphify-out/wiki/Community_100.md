# Community 100

> 12 nodes

## Key Concepts

- **.stop()** (8 connections) — `app/container.py`
- **.stop()** (4 connections) — `app/machine/iaicontrol.py`
- **.stop_thread_handler_stm32()** (4 connections) — `app/machine/iaicontrol.py`
- **.stop_thread_input_handler_stm32()** (4 connections) — `app/machine/iaicontrol.py`
- **.stop_log_thread()** (4 connections) — `app/services/log/log_manager.py`
- **.request_stop()** (3 connections) — `app/core/context.py`
- **Dừng toàn bộ dịch vụ, giải phóng cổng COM, đóng Camera, ngắt luồng và giải…** (1 connections) — `app/container.py`
- **Yêu cầu dừng pipeline và các stage đang chạy.** (1 connections) — `app/core/context.py`
- **Dừng luồng chính xử lý logic và gửi dữ liệu Output tới STM32.** (1 connections) — `app/machine/iaicontrol.py`
- **Dừng luồng đọc dữ liệu đầu vào từ các nút nhấn vật lý của STM32.** (1 connections) — `app/machine/iaicontrol.py`
- **Dừng toàn bộ các luồng hoạt động của bộ điều khiển STM32/IAI và hủy đăng ký RX…** (1 connections) — `app/machine/iaicontrol.py`
- **Dừng luồng ghi log và worker dọn dẹp an toàn.** (1 connections) — `app/services/log/log_manager.py`

## Relationships

- [Community 25](Community_25.md) (3 shared connections)
- [Community 175](Community_175.md) (1 shared connections)
- [Community 65](Community_65.md) (1 shared connections)
- [Community 121](Community_121.md) (1 shared connections)
- [Community 62](Community_62.md) (1 shared connections)
- [Community 31](Community_31.md) (1 shared connections)
- [Community 3](Community_3.md) (1 shared connections)

## Source Files

- `app/container.py`
- `app/core/context.py`
- `app/machine/iaicontrol.py`
- `app/services/log/log_manager.py`

## Audit Trail

- EXTRACTED: 14 (67%)
- INFERRED: 7 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*