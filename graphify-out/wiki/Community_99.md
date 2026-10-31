# Community 99

> 13 nodes

## Key Concepts

- **TestAntiBlurAPI** (8 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **.setUpClass()** (2 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **.test_calculate_anti_blur_timers()** (2 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **.test_get_anti_blur_config()** (2 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **.test_get_anti_blur_defaults()** (2 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **.test_reload_features_config()** (2 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **.test_save_anti_blur_config()** (2 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **Kiểm tra các endpoints REST API của AntiBlurService.** (1 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **GET /api/anti_blur/config trả về cấu hình hiện tại và tính toán metric.** (1 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **POST /api/anti_blur/config lưu thành công dữ liệu vào storage file.** (1 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **POST /api/anti_blur/calculate tính toán đúng các thông số URD.** (1 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **POST /api/anti_blur/reload_features đọc file features.cfg thành công.** (1 connections) — `app/tests/inspection/test_anti_blur_logic.py`
- **GET /api/anti_blur/defaults trả về danh sách 14 tham số chuẩn an toàn.** (1 connections) — `app/tests/inspection/test_anti_blur_logic.py`

## Relationships

- [Community 52](Community_52.md) (1 shared connections)
- [Community 43](Community_43.md) (1 shared connections)

## Source Files

- `app/tests/inspection/test_anti_blur_logic.py`

## Audit Trail

- EXTRACTED: 13 (93%)
- INFERRED: 1 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*