# Community 129

> 10 nodes

## Key Concepts

- **.update()** (6 connections) — `app/config/robot_config.py`
- **.to_dict()** (5 connections) — `app/config/robot_config.py`
- **.validate_config()** (5 connections) — `app/config/robot_config.py`
- **get_robot_config()** (5 connections) — `app/routers/api_robot_config.py`
- **Any** (4 connections)
- **get** (2 connections)
- **Xuất dữ liệu cấu hình dưới dạng dictionary.** (1 connections) — `app/config/robot_config.py`
- **Cập nhật dữ liệu cấu hình mới sau khi đã validate chặt chẽ.** (1 connections) — `app/config/robot_config.py`
- **Kiểm tra tính hợp lệ của toàn bộ dữ liệu cấu hình.** (1 connections) — `app/config/robot_config.py`
- **Lấy cấu hình hiện tại của Robot và kết nối PLC từ storage/config/robot.json.** (1 connections) — `app/routers/api_robot_config.py`

## Relationships

- [Community 78](Community_78.md) (7 shared connections)
- [Community 84](Community_84.md) (2 shared connections)
- [Community 119](Community_119.md) (1 shared connections)
- [Community 24](Community_24.md) (1 shared connections)

## Source Files

- `app/config/robot_config.py`
- `app/routers/api_robot_config.py`

## Audit Trail

- EXTRACTED: 17 (81%)
- INFERRED: 4 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*