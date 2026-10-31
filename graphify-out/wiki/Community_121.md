# Community 121

> 22 nodes

## Key Concepts

- **Camera** (41 connections) — `app/services/camera/camera_connect.py`
- **.capture_image_trigger()** (5 connections) — `app/services/camera/camera_connect.py`
- **._cleanup_camera_resources()** (5 connections) — `app/services/camera/camera_connect.py`
- **.set_enumeration()** (5 connections) — `app/services/camera/camera_connect.py`
- **.disable_software_trigger()** (4 connections) — `app/services/camera/camera_connect.py`
- **.release()** (4 connections) — `app/services/camera/camera_connect.py`
- **.capture_image_path()** (3 connections) — `app/services/camera/camera_connect.py`
- **.capture_once()** (3 connections) — `app/services/camera/camera_connect.py`
- **.enable_software_trigger()** (3 connections) — `app/services/camera/camera_connect.py`
- **.print_device_info()** (3 connections) — `app/services/camera/camera_connect.py`
- **.send_trigger()** (3 connections) — `app/services/camera/camera_connect.py`
- **.display_captured_image()** (2 connections) — `app/services/camera/camera_connect.py`
- **.get_config()** (2 connections) — `app/services/camera/camera_connect.py`
- **.image()** (1 connections) — `app/services/camera/camera_connect.py`
- **.get_device_info_dict()** (1 connections) — `app/services/camera/camera_connect.py`
- **Lấy cấu hình camera hiện tại. Input: không có. Output: dictionary JSON-…** (1 connections) — `app/services/camera/camera_connect.py`
- **Hiển thị ảnh sau khi chụp bằng OpenCV. :param img: Khung hình (numpy array) cần…** (1 connections) — `app/services/camera/camera_connect.py`
- **Dọn dẹp tài nguyên phần cứng camera phục vụ cho reconnect hoặc shutdown.** (1 connections) — `app/services/camera/camera_connect.py`
- **Giải phóng camera hoàn toàn khi tắt ứng dụng.** (1 connections) — `app/services/camera/camera_connect.py`
- **Trả về True nếu chụp & lưu ảnh thành công** (1 connections) — `app/services/camera/camera_connect.py`
- **In thông tin phần cứng thiết bị camera ra console (debug).** (1 connections) — `app/services/camera/camera_connect.py`
- **Bật trigger -> chụp 1 ảnh -> lưu ảnh -> tắt trigger Return: (status, image,…** (1 connections) — `app/services/camera/camera_connect.py`

## Relationships

- [Community 74](Community_74.md) (6 shared connections)
- [Community 140](Community_140.md) (5 shared connections)
- [Community 137](Community_137.md) (4 shared connections)
- [Community 76](Community_76.md) (4 shared connections)
- [Community 125](Community_125.md) (3 shared connections)
- [Community 145](Community_145.md) (3 shared connections)
- [Community 134](Community_134.md) (2 shared connections)
- [Community 80](Community_80.md) (1 shared connections)
- [Community 24](Community_24.md) (1 shared connections)
- [Community 52](Community_52.md) (1 shared connections)
- [Community 66](Community_66.md) (1 shared connections)
- [Community 100](Community_100.md) (1 shared connections)

## Source Files

- `app/services/camera/camera_connect.py`

## Audit Trail

- EXTRACTED: 60 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*