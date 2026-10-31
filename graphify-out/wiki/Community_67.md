# Community 67

> 17 nodes

## Key Concepts

- **.load_manifest()** (12 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **._cleanup_orphaned_patchcore_rois()** (8 connections) — `app/services/judment_law_product_service.py`
- **.delete_records_by_product_id()** (6 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **.delete_records_under_dir()** (6 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **._compact_metadata()** (5 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **.delete_records_by_model_root()** (5 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **.is_record_belonging_to_product()** (5 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **.has_records_for_product()** (4 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **Path** (1 connections)
- **Xóa các record trỏ đúng tới một thư mục session PatchCore. Args: model_root:…** (1 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **Xóa toàn bộ các record có model_root nằm trong hoặc trùng với target_dir.** (1 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **Kiểm tra một record trong manifest có thuộc về product_id hay không. Tránh xóa…** (1 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **Kiểm tra manifest có chứa record thuộc về product_id hay không. Args:…** (1 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **Xóa toàn bộ các record thuộc về một product_id cụ thể trong manifest. Đảm bảo…** (1 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **Loại bỏ các khóa legacy hoặc trùng lặp khỏi một record.** (1 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **Đọc danh sách record từ file manifest trung tâm. Returns: list[dict]: Các…** (1 connections) — `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- **Chỉ dọn session đúng loại, không xóa cả thư mục ROI dùng chung.** (1 connections) — `app/services/judment_law_product_service.py`

## Relationships

- [Community 21](Community_21.md) (10 shared connections)
- [Community 5](Community_5.md) (5 shared connections)
- [Community 45](Community_45.md) (5 shared connections)
- [Community 17](Community_17.md) (2 shared connections)
- [Community 66](Community_66.md) (2 shared connections)

## Source Files

- `app/engines/train/patchcore_train_model/patchcore_train_record_repository.py`
- `app/services/judment_law_product_service.py`

## Audit Trail

- EXTRACTED: 37 (88%)
- INFERRED: 5 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*