# Community 104

> 15 nodes

## Key Concepts

- **._handle_single_input_message()** (12 connections) — `app/machine/iaicontrol.py`
- **.fuc_update_input_queue_request_arm()** (4 connections) — `app/machine/iaicontrol.py`
- **.update_status_from_string()** (4 connections) — `app/machine/iaicontrol.py`
- **.update_var_input()** (4 connections) — `app/machine/iaicontrol.py`
- **.get_is_origin()** (3 connections) — `app/machine/iaicontrol.py`
- **.get_status()** (3 connections) — `app/machine/iaicontrol.py`
- **._parse_input_value()** (3 connections) — `app/machine/iaicontrol.py`
- **.set_is_origin()** (3 connections) — `app/machine/iaicontrol.py`
- **.set_status()** (3 connections) — `app/machine/iaicontrol.py`
- **._input_thread()** (2 connections) — `app/machine/iaicontrol.py`
- **Cập nhật biến input với lock, thread-safe** (1 connections) — `app/machine/iaicontrol.py`
- **Cập nhật trạng thái tất cả các biến từ chuỗi STM32, thread-safe data: chuỗi…** (1 connections) — `app/machine/iaicontrol.py`
- **Cập nhật trạng thái nút và cảm biến từ RX queue của ManagerSerial. Xả toàn bộ…** (1 connections) — `app/machine/iaicontrol.py`
- **Xử lý chi tiết từng bản tin input nhận từ STM32.** (1 connections) — `app/machine/iaicontrol.py`
- **Đọc giá trị số của một bản tin input STM32. Input: chuỗi dạng ``btn_start:1``…** (1 connections) — `app/machine/iaicontrol.py`

## Relationships

- [Community 25](Community_25.md) (14 shared connections)
- [Community 110](Community_110.md) (1 shared connections)
- [Community 136](Community_136.md) (1 shared connections)

## Source Files

- `app/machine/iaicontrol.py`

## Audit Trail

- EXTRACTED: 31 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*