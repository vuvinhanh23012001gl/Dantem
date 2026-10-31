# Community 103

> 12 nodes

## Key Concepts

- **.move_to_point()** (6 connections) — `app/machine/iaicontrol.py`
- **.wait_for_specific_data()** (6 connections) — `app/machine/iaicontrol.py`
- **.move_to_origin()** (5 connections) — `app/machine/iaicontrol.py`
- **.clear_command_rx_queue()** (4 connections) — `app/machine/iaicontrol.py`
- **.can_move_iai()** (3 connections) — `app/machine/iaicontrol.py`
- **._matches_expected_signal()** (3 connections) — `app/machine/iaicontrol.py`
- **Kiểm tra trạng thái di chuyển (độc lập, không phụ thuộc cổng COM).** (1 connections) — `app/machine/iaicontrol.py`
- **Xả sạch toàn bộ bản tin tồn đọng trong command_rx_queue trước khi gửi lệnh mới.** (1 connections) — `app/machine/iaicontrol.py`
- **Gửi tọa độ đến bộ điều khiển di chuyển.** (1 connections) — `app/machine/iaicontrol.py`
- **Gửi lệnh đưa ARM về gốc và chờ xác nhận. Input: ``timeout`` là thời gian chờ…** (1 connections) — `app/machine/iaicontrol.py`
- **Chờ tín hiệu cụ thể từ queue_check_in_1. - expected_signal: tín hiệu mong đợi…** (1 connections) — `app/machine/iaicontrol.py`
- **So khớp phản hồi ARM, kể cả dạng tọa độ có padding và hậu tố ``ok``. Input:…** (1 connections) — `app/machine/iaicontrol.py`

## Relationships

- [Community 25](Community_25.md) (7 shared connections)
- [Community 110](Community_110.md) (2 shared connections)

## Source Files

- `app/machine/iaicontrol.py`

## Audit Trail

- EXTRACTED: 21 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*