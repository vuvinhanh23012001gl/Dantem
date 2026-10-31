# Community 90

> 15 nodes

## Key Concepts

- **Pipeline** (14 connections) — `app/pipeline.py`
- **._run_pipeline()** (7 connections) — `app/pipeline.py`
- **.__init__()** (6 connections) — `app/pipeline.py`
- **._publish_log()** (6 connections) — `app/pipeline.py`
- **._read_runtime_status()** (5 connections) — `app/pipeline.py`
- **._start_cycle_after_reset()** (4 connections) — `app/pipeline.py`
- **.run()** (4 connections) — `app/stages/stage_3_export.py`
- **._watch_reset_button()** (3 connections) — `app/pipeline.py`
- **.open_task_pipeline()** (2 connections) — `app/pipeline.py`
- **.stop_task_pipeline()** (1 connections) — `app/pipeline.py`
- **Chuyển sang Stage 1 sau tín hiệu Reset của IAI.** (1 connections) — `app/pipeline.py`
- **Theo dõi cạnh nhấn Reset và khóa Reset trong lúc phán định.** (1 connections) — `app/pipeline.py`
- **Gửi log pipeline vào ô ``log_judment`` qua queue hiện có.** (1 connections) — `app/pipeline.py`
- **Đọc trạng thái phần cứng và trạng thái IAI/Robot, không điều khiển phần cứng.** (1 connections) — `app/pipeline.py`
- **Tổng hợp kết quả sản phẩm, lưu file và chờ chu kỳ Reset tiếp theo. Input: kết…** (1 connections) — `app/stages/stage_3_export.py`

## Relationships

- [Community 68](Community_68.md) (6 shared connections)
- [Community 134](Community_134.md) (2 shared connections)
- [Community 175](Community_175.md) (2 shared connections)
- [Community 12](Community_12.md) (2 shared connections)
- [Community 167](Community_167.md) (1 shared connections)
- [Community 81](Community_81.md) (1 shared connections)
- [Community 149](Community_149.md) (1 shared connections)

## Source Files

- `app/pipeline.py`
- `app/stages/stage_3_export.py`

## Audit Trail

- EXTRACTED: 28 (78%)
- INFERRED: 8 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*