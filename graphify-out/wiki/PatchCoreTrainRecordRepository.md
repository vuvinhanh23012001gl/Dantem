# PatchCoreTrainRecordRepository

> God node · 62 connections · `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`

**Community:** [Community 21](Community_21.md)

## Connections by Relation

### calls
- .delete_capture_item() `EXTRACTED`
- test_trainler_patchcore_runtime_with_workspace_images() `EXTRACTED`
- test_run_patchcore_inference_from_latest_record() `EXTRACTED`
- ._rollback() `EXTRACTED`
- test_trainler_patchcore_logic() `EXTRACTED`
- ._cleanup_orphaned_patchcore_rois() `EXTRACTED`
- test_patchcore_train_record_service_logic() `EXTRACTED`
- test_run_patchcore_train_record_service() `EXTRACTED`
- ._cleanup_patchcore_product() `EXTRACTED`
- ._delete_patchcore_manifest_records() `EXTRACTED`
- ._has_patchcore_records() `EXTRACTED`
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`
- .setUp() `EXTRACTED`
- .setUp() `EXTRACTED`

### contains
- patchcore_train_record_repository.py `EXTRACTED`

### imports
- trainler.py `EXTRACTED`
- test_foreign_object_multi_roi.py `EXTRACTED`
- patchcore_inspection_service.py `EXTRACTED`
- foreign_object_patch_core_service.py `EXTRACTED`
- anomaly_point_patch_core_service.py `EXTRACTED`
- capture_item_delete_service.py `EXTRACTED`
- product_service.py `EXTRACTED`
- judment_law_product_service.py `EXTRACTED`
- test_trainler_patchcore.py `EXTRACTED`
- test_run_patchcore_inference.py `EXTRACTED`
- test_anomaly_point_roi_isolation.py `EXTRACTED`
- test_logic_trainler_patchcore.py `EXTRACTED`
- patchcore_train_model/__init__.py `EXTRACTED`
- test_run_patchcore_train_record_service.py `EXTRACTED`
- test_logic_patchcore_train_record_service.py `EXTRACTED`
- patchcore_train_record_service.py `EXTRACTED`

### method
- .save_record() `EXTRACTED`
- .load_manifest() `EXTRACTED`
- .save_manifest() `EXTRACTED`
- ._normalize_runtime_value() `EXTRACTED`
- ._session_parent() `EXTRACTED`
- .delete_records_under_dir() `EXTRACTED`
- .delete_records_by_product_id() `EXTRACTED`
- ._same_session_parent() `EXTRACTED`
- .get_latest_run() `EXTRACTED`
- .delete_records_by_model_root() `EXTRACTED`
- .is_record_belonging_to_product() `EXTRACTED`
- ._manifest_path_value() `EXTRACTED`
- ._compact_metadata() `EXTRACTED`
- ._resolve_manifest_path() `EXTRACTED`
- .config_to_dict() `EXTRACTED`
- .has_records_for_product() `EXTRACTED`
- ._has_same_roi() `EXTRACTED`
- .__init__() `EXTRACTED`

### rationale_for
- Quản lý lịch sử train mô hình PatchCore theo từng phiên. Mỗi phiên train được… `EXTRACTED`

### references
- .__init__() `EXTRACTED`
- .__init__() `EXTRACTED`

### uses
- JudmentLawProductSevice `INFERRED`
- TrainlerPatchCore `INFERRED`
- ProductService `INFERRED`
- ForeignObjectPatchCoreService `INFERRED`
- PatchCoreInspectionService `INFERRED`
- ModelStorageTests `INFERRED`
- CaptureItemDeleteService `INFERRED`
- AnomalyPointPatchCoreService `INFERRED`
- TestAnomalyPointRoiIsolation `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*