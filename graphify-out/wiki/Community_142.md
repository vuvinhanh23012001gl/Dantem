# Community 142

> 14 nodes

## Key Concepts

- **LogCleanupWorker** (14 connections) — `app/services/log/log_cleanup.py`
- **.cleanup_now()** (5 connections) — `app/services/log/log_cleanup.py`
- **.cleanup_folder()** (3 connections) — `app/services/log/log_cleanup.py`
- **._worker_loop()** (3 connections) — `app/services/log/log_cleanup.py`
- **Path** (3 connections)
- **.__init__()** (2 connections) — `app/services/log/log_cleanup.py`
- **.start()** (2 connections) — `app/services/log/log_cleanup.py`
- **.stop()** (2 connections) — `app/services/log/log_cleanup.py`
- **Worker chạy nền định kỳ quét và dọn dẹp các tệp log/ảnh cũ hơn số ngày cấu…** (1 connections) — `app/services/log/log_cleanup.py`
- **Bắt đầu luồng kiểm tra định kỳ.** (1 connections) — `app/services/log/log_cleanup.py`
- **Dừng luồng dọn dẹp an toàn.** (1 connections) — `app/services/log/log_cleanup.py`
- **Vòng lặp chạy nền định kỳ quét thư mục.** (1 connections) — `app/services/log/log_cleanup.py`
- **Phương thức tiện ích gọi trực tiếp để dọn dẹp một thư mục log.** (1 connections) — `app/services/log/log_cleanup.py`
- **Thực hiện quét và dọn dẹp ngay lập tức: Xóa nguyên toàn bộ thư mục theo ngày…** (1 connections) — `app/services/log/log_cleanup.py`

## Relationships

- [Community 52](Community_52.md) (4 shared connections)
- [Community 31](Community_31.md) (2 shared connections)
- [Community 143](Community_143.md) (2 shared connections)

## Source Files

- `app/services/log/log_cleanup.py`

## Audit Trail

- EXTRACTED: 22 (92%)
- INFERRED: 2 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*