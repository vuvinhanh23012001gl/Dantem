# Community 81

> 23 nodes

## Key Concepts

- **.run()** (15 connections) — `app/stages/stage_2_transform.py`
- **TestStage2MultiWorkers** (14 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **._create_dummy_product()** (8 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **.test_disabled_retrain_passes_empty_allowlist()** (6 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **.test_dynamic_workers_from_config_software()** (6 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **.test_multi_worker_concurrency()** (6 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **.test_multi_worker_error_propagation()** (6 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **.test_multi_worker_results_ordering_with_varying_latencies()** (6 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **.test_multi_worker_fewer_items_than_max()** (5 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **DummyPreparedProduct** (2 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **.setUp()** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **capture_thread_name()** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **slow_concurrent_summary()** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **failing_summary()** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **mock_varying_summary()** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **Di chuyển, chụp ảnh và phán định toàn bộ point của sản phẩm theo mô hình…** (1 connections) — `app/stages/stage_2_transform.py`
- **Kiểm tra khi các worker hoàn tất lộn xộn thời gian, kết quả tổng hợp vẫn đúng…** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **Kiểm tra khi 1 worker gặp lỗi exception, toàn bộ pool được dọn dẹp và lỗi được…** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **Kiểm tra khi sản phẩm chỉ có 2 item nhưng max_judger_workers=5, chỉ khởi tạo…** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **Kiểm tra khi Config_SoftWare cấu hình max_judger_workers=8, Stage 2 áp dụng số…** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **Kiểm tra chuyên sâu kiến trúc Multi-Worker Pool của Stage 2 (tối đa 5 worker…** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **Khi retrain tắt, Stage 2 phải chặn lưu ảnh đầu vào retrain.** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`
- **Kiểm tra tối đa 5 worker cùng chạy phán định AI song song.** (1 connections) — `app/tests/inspection/test_stage_2_multi_workers.py`

## Relationships

- [Community 68](Community_68.md) (11 shared connections)
- [Community 6](Community_6.md) (4 shared connections)
- [Community 120](Community_120.md) (3 shared connections)
- [Community 3](Community_3.md) (2 shared connections)
- [Community 149](Community_149.md) (1 shared connections)
- [Community 45](Community_45.md) (1 shared connections)
- [Community 90](Community_90.md) (1 shared connections)

## Source Files

- `app/stages/stage_2_transform.py`
- `app/tests/inspection/test_stage_2_multi_workers.py`

## Audit Trail

- EXTRACTED: 36 (65%)
- INFERRED: 19 (35%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*