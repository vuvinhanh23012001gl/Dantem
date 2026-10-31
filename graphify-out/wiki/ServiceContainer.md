# ServiceContainer

> God node · 76 connections · `app/container.py`

**Community:** [Community 175](Community_175.md)

## Connections by Relation

### calls
- create_container() `EXTRACTED`

### contains
- container.py `EXTRACTED`

### imports
- api_tool_law_regulations.py `EXTRACTED`
- api_captureproduct.py `EXTRACTED`
- stage_2_transform.py `EXTRACTED`
- dependencies.py `EXTRACTED`
- api_product.py `EXTRACTED`
- pipeline.py `EXTRACTED`
- home.py `EXTRACTED`
- stage_1_preprocess.py `EXTRACTED`
- socketio_log.py `EXTRACTED`
- api_draw_regulations.py `EXTRACTED`
- stage_3_export.py `EXTRACTED`

### method
- .__init__() `EXTRACTED`
- .notify_config_changed() `EXTRACTED`
- .stop() `EXTRACTED`
- .is_tcp_connected() `EXTRACTED`
- .send_judgment_log() `EXTRACTED`
- .get_mode() `EXTRACTED`
- .set_mode() `EXTRACTED`

### references
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`

### uses
- [IAIControl](IAIControl.md) `INFERRED`
- [StageTransform](StageTransform.md) `INFERRED`
- RobotConfig `INFERRED`
- StagePreprocess `INFERRED`
- RobotControl `INFERRED`
- RuntimeState `INFERRED`
- Pipeline `INFERRED`
- run_model_color() `INFERRED`
- run_model_ocr() `INFERRED`
- run_model_stamp() `INFERRED`
- run_model_stamp_alignment() `INFERRED`
- StageExport `INFERRED`
- erase_item_img() `INFERRED`
- delete_product() `INFERRED`
- log_sender() `INFERRED`
- capture() `INFERRED`
- erase_frame() `INFERRED`
- add_product() `INFERRED`
- create_anomaly_point_model() `INFERRED`
- delete_foreign_object_model() `INFERRED`
- *…and 32 more `uses` connection(s) not listed (lowest-degree first to go)*

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*