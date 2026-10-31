# Community 6

> 31 nodes

## Key Concepts

- **InspectionTaskItem** (13 connections) — `app/stages/stage_2_transform.py`
- **._execute_judgment_task()** (12 connections) — `app/stages/stage_2_transform.py`
- **._capture_point_task()** (11 connections) — `app/stages/stage_2_transform.py`
- **._producer_loop()** (10 connections) — `app/stages/stage_2_transform.py`
- **Any** (10 connections)
- **._consumer_worker()** (9 connections) — `app/stages/stage_2_transform.py`
- **._handle_no_data_task()** (7 connections) — `app/stages/stage_2_transform.py`
- **._enqueue_task()** (6 connections) — `app/stages/stage_2_transform.py`
- **._process_point()** (6 connections) — `app/stages/stage_2_transform.py`
- **._return_iai_to_start()** (5 connections) — `app/stages/stage_2_transform.py`
- **._move_with_retry()** (4 connections) — `app/stages/stage_2_transform.py`
- **Queue** (4 connections)
- **._capture_with_retry()** (3 connections) — `app/stages/stage_2_transform.py`
- **._ensure_running()** (3 connections) — `app/stages/stage_2_transform.py`
- **._requires_calibration()** (3 connections) — `app/stages/stage_2_transform.py`
- **Exception** (3 connections)
- **.face()** (2 connections) — `app/stages/stage_2_transform.py`
- **_format_insp_entry()** (1 connections) — `app/stages/stage_2_transform.py`
- **Gửi lệnh di chuyển với số lần thử cấu hình trong IAIConfig.** (1 connections) — `app/stages/stage_2_transform.py`
- **Chụp ảnh camera với số lần thử cấu hình.** (1 connections) — `app/stages/stage_2_transform.py`
- **Dừng stage nếu người dùng yêu cầu stop hoặc IAI đang ở lỗi.** (1 connections) — `app/stages/stage_2_transform.py`
- **Luồng Producer: Di chuyển IAI và trigger chụp ảnh, đẩy vào hàng đợi.** (1 connections) — `app/stages/stage_2_transform.py`
- **Đóng gói dữ liệu một điểm đo để chuyển từ luồng chụp sang luồng phán định.** (1 connections) — `app/stages/stage_2_transform.py`
- **Đưa task vào queue, hỗ trợ backpressure chặn luồng chụp tạm thời khi queue đầy.** (1 connections) — `app/stages/stage_2_transform.py`
- **Đưa IAI về vị trí item đầu tiên (step 1) hoặc vị trí 0,0,0.** (1 connections) — `app/stages/stage_2_transform.py`
- *... and 6 more nodes in this community*

## Relationships

- [Community 68](Community_68.md) (16 shared connections)
- [Community 91](Community_91.md) (5 shared connections)
- [Community 81](Community_81.md) (4 shared connections)
- [Community 52](Community_52.md) (2 shared connections)
- [Community 23](Community_23.md) (2 shared connections)
- [Community 146](Community_146.md) (1 shared connections)
- [Community 149](Community_149.md) (1 shared connections)
- [Community 45](Community_45.md) (1 shared connections)
- [Community 3](Community_3.md) (1 shared connections)

## Source Files

- `app/stages/stage_2_transform.py`

## Audit Trail

- EXTRACTED: 75 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*