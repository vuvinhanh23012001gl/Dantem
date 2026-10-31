# Community 91

> 15 nodes

## Key Concepts

- **._save_judgment_result()** (8 connections) — `app/stages/stage_2_transform.py`
- **._output_url()** (7 connections) — `app/stages/stage_2_transform.py`
- **._session_item_dir()** (7 connections) — `app/stages/stage_2_transform.py`
- **._save_no_data_result()** (5 connections) — `app/stages/stage_2_transform.py`
- **._save_image()** (4 connections) — `app/stages/stage_2_transform.py`
- **._write_output_disk_sync()** (4 connections) — `app/stages/stage_2_transform.py`
- **.test_solution_1_async_output_saver()** (4 connections) — `app/tests/inspection/test_storage_optimization.py`
- **Path** (2 connections)
- **Ghi kết quả ra đĩa đồng bộ (dùng làm fallback).** (1 connections) — `app/stages/stage_2_transform.py`
- **Đổi đường dẫn app/output thành URL static cho client.** (1 connections) — `app/stages/stage_2_transform.py`
- **Lưu ảnh point vào app/output và trả về đường dẫn tương đối.** (1 connections) — `app/stages/stage_2_transform.py`
- **Tạo thư mục lưu dữ liệu của một item trong một session.** (1 connections) — `app/stages/stage_2_transform.py`
- **Lưu ảnh tham chiếu và result NO_DATA cho item chưa đủ dữ liệu chạy. Input: Dữ…** (1 connections) — `app/stages/stage_2_transform.py`
- **Lưu ảnh gốc, ảnh judgment và JSON kết quả của item (hỗ trợ cả bất đồng bộ và…** (1 connections) — `app/stages/stage_2_transform.py`
- **Giải pháp 1: StageTransform lưu file output trên luồng nền mà không block…** (1 connections) — `app/tests/inspection/test_storage_optimization.py`

## Relationships

- [Community 68](Community_68.md) (7 shared connections)
- [Community 6](Community_6.md) (5 shared connections)
- [Community 149](Community_149.md) (1 shared connections)
- [Community 113](Community_113.md) (1 shared connections)

## Source Files

- `app/stages/stage_2_transform.py`
- `app/tests/inspection/test_storage_optimization.py`

## Audit Trail

- EXTRACTED: 30 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*