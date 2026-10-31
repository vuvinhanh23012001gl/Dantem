# Community 70

> 22 nodes

## Key Concepts

- **Log_CSV** (20 connections) — `app/services/log/log_csv.py`
- **.write_session_item()** (11 connections) — `app/services/log/log_csv.py`
- **.write()** (7 connections) — `app/services/log/log_csv.py`
- **.write_summary()** (7 connections) — `app/services/log/log_csv.py`
- **._ensure_file_initialized()** (6 connections) — `app/services/log/log_csv.py`
- **Path** (6 connections)
- **.test_log_csv_session_detail_format()** (4 connections) — `app/tests/services/test_log_system.py`
- **.test_log_csv_summary_daily_format()** (4 connections) — `app/tests/services/test_log_system.py`
- **.test_session_uncalled_inspectors_na_values()** (4 connections) — `app/tests/services/test_log_system.py`
- **._compatible_session_path()** (3 connections) — `app/services/log/log_csv.py`
- **.test_csv_new_schema_does_not_modify_legacy_csv()** (3 connections) — `app/tests/inspection/test_retired_inspectors.py`
- **Any** (3 connections)
- **.__init__()** (2 connections) — `app/services/log/log_csv.py`
- **_resolve_category()** (1 connections) — `app/services/log/log_csv.py`
- **Đảm bảo thư mục và tiêu đề header BOM UTF-8-SIG của file CSV tồn tại.** (1 connections) — `app/services/log/log_csv.py`
- **Ghi 1 dòng tổng kết phiên phán định vào file CSV tổng nội dung (Ảnh 1). Cột:…** (1 connections) — `app/services/log/log_csv.py`
- **Ghi chi tiết 1 item/point vào file CSV session theo từng hạng mục (Ảnh 2).** (1 connections) — `app/services/log/log_csv.py`
- **Phương thức ghi dữ liệu tương thích ngược: - Nếu data có 'Session' và 'Tỷ lệ…** (1 connections) — `app/services/log/log_csv.py`
- **Quản lý ghi log kết quả phán định ra file CSV chuẩn công nghiệp: 1. File CSV…** (1 connections) — `app/services/log/log_csv.py`
- **Kiểm tra ghi file CSV tổng summary_daily.csv đúng theo chuẩn Ảnh 1.** (1 connections) — `app/tests/services/test_log_system.py`
- **Kiểm tra schema mới không còn cột Bọt khí và giữ đủ dữ liệu Tem.** (1 connections) — `app/tests/services/test_log_system.py`
- **Kiểm tra khi chỉ cấu hình Tem, các hạng mục không được gọi xuất NA.** (1 connections) — `app/tests/services/test_log_system.py`

## Relationships

- [Community 52](Community_52.md) (5 shared connections)
- [Community 143](Community_143.md) (4 shared connections)
- [Community 31](Community_31.md) (2 shared connections)
- [Community 26](Community_26.md) (2 shared connections)

## Source Files

- `app/services/log/log_csv.py`
- `app/tests/inspection/test_retired_inspectors.py`
- `app/tests/services/test_log_system.py`

## Audit Trail

- EXTRACTED: 44 (86%)
- INFERRED: 7 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*