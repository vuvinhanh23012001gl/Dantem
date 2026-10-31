# Community 32

> 19 nodes

## Key Concepts

- **.__init__()** (6 connections) — `app/engines/model_AI/model_unet.py`
- **.get_mask()** (5 connections) — `app/engines/model_AI/model_unet.py`
- **.get_polygon()** (5 connections) — `app/engines/model_AI/model_unet.py`
- **.predict()** (5 connections) — `app/engines/model_AI/model_unet.py`
- **.warmup()** (4 connections) — `app/engines/model_AI/model_unet.py`
- **.clean_mask_opening()** (3 connections) — `app/engines/model_AI/model_unet.py`
- **.find_largest_external_polygon()** (3 connections) — `app/engines/model_AI/model_unet.py`
- **.load_model()** (3 connections) — `app/engines/model_AI/model_unet.py`
- **.preprocess()** (3 connections) — `app/engines/model_AI/model_unet.py`
- **.create_file_path()** (2 connections) — `app/utils/folder.py`
- **Thực hiện feed-forward ảnh qua mô hình để lấy mặt nạ phân đoạn (binary mask).…** (1 connections) — `app/engines/model_AI/model_unet.py`
- **Chạy thử nghiệm mô hình (Warmup) với một ảnh đen (dummy image). Mục đích giúp…** (1 connections) — `app/engines/model_AI/model_unet.py`
- **Làm sạch mask bằng phép Morphology Opening (Erosion + Dilation) Parameters:…** (1 connections) — `app/engines/model_AI/model_unet.py`
- **Khởi tạo cấu hình, kiểm tra file trọng số và tải mô hình lên thiết bị phần…** (1 connections) — `app/engines/model_AI/model_unet.py`
- **Tìm contour ngoài cùng, lọc theo diện tích và xấp xỉ polygon Parameters: mask…** (1 connections) — `app/engines/model_AI/model_unet.py`
- **Khởi tạo kiến trúc mạng Unet++, nạp trọng số pre-trained từ file cấu hình và…** (1 connections) — `app/engines/model_AI/model_unet.py`
- **Tiền xử lý ảnh thô trước khi đưa vào mô hình Deep Learning. Các bước bao gồm:…** (1 connections) — `app/engines/model_AI/model_unet.py`
- **Dự đoán mask và làm sạch các đốm nhiễu nhỏ xung quanh bằng toán tử Opening.…** (1 connections) — `app/engines/model_AI/model_unet.py`
- **Trích xuất tọa độ đa giác xấp xỉ của vùng đối tượng lớn nhất từ ảnh đầu vào.…** (1 connections) — `app/engines/model_AI/model_unet.py`

## Relationships

- [Community 128](Community_128.md) (10 shared connections)
- [Community 22](Community_22.md) (1 shared connections)
- [Community 75](Community_75.md) (1 shared connections)

## Source Files

- `app/engines/model_AI/model_unet.py`
- `app/utils/folder.py`

## Audit Trail

- EXTRACTED: 29 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*