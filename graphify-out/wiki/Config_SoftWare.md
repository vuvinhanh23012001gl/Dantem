# Config_SoftWare

> God node · 73 connections · `app/services/log/config_software.py`

**Community:** [Community 3](Community_3.md)

## Connections by Relation

### calls
- .__init__() `EXTRACTED`
- ._save_training_inputs() `EXTRACTED`
- ._execute_judgment_task() `EXTRACTED`
- .test_config_software_log_dir_and_retrain_inspectors() `EXTRACTED`
- .test_manager_log_pipeline_integration() `EXTRACTED`
- .test_config_software_max_workers_validation() `EXTRACTED`
- .test_legacy_retrain_setting_migrates_to_anomaly_point() `EXTRACTED`
- .test_new_log_folder_structure() `EXTRACTED`
- .test_new_retrain_setting_takes_precedence_over_legacy_setting() `EXTRACTED`

### contains
- config_software.py `EXTRACTED`

### imports
- stage_2_transform.py `EXTRACTED`
- judment.py `EXTRACTED`
- log_manager.py `EXTRACTED`
- test_log_system.py `EXTRACTED`
- test_storage_optimization.py `EXTRACTED`
- api_config_software.py `EXTRACTED`
- log/__init__.py `EXTRACTED`
- test_stage_2_multi_workers.py `EXTRACTED`

### method
- .create_path_by_name_product() `EXTRACTED`
- .get_base_log_dir() `EXTRACTED`
- .get_default_config() `EXTRACTED`
- .to_dict() `EXTRACTED`
- .get_enabled_retrain_inspectors() `EXTRACTED`
- .get_output_retrain_dir() `EXTRACTED`
- .set_log_dir() `EXTRACTED`
- .get_retrain_inspectors() `EXTRACTED`
- .save_config_software() `EXTRACTED`
- .get_arr_disk_on_pc() `EXTRACTED`
- .__init__() `EXTRACTED`
- .set_output_dir() `EXTRACTED`
- .get_output_judgment_dir() `EXTRACTED`
- .get_output_patch_core_dir() `EXTRACTED`
- .get_max_judger_workers() `EXTRACTED`
- .set_max_judger_workers() `EXTRACTED`
- .get_time_save_log() `EXTRACTED`
- .set_time_save_log() `EXTRACTED`
- .set_open_retrain() `EXTRACTED`
- .set_retrain_inspectors() `EXTRACTED`
- *…and 24 more `method` connection(s) not listed (lowest-degree first to go)*

### rationale_for
- Quản lý cấu hình phần mềm & đường dẫn log `EXTRACTED`

### references
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`

### uses
- [StageTransform](StageTransform.md) `INFERRED`
- Judment `INFERRED`
- Manager_Log `INFERRED`
- TestLogSystem `INFERRED`
- TestStage2MultiWorkers `INFERRED`
- get_config_logs_defaults() `INFERRED`
- get_config_logs() `INFERRED`
- update_config_logs() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*