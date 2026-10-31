# Community 113

> 20 nodes

## Key Concepts

- **Log_Img** (17 connections) — `app/services/log/log_img.py`
- **TestStorageOptimization** (11 connections) — `app/tests/inspection/test_storage_optimization.py`
- **.save()** (7 connections) — `app/services/log/log_img.py`
- **.test_solution_3_fallback_to_imwrite_when_source_missing()** (4 connections) — `app/tests/inspection/test_storage_optimization.py`
- **.test_solution_3_fast_jpeg_copy_when_source_exists()** (4 connections) — `app/tests/inspection/test_storage_optimization.py`
- **.test_log_img_ok_ng_prefix()** (4 connections) — `app/tests/services/test_log_system.py`
- **.__init__()** (2 connections) — `app/services/log/log_img.py`
- **.set_save_mode()** (2 connections) — `app/services/log/log_img.py`
- **Path** (2 connections)
- **.set_enable()** (1 connections) — `app/services/log/log_img.py`
- **.setUp()** (1 connections) — `app/tests/inspection/test_storage_optimization.py`
- **.tearDown()** (1 connections) — `app/tests/inspection/test_storage_optimization.py`
- **Any** (1 connections)
- **Quản lý lưu trữ hình ảnh kiểm tra và phán định. Hỗ trợ các chế độ lưu: - ALL:…** (1 connections) — `app/services/log/log_img.py`
- **Cập nhật chế độ lưu ảnh: ALL, NG_ONLY, OFF.** (1 connections) — `app/services/log/log_img.py`
- **Lưu hình ảnh phán định xuống đĩa cứng theo chính sách cấu hình. Args: img: Ma…** (1 connections) — `app/services/log/log_img.py`
- **Kiểm tra toàn diện 3 giải pháp tối ưu hóa Disk I/O: 1. Async Output Saver…** (1 connections) — `app/tests/inspection/test_storage_optimization.py`
- **Giải pháp 3: Khi có source_file hợp lệ, Log_Img copy trực tiếp thay vì encode…** (1 connections) — `app/tests/inspection/test_storage_optimization.py`
- **Giải pháp 3 fallback: Khi không có source_file hoặc file không tồn tại, Log_Img…** (1 connections) — `app/tests/inspection/test_storage_optimization.py`
- **Kiểm tra tên file ảnh có tiền tố OK_ hoặc NG_ và được lưu vào thư mục Log_img.** (1 connections) — `app/tests/services/test_log_system.py`

## Relationships

- [Community 52](Community_52.md) (6 shared connections)
- [Community 31](Community_31.md) (2 shared connections)
- [Community 143](Community_143.md) (2 shared connections)
- [Community 122](Community_122.md) (1 shared connections)
- [Community 91](Community_91.md) (1 shared connections)
- [Community 14](Community_14.md) (1 shared connections)
- [Community 68](Community_68.md) (1 shared connections)

## Source Files

- `app/services/log/log_img.py`
- `app/tests/inspection/test_storage_optimization.py`
- `app/tests/services/test_log_system.py`

## Audit Trail

- EXTRACTED: 31 (79%)
- INFERRED: 8 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*