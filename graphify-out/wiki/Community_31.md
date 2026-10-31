# Community 31

> 18 nodes

## Key Concepts

- **Manager_Log** (22 connections) — `app/services/log/log_manager.py`
- **.Init()** (9 connections) — `app/services/log/log_manager.py`
- **.get_current_product_name()** (6 connections) — `app/services/log/log_manager.py`
- **.__init__()** (6 connections) — `app/services/log/log_manager.py`
- **._log_thread_loop()** (5 connections) — `app/services/log/log_manager.py`
- **._fetch_queue_item()** (4 connections) — `app/services/log/log_manager.py`
- **.calculate_pass_rate()** (3 connections) — `app/services/log/log_manager.py`
- **.start_thread()** (3 connections) — `app/services/log/log_manager.py`
- **.normalize_folder_name()** (3 connections) — `app/utils/aggregate_function.py`
- **Any** (2 connections)
- **Bắt đầu luồng ghi log nền.** (1 connections) — `app/services/log/log_manager.py`
- **Đọc an toàn từ queue_manager_log (hỗ trợ cả Worker và Queue chuẩn).** (1 connections) — `app/services/log/log_manager.py`
- **Vòng lặp tiêu thụ dữ liệu từ queue_manager_log mà không chiếm dụng CPU.** (1 connections) — `app/services/log/log_manager.py`
- **Quản trị viên logging trung tâm cho ứng dụng. Điều phối toàn bộ việc ghi log…** (1 connections) — `app/services/log/log_manager.py`
- **Lấy tên chuẩn hóa của sản phẩm đang chọn.** (1 connections) — `app/services/log/log_manager.py`
- **Tính tỷ lệ phán định % từ product_count_service (OK / Total * 100).** (1 connections) — `app/services/log/log_manager.py`
- **Khởi tạo và cấu hình các thành phần ghi log.** (1 connections) — `app/services/log/log_manager.py`
- **Chuyển tiếng Việt sang không dấu, thay khoảng trắng bằng '_', chỉ giữ…** (1 connections) — `app/utils/aggregate_function.py`

## Relationships

- [Community 52](Community_52.md) (6 shared connections)
- [Community 3](Community_3.md) (3 shared connections)
- [Community 77](Community_77.md) (2 shared connections)
- [Community 113](Community_113.md) (2 shared connections)
- [Community 70](Community_70.md) (2 shared connections)
- [Community 142](Community_142.md) (2 shared connections)
- [Community 80](Community_80.md) (1 shared connections)
- [Community 134](Community_134.md) (1 shared connections)
- [Community 100](Community_100.md) (1 shared connections)
- [Community 143](Community_143.md) (1 shared connections)
- [Community 154](Community_154.md) (1 shared connections)
- [Community 75](Community_75.md) (1 shared connections)

## Source Files

- `app/services/log/log_manager.py`
- `app/utils/aggregate_function.py`

## Audit Trail

- EXTRACTED: 40 (85%)
- INFERRED: 7 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*