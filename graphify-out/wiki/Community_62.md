# Community 62

> 23 nodes

## Key Concepts

- **RuntimeState** (17 connections) — `app/core/context.py`
- **.get_pipeline_state()** (3 connections) — `app/core/context.py`
- **.set_pipeline_state()** (3 connections) — `app/core/context.py`
- **.clear_stop()** (2 connections) — `app/core/context.py`
- **.get_connections()** (2 connections) — `app/core/context.py`
- **.get_product_result()** (2 connections) — `app/core/context.py`
- **.is_judgment_running()** (2 connections) — `app/core/context.py`
- **.is_stop_requested()** (2 connections) — `app/core/context.py`
- **.set_connections()** (2 connections) — `app/core/context.py`
- **.set_judgment_running()** (2 connections) — `app/core/context.py`
- **.set_product_result()** (2 connections) — `app/core/context.py`
- **.__init__()** (1 connections) — `app/core/context.py`
- **Lưu trạng thái dùng chung giữa pipeline và các service. Input: không có.…** (1 connections) — `app/core/context.py`
- **Cập nhật trạng thái tổng thể của pipeline.** (1 connections) — `app/core/context.py`
- **Đọc trạng thái tổng thể hiện tại của pipeline.** (1 connections) — `app/core/context.py`
- **Cập nhật trạng thái kết nối mạng Ethernet TCP và camera.** (1 connections) — `app/core/context.py`
- **Trả về ``(com_connected, camera_connected)``.** (1 connections) — `app/core/context.py`
- **Cập nhật cờ sản phẩm đang được phán định.** (1 connections) — `app/core/context.py`
- **Đọc cờ sản phẩm đang được phán định.** (1 connections) — `app/core/context.py`
- **Lưu kết quả sản phẩm cuối cùng cho stage export hoặc client.** (1 connections) — `app/core/context.py`
- **Đọc kết quả sản phẩm cuối cùng.** (1 connections) — `app/core/context.py`
- **Xóa yêu cầu dừng để chuẩn bị một chu kỳ mới.** (1 connections) — `app/core/context.py`
- **Kiểm tra yêu cầu dừng hiện tại.** (1 connections) — `app/core/context.py`

## Relationships

- [Community 68](Community_68.md) (3 shared connections)
- [Community 80](Community_80.md) (1 shared connections)
- [Community 134](Community_134.md) (1 shared connections)
- [Community 100](Community_100.md) (1 shared connections)
- [Community 175](Community_175.md) (1 shared connections)

## Source Files

- `app/core/context.py`

## Audit Trail

- EXTRACTED: 28 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*