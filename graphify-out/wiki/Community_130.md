# Community 130

> 7 nodes

## Key Concepts

- **.read_json_from_file()** (8 connections) — `app/utils/folder.py`
- **.get_or_create_json_by_path()** (4 connections) — `app/utils/folder.py`
- **.__init__()** (3 connections) — `app/services/log/config_software.py`
- **.__init__()** (3 connections) — `app/services/log/infor_software.py`
- **.read()** (2 connections) — `app/repository/choose_product_repository.py`
- **Kiểm tra nếu file JSON đã tồn tại thì trả về đường dẫn. Nếu chưa có: tạo folder…** (1 connections) — `app/utils/folder.py`
- **Đọc dữ liệu từ file JSON. - Luôn trả về dict để tránh lỗi NoneType.** (1 connections) — `app/utils/folder.py`

## Relationships

- [Community 75](Community_75.md) (2 shared connections)
- [Community 106](Community_106.md) (1 shared connections)
- [Community 3](Community_3.md) (1 shared connections)
- [Community 79](Community_79.md) (1 shared connections)
- [Community 57](Community_57.md) (1 shared connections)
- [Community 87](Community_87.md) (1 shared connections)
- [Community 97](Community_97.md) (1 shared connections)

## Source Files

- `app/repository/choose_product_repository.py`
- `app/services/log/config_software.py`
- `app/services/log/infor_software.py`
- `app/utils/folder.py`

## Audit Trail

- EXTRACTED: 15 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*