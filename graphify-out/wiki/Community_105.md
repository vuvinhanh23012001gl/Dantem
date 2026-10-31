# Community 105

> 12 nodes

## Key Concepts

- **.create_account()** (7 connections) — `app/services/barcode_account_service.py`
- **.get_barcode_accounts()** (5 connections) — `app/services/barcode_account_service.py`
- **.validate_account_data()** (4 connections) — `app/services/barcode_account_service.py`
- **.test_delete_account()** (4 connections) — `app/tests/repository/test_barcode_account.py`
- **.delete_account()** (3 connections) — `app/services/barcode_account_service.py`
- **.test_create_and_group_sorting()** (3 connections) — `app/tests/repository/test_barcode_account.py`
- **.test_duplicate_barcode_prevention()** (2 connections) — `app/tests/repository/test_barcode_account.py`
- **Any** (2 connections)
- **Tạo tài khoản mới và lưu vào file storage: - Kiểm tra hợp lệ barcode và dữ liệu…** (1 connections) — `app/services/barcode_account_service.py`
- **Xóa tài khoản theo mã barcode.** (1 connections) — `app/services/barcode_account_service.py`
- **Xác thực dữ liệu form tạo tài khoản Barcode: - Tên người thao tác không được để…** (1 connections) — `app/services/barcode_account_service.py`
- **Lấy danh sách tài khoản barcode: - Chỉ lấy Manager và User, Admin không cần…** (1 connections) — `app/services/barcode_account_service.py`

## Relationships

- [Community 98](Community_98.md) (4 shared connections)
- [Community 169](Community_169.md) (4 shared connections)

## Source Files

- `app/services/barcode_account_service.py`
- `app/tests/repository/test_barcode_account.py`

## Audit Trail

- EXTRACTED: 15 (71%)
- INFERRED: 6 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*