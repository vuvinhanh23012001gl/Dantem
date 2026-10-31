# Community 30

> 15 nodes

## Key Concepts

- **TestAnomalyPointRoiIsolation** (11 connections) — `app/tests/engines/service/test_anomaly_point_roi_isolation.py`
- **.delete_model()** (6 connections) — `app/engines/service/anomaly_point_patch_core_service.py`
- **.create_model()** (4 connections) — `app/engines/service/anomaly_point_patch_core_service.py`
- **.invalidate_cache()** (4 connections) — `app/engines/service/anomaly_point_patch_core_service.py`
- **._add_roi()** (4 connections) — `app/tests/engines/service/test_anomaly_point_roi_isolation.py`
- **_make_model()** (3 connections) — `app/tests/engines/service/test_anomaly_point_roi_isolation.py`
- **.test_delete_model_roi0_keeps_roi1()** (3 connections) — `app/tests/engines/service/test_anomaly_point_roi_isolation.py`
- **.test_delete_model_without_model_fails_cleanly()** (2 connections) — `app/tests/engines/service/test_anomaly_point_roi_isolation.py`
- **.test_get_patchcore_frame_missing_model_raises()** (2 connections) — `app/tests/engines/service/test_anomaly_point_roi_isolation.py`
- **.test_models_are_isolated_per_roi()** (2 connections) — `app/tests/engines/service/test_anomaly_point_roi_isolation.py`
- **.test_resolve_model_root_per_roi_and_legacy()** (1 connections) — `app/tests/engines/service/test_anomaly_point_roi_isolation.py`
- **Path** (1 connections)
- **Xóa cache model trong RAM cho 1 khung roi_id cụ thể hoặc toàn bộ item.** (1 connections) — `app/engines/service/anomaly_point_patch_core_service.py`
- **Tạo model PatchCore cho đúng khung roi_id trên item.** (1 connections) — `app/engines/service/anomaly_point_patch_core_service.py`
- **Xóa model PatchCore và dọn cache RAM của riêng khung roi_id.** (1 connections) — `app/engines/service/anomaly_point_patch_core_service.py`

## Relationships

- [Community 21](Community_21.md) (8 shared connections)
- [Community 9](Community_9.md) (3 shared connections)
- [Community 128](Community_128.md) (1 shared connections)

## Source Files

- `app/engines/service/anomaly_point_patch_core_service.py`
- `app/tests/engines/service/test_anomaly_point_roi_isolation.py`

## Audit Trail

- EXTRACTED: 23 (79%)
- INFERRED: 6 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*