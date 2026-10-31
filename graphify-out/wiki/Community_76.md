# Community 76

> 17 nodes

## Key Concepts

- **CameraConfig** (12 connections) — `app/config/camera_config.py`
- **.apply_config_values()** (7 connections) — `app/services/camera/camera_connect.py`
- **.save_config_values()** (7 connections) — `app/services/camera/camera_connect.py`
- **.to_dict()** (5 connections) — `app/config/camera_config.py`
- **.update_operator_values()** (5 connections) — `app/config/camera_config.py`
- **.reload_feature_file()** (5 connections) — `app/services/camera/camera_connect.py`
- **.save_feature_config()** (4 connections) — `app/services/camera/camera_connect.py`
- **.validate()** (3 connections) — `app/config/camera_config.py`
- **Any** (2 connections)
- **Kiểm tra miền giá trị số cơ bản trước khi áp dụng camera. Input: không có.…** (1 connections) — `app/config/camera_config.py`
- **Chuyển cấu hình thành dictionary để trả về API hoặc ghi JSON. Input: không có.…** (1 connections) — `app/config/camera_config.py`
- **Cấu hình runtime ánh xạ trực tiếp vào camera feature file. Input: dictionary…** (1 connections) — `app/config/camera_config.py`
- **Cập nhật field vận hành, không cho operator sửa white balance. Input:…** (1 connections) — `app/config/camera_config.py`
- **Áp dụng tạm thời field vận hành mà chưa lưu file. Input: dictionary field vận…** (1 connections) — `app/services/camera/camera_connect.py`
- **Cập nhật, lưu file và áp dụng cấu hình vận hành. Input: dictionary field vận…** (1 connections) — `app/services/camera/camera_connect.py`
- **Nạp lại features.cfg để khôi phục camera sau thao tác thất bại. Input: không…** (1 connections) — `app/services/camera/camera_connect.py`
- **Ghi trực tiếp nodemap hiện tại vào file features.cfg. Input: không có; sử dụng…** (1 connections) — `app/services/camera/camera_connect.py`

## Relationships

- [Community 121](Community_121.md) (4 shared connections)
- [Community 140](Community_140.md) (3 shared connections)
- [Community 52](Community_52.md) (2 shared connections)
- [Community 125](Community_125.md) (2 shared connections)
- [Community 22](Community_22.md) (1 shared connections)
- [Community 23](Community_23.md) (1 shared connections)
- [Community 45](Community_45.md) (1 shared connections)

## Source Files

- `app/config/camera_config.py`
- `app/services/camera/camera_connect.py`

## Audit Trail

- EXTRACTED: 32 (89%)
- INFERRED: 4 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*