# Community 147

> 9 nodes

## Key Concepts

- **ProductCountService** (10 connections) — `app/services/product_count_service.py`
- **.get_counts()** (2 connections) — `app/services/product_count_service.py`
- **.__init__()** (2 connections) — `app/services/product_count_service.py`
- **.record_result()** (2 connections) — `app/services/product_count_service.py`
- **.reset_counts()** (2 connections) — `app/services/product_count_service.py`
- **Lấy số lượng sản phẩm hiện tại. Returns: Dict[str, int]: Dictionary chứa {"ok":…** (1 connections) — `app/services/product_count_service.py`
- **Ghi nhận kết quả phán định sản phẩm (OK/NG) và cập nhật tổng số. Args: is_ok…** (1 connections) — `app/services/product_count_service.py`
- **Đặt lại toàn bộ số đếm OK = 0, NG = 0, Tổng = 0 khi người dùng bấm nút Đặt lại.…** (1 connections) — `app/services/product_count_service.py`
- **Dịch vụ quản lý số lượng sản phẩm OK, NG và Tổng đếm chạy trong runtime. Đảm…** (1 connections) — `app/services/product_count_service.py`

## Relationships

- [Community 52](Community_52.md) (2 shared connections)
- [Community 87](Community_87.md) (2 shared connections)
- [Community 80](Community_80.md) (1 shared connections)
- [Community 134](Community_134.md) (1 shared connections)

## Source Files

- `app/services/product_count_service.py`

## Audit Trail

- EXTRACTED: 13 (93%)
- INFERRED: 1 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*