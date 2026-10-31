# Community 7

> 20 nodes

## Key Concepts

- **.get_bounding_boxes()** (8 connections) — `app/engines/model_AI/model_patch_core.py`
- **ndarray** (8 connections)
- **._extract_features()** (7 connections) — `app/engines/model_AI/model_patch_core.py`
- **.predict_with_anomaly_boxes()** (7 connections) — `app/engines/model_AI/model_patch_core.py`
- **.preprocess()** (7 connections) — `app/engines/model_AI/model_patch_core.py`
- **._merge_overlapping_boxes()** (6 connections) — `app/engines/model_AI/model_patch_core.py`
- **.get_bounding_box()** (5 connections) — `app/engines/model_AI/model_patch_core.py`
- **._boxes_overlap()** (3 connections) — `app/engines/model_AI/model_patch_core.py`
- **.draw_bounding_boxes()** (3 connections) — `app/engines/model_AI/model_patch_core.py`
- **._union_boxes()** (3 connections) — `app/engines/model_AI/model_patch_core.py`
- **Tensor** (2 connections)
- **Dự đoán anomaly score, tạo heatmap overlay và trích xuất bounding boxes theo…** (1 connections) — `app/engines/model_AI/model_patch_core.py`
- **Dự đoán và trích xuất trực tiếp ảnh gốc được vẽ đè các khung bao quanh vùng bất…** (1 connections) — `app/engines/model_AI/model_patch_core.py`
- **Tính toán phân ngưỡng động bản đồ bất thường, lọc nhiễu hạt và trích xuất danh…** (1 connections) — `app/engines/model_AI/model_patch_core.py`
- **Gộp các box bất thường giao nhau hoặc nằm trong cùng một vùng. Args: boxes:…** (1 connections) — `app/engines/model_AI/model_patch_core.py`
- **Kiểm tra hai box có giao nhau với diện tích dương hay không.** (1 connections) — `app/engines/model_AI/model_patch_core.py`
- **Trả box nhỏ nhất bao phủ toàn bộ hai box đầu vào.** (1 connections) — `app/engines/model_AI/model_patch_core.py`
- **Thực hiện vẽ các hộp chữ nhật bao quanh vùng lỗi kèm nhãn nền màu tương ứng lên…** (1 connections) — `app/engines/model_AI/model_patch_core.py`
- **Tiền xử lý ảnh thô từ mảng NumPy sang dạng Tensor chuẩn hóa chuẩn bị đưa vào mô…** (1 connections) — `app/engines/model_AI/model_patch_core.py`
- **Hàm nội bộ thực hiện trích xuất, gom cụm (pooling) và ghép nối các đặc trưng…** (1 connections) — `app/engines/model_AI/model_patch_core.py`

## Relationships

- [Community 128](Community_128.md) (15 shared connections)
- [Community 9](Community_9.md) (1 shared connections)

## Source Files

- `app/engines/model_AI/model_patch_core.py`

## Audit Trail

- EXTRACTED: 40 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*