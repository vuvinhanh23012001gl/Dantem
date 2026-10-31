# Community 110

> 11 nodes

## Key Concepts

- **.send_command_stm32()** (8 connections) — `app/machine/iaicontrol.py`
- **._handler_request_stm32()** (7 connections) — `app/machine/iaicontrol.py`
- **.fuc_update_output_queue_request_arm()** (4 connections) — `app/machine/iaicontrol.py`
- **.press_start_stop_processing_complete()** (4 connections) — `app/machine/iaicontrol.py`
- **.show_states()** (4 connections) — `app/machine/iaicontrol.py`
- **.start_input_thread()** (2 connections) — `app/machine/iaicontrol.py`
- **show trạng thái hiện tại của của các Input Output** (1 connections) — `app/machine/iaicontrol.py`
- **Luồng này đọc trạng thái từ các nút nhấn.Xủ lý Input và cập nhật trạng thái gửi…** (1 connections) — `app/machine/iaicontrol.py`
- **Gửi lệnh qua ManagerSerial được truyền từ bên ngoài. Input: ``data`` là chuỗi…** (1 connections) — `app/machine/iaicontrol.py`
- **Gửi lệnh xuống STM32 khi trạng thái output thay đổi** (1 connections) — `app/machine/iaicontrol.py`
- **Hàm này xử lý khi người dùng nhấn nút nhấn về gốc** (1 connections) — `app/machine/iaicontrol.py`

## Relationships

- [Community 25](Community_25.md) (9 shared connections)
- [Community 103](Community_103.md) (2 shared connections)
- [Community 104](Community_104.md) (1 shared connections)

## Source Files

- `app/machine/iaicontrol.py`

## Audit Trail

- EXTRACTED: 23 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*