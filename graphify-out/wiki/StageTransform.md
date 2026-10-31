# StageTransform

> God node · 57 connections · `app/stages/stage_2_transform.py`

**Community:** [Community 68](Community_68.md)

## Connections by Relation

### calls
- .__init__() `EXTRACTED`
- .test_disabled_retrain_passes_empty_allowlist() `EXTRACTED`
- .test_dynamic_workers_from_config_software() `EXTRACTED`
- .test_multi_worker_concurrency() `EXTRACTED`
- .test_multi_worker_error_propagation() `EXTRACTED`
- .test_multi_worker_results_ordering_with_varying_latencies() `EXTRACTED`
- .test_backpressure_queue_blocking() `EXTRACTED`
- .test_multi_worker_fewer_items_than_max() `EXTRACTED`
- .test_consumer_exception_handling() `EXTRACTED`
- .test_pipelined_execution_results_and_ordering() `EXTRACTED`
- .test_capture_task_triggers_retrigger_on_blurred_image() `EXTRACTED`
- .test_return_to_first_point_after_judgment() `EXTRACTED`
- .test_solution_1_async_output_saver() `EXTRACTED`

### contains
- stage_2_transform.py `EXTRACTED`

### imports
- test_anti_blur_logic.py `EXTRACTED`
- test_storage_optimization.py `EXTRACTED`
- pipeline.py `EXTRACTED`
- test_stage_2_multi_workers.py `EXTRACTED`
- test_stage_2_pipelined_queue.py `EXTRACTED`
- stage_3_export.py `EXTRACTED`
- test_stage_2_return_to_first_point.py `EXTRACTED`
- stages/__init__.py `EXTRACTED`

### method
- .run() `EXTRACTED`
- ._execute_judgment_task() `EXTRACTED`
- ._capture_point_task() `EXTRACTED`
- ._producer_loop() `EXTRACTED`
- ._consumer_worker() `EXTRACTED`
- ._save_judgment_result() `EXTRACTED`
- ._output_url() `EXTRACTED`
- ._handle_no_data_task() `EXTRACTED`
- ._strip_internal_images() `EXTRACTED`
- ._session_item_dir() `EXTRACTED`
- ._enqueue_task() `EXTRACTED`
- ._process_point() `EXTRACTED`
- ._send_client() `EXTRACTED`
- ._return_iai_to_start() `EXTRACTED`
- ._save_no_data_result() `EXTRACTED`
- ._write_output_disk_sync() `EXTRACTED`
- ._move_with_retry() `EXTRACTED`
- ._save_image() `EXTRACTED`
- ._capture_with_retry() `EXTRACTED`
- ._ensure_running() `EXTRACTED`
- *…and 4 more `method` connection(s) not listed (lowest-degree first to go)*

### uses
- [ServiceContainer](ServiceContainer.md) `INFERRED`
- [Config_SoftWare](Config_SoftWare.md) `INFERRED`
- EnumMode `INFERRED`
- AntiBlurService `INFERRED`
- TestStage2MultiWorkers `INFERRED`
- RuntimePipelineState `INFERRED`
- TestStorageOptimization `INFERRED`
- StageExport `INFERRED`
- TestStage2PipelinedQueue `INFERRED`
- TestStage2AntiBlurIntegration `INFERRED`
- TestStage2ReturnToFirstPoint `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*