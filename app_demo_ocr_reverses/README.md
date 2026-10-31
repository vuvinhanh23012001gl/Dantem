# Hệ Thống OCR Nhận Diện Nội Dung & Xác Định Hướng Chữ Công Nghiệp (`app_demo_ocr_reverses`)

## 1. Tổng quan & Mục tiêu

Dự án **`app_demo_ocr_reverses`** là hệ thống kiểm tra ngoại quan nhãn/tem công nghiệp (Industrial Label Inspection) có khả năng:
- **Nhận diện nội dung văn bản (OCR)** đa ngôn ngữ (Latin/Tiếng Việt/Tiếng Anh/CJK, mã LOT, Serial, ngày sản xuất).
- **Xác định chính xác hướng chữ gốc** trước mọi bước hiệu chỉnh:
  - `0°` (`NORMAL`): Chữ đúng chiều chuẩn -> **OK**.
  - `90°` (`ROTATED_90`): Chữ xoay 90° theo chiều kim đồng hồ -> **NG**.
  - `180°` (`INVERTED`): Chữ bị dán/in ngược 180° -> **NG**.
  - `270°` (`ROTATED_270`): Chữ xoay 270° theo chiều kim đồng hồ (90° ngược chiều kim đồng hồ) -> **NG**.
  - `MIRROR`: Chữ bị lật gương trái-phải (Horizontal Flip) -> **NG**.
  - `MIXED_ORIENTATION`: Tem có nhiều dòng chữ bị in ngược/khác hướng nhau trên cùng một nhãn -> **NG**.
- **Tách biệt rõ góc xoay chuẩn (`angle` $\in \{0^\circ, 90^\circ, 180^\circ, 270^\circ\}$) và góc nghiêng phối cảnh/lắp đặt (`skew_angle` $\in (-45^\circ, +45^\circ]$)**: Nhãn bị nghiêng nhẹ (ví dụ `+8°`) nhưng chữ đúng chiều `0°` vẫn được nhận diện là `0° NORMAL` kèm cảnh báo góc nghiêng, không bị nhầm thành xoay `90°`/`180°`.
- **Bảo toàn tuyệt đối hệ tọa độ và hướng của ảnh gốc**: Không để bước tiền xử lý xoay tự động làm mất thông tin hướng ban đầu của tem.

---

## 2. Khảo sát & Lựa chọn Thư viện / Mô hình OCR

Hệ thống sử dụng bộ 4 mô hình **PaddleOCR v3.7.0 / PaddleX v3.7.2 (PP-OCRv6 & PP-LCNet)** chạy hoàn toàn **Offline** trên Windows (Python 3.11.0):

| Thành phần | Mô hình lựa chọn | Vai trò trong kiến trúc |
|---|---|---|
| **Document Orientation** | `PP-LCNet_x1_0_doc_ori` | Phân loại góc hướng toàn cục của ảnh gốc (`0°`, `90°`, `180°`, `270°`). |
| **Text Detection** | `PP-OCRv6_medium_det` | Phát hiện đa giác 4 đỉnh (`polygon`) và `bbox` trực tiếp trên hệ tọa độ ảnh gốc. |
| **Text Line Orientation** | `PP-LCNet_x1_0_textline_ori` | Phân loại hướng từng dòng chữ (`0_degree` vs `180_degree`). |
| **Text Recognition** | `PP-OCRv6_medium_rec` | Nhận diện ký tự độ chính xác cao và đối chiếu đa giả thuyết (`0°/90°`, `180°/270°`, `Mirror`). |

### Lý do lựa chọn giải pháp kết hợp PaddleOCR Modular + Multi-Hypothesis Orientation Engine:
1. **Không bị mất hướng gốc do Auto-Rotation**: Nếu gọi pipeline mặc định của PaddleOCR (`use_doc_orientation_classify=True`), ảnh sẽ bị xoay trước khi phát hiện chữ khiến tọa độ `bbox` bị lệch khỏi ảnh gốc và mất khả năng phát hiện tem có nhiều dòng chữ ngược hướng nhau. Việc tách rời 4 mô hình (`DocImgOrientationClassification`, `TextDetection`, `TextLineOrientationClassification`, `TextRecognition`) cho phép giữ nguyên tọa độ gốc 100%.
2. **Giải quyết triệt để bài toán `90°`/`270°` và `Mirror` (Lật gương)**:
   - Dựa trên tỷ lệ khung hình học `height / width >= 1.5` của đa giác chữ trên ảnh gốc kết hợp vector cạnh dài của `minAreaRect`, hệ thống tách biệt dòng chữ ngang (`0°`/`180°`) và dòng chữ dọc (`90°`/`270°`) đồng thời đo góc nghiêng `skew_angle`.
   - Đối với mỗi dòng chữ, hệ thống kiểm tra đồng thời 4 giả thuyết (`c_0`, `c_180`, `c_mirror_0`, `c_mirror_180`), kết hợp xác suất từ `PP-LCNet_x1_0_textline_ori`, điểm tự tin nhận diện từ `PP-OCRv6_medium_rec` và bộ đánh giá từ vựng/ký tự bất đối xứng (`compute_lexical_quality`, `symmetric_char_ratio`) để phát hiện chính xác cả chữ lật gương (`MIRROR`).
3. **Tăng cường ảnh tự động cho tem mờ, nhiễu, thiếu sáng**: Tích hợp bộ lọc `CLAHE` trên kênh sáng `LAB` + `Bilateral Filter` + `Unsharp Masking` tự động kích hoạt khi ảnh thiếu sáng hoặc độ tương phản thấp mà vẫn giữ nguyên kích thước ảnh gốc.

---

## 3. Cấu trúc Source Code (OOP)

```text
app_demo_ocr_reverses/
├── .venv/                          # Môi trường ảo Python 3.11.0 độc lập
├── app/
│   ├── core/
│   │   ├── constants.py            # Enum trạng thái hướng (NORMAL, INVERTED, MIRROR...) & OK/NG
│   │   ├── geometry.py             # Cắt vùng chữ phối cảnh, tính góc nghiêng skew_angle, đọc/ghi ảnh Unicode
│   │   └── logger.py               # Cấu hình logging chuẩn
│   ├── models/
│   │   ├── ocr_engine.py           # Wrapper PP-OCRv6_medium_det & PP-OCRv6_medium_rec + CLAHE enhancement
│   │   └── orientation_engine.py   # Wrapper PP-LCNet_x1_0_doc_ori, textline_ori & phân tích đối xứng Mirror
│   ├── services/
│   │   ├── ocr_service.py          # Điều phối pipeline OCR + Đa giả thuyết hướng trên tọa độ ảnh gốc
│   │   ├── orientation_service.py  # Hợp nhất hướng từng dòng & toàn nhãn, phán định công nghiệp OK/NG
│   │   └── visualization_service.py# Vẽ Bounding Box, Polygon, nhãn hướng & banner lên ảnh kết quả
│   ├── schemas/
│   │   └── ocr_schema.py           # Pydantic schemas chuẩn hóa đầu ra JSON
│   ├── ui/
│   │   └── main_window.py          # Giao diện Desktop PySide6 trực quan
│   └── main.py                     # Entry point hỗ trợ cả GUI (PySide6) và CLI
├── config/
│   ├── __init__.py
│   └── settings.yaml               # File cấu hình ngưỡng nhận diện và mô hình
├── data/
│   └── test_images/                # Bộ 14 ảnh kiểm thử (0°, 90°, 180°, 270°, Mirror, Nghiêng, Mờ/Nhiễu, Thực tế...)
├── output/                         # Thư mục xuất kết quả JSON, ảnh vẽ Bounding Box và báo cáo Benchmark
├── generate_test_images.py         # Script tự động sinh bộ ảnh kiểm thử và ground_truth.json
├── evaluate_benchmark.py           # Script chạy kiểm thử tự động và thống kê độ chính xác thực nghiệm
├── run_gui.bat                     # Chạy nhanh giao diện đồ họa PySide6 trên Windows
├── run_benchmark.bat               # Chạy nhanh bộ kiểm thử tự động
├── requirements.txt                # Danh sách các thư viện và phiên bản cố định
└── README.md                       # Tài liệu hướng dẫn sử dụng
```

---

## 4. Hướng dẫn Cài đặt & Khởi chạy

### A. Kích hoạt môi trường ảo (`.venv`)

Mở **PowerShell** tại thư mục dự án:

```powershell
cd "C:\Disk D\Project\Inspector_carton\app_demo_ocr_reverses"
.\.venv\Scripts\Activate.ps1
```

*(Nếu cần cài đặt lại từ `requirements.txt` trên máy mới:)*
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### B. Khởi chạy Giao diện Đồ họa (PySide6 GUI)

Cách 1 — Nháy đúp vào file `run_gui.bat` hoặc chạy trong PowerShell:
```powershell
cd "C:\Disk D\Project\Inspector_carton\app_demo_ocr_reverses"
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK="True"
.\.venv\Scripts\python.exe -m app.main
```

Cách 2 — Mở trực tiếp một ảnh bất kỳ lên giao diện GUI:
```powershell
.\.venv\Scripts\python.exe -m app.main --image "data/test_images/03_inverted_180deg.png"
```

### C. Kiểm tra ảnh bất kỳ bằng dòng lệnh (CLI Mode)

Kiểm tra 1 ảnh bất kỳ và xuất JSON + ảnh kết quả vào `output/`:
```powershell
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK="True"
.\.venv\Scripts\python.exe -m app.main --image "đường_dẫn_tới_ảnh.jpg" --no-gui
```

Kiểm tra hàng loạt toàn bộ ảnh trong một thư mục:
```powershell
.\.venv\Scripts\python.exe -m app.main --dir "data/test_images" --no-gui
```

### D. Tái tạo bộ ảnh kiểm thử và chạy Benchmark đánh giá

```powershell
.\.venv\Scripts\python.exe generate_test_images.py
.\.venv\Scripts\python.exe evaluate_benchmark.py
```

---

## 5. Định dạng JSON Kết quả Đầu ra

Mỗi ảnh kiểm tra được xuất ra file `output/<tên_ảnh>_result.json` với cấu trúc đầy đủ:

```json
{
    "image": "03_inverted_180deg.png",
    "success": true,
    "total_lines": 5,
    "orientation": {
        "angle": 180,
        "status": "INVERTED",
        "confidence": 0.9999,
        "is_mirrored": false,
        "skew_angle": 0.0,
        "is_tilted": false,
        "has_mixed_orientations": false,
        "doc_model_angle": 180,
        "doc_model_confidence": 0.9587
    },
    "texts": [
        {
            "line_id": 0,
            "text": "MADE IN VIETNAM",
            "confidence": 0.9996,
            "angle": 180,
            "status": "INVERTED",
            "orientation_confidence": 1.0,
            "is_mirrored": false,
            "skew_angle": 0.0,
            "bbox": [472, 29, 725, 65],
            "polygon": [[472, 29], [725, 29], [725, 65], [472, 65]]
        }
    ],
    "result": "NG",
    "reason": "Phát hiện chữ sai chiều chuẩn: Bị ngược (180°) (Góc=180°).",
    "processing_time_ms": 4555.5
}
```
