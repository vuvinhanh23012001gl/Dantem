# Community 122

> 10 nodes

## Key Concepts

- **._save_training_inputs()** (13 connections) — `app/judger/judment.py`
- **.test_solution_2_async_retrain_saver()** (4 connections) — `app/tests/inspection/test_storage_optimization.py`
- **.flush_retrain_queue()** (3 connections) — `app/judger/judment.py`
- **._get_retrain_executor()** (3 connections) — `app/judger/judment.py`
- **.get_output_retrain_dir()** (3 connections) — `app/services/log/config_software.py`
- **Path** (1 connections)
- **ThreadPoolExecutor** (1 connections)
- **Đợi toàn bộ ảnh retrain trong luồng nền được flush xuống đĩa.** (1 connections) — `app/judger/judment.py`
- **Lưu crop ROI hoặc full frame mà inspector thực sự nhận trước inference.** (1 connections) — `app/judger/judment.py`
- **Giải pháp 2: Judment hỗ trợ lưu ảnh retrain ngầm khi async_save=True.** (1 connections) — `app/tests/inspection/test_storage_optimization.py`

## Relationships

- [Community 14](Community_14.md) (7 shared connections)
- [Community 3](Community_3.md) (2 shared connections)
- [Community 18](Community_18.md) (2 shared connections)
- [Community 108](Community_108.md) (1 shared connections)
- [Community 113](Community_113.md) (1 shared connections)

## Source Files

- `app/judger/judment.py`
- `app/services/log/config_software.py`
- `app/tests/inspection/test_storage_optimization.py`

## Audit Trail

- EXTRACTED: 21 (95%)
- INFERRED: 1 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*