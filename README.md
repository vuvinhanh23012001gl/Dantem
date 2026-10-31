# Dantem

Hệ thống thị giác máy tính công nghiệp kiểm tra chất lượng dán tem, mã vạch (Barcode), mã phản hồi nhanh (QR Code), OCR chữ và phát hiện dị vật cho bao bì carton.

## 1. Giới thiệu dự án
Dự án **Dantem (Inspector Carton)** cung cấp giải pháp thị giác máy tính thời gian thực (Computer Vision) kết hợp giao diện Web quản trị & vận hành sản xuất:
- **Kiểm tra căn chỉnh tem (Stamp Alignment)**: Phát hiện có/lệch tem, định vị đa khung hình (Multi-ROI).
- **Kiểm tra Barcode (1D)**: Quét và giải mã tất cả các chuẩn mã vạch công nghiệp (Code 128, Code 39, EAN, UPC,...) sử dụng ZXing-C++.
- **Kiểm tra mã QR (2D)**: Quét và giải mã QRCode, MicroQRCode, so khớp chuỗi chuẩn xác (`expected_text`).
- **Kiểm tra chữ OCR**: Nhận dạng ký tự quang học trên bề mặt sản phẩm.
- **Kiểm tra dị vật & bất thường (PatchCore / YOLO)**: Phát hiện lỗi bề mặt và dị vật lạ.
- **Tích hợp phần cứng**: Giao tiếp PLC, Robot và Camera công nghiệp (Sentech/StapiPy).

## 2. Hướng dẫn cài đặt môi trường
Dự án sử dụng Python 3.11. Để cài đặt môi trường phát triển trên máy mới:

```bash
# 1. Tạo môi trường ảo
python -m venv .venv

# 2. Kích hoạt môi trường ảo (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# 3. Nâng cấp pip và cài đặt thư viện phụ thuộc
pip install --upgrade pip
pip install -r requirements.txt

# 4. Cài đặt thư viện Camera Sentech (nếu kết nối camera vật lý)
pip install stapipy-1.2.2-cp311-cp311-win_amd64.whl
```

## 3. Khởi chạy ứng dụng
- Chạy toàn bộ hệ thống (App + Simulator):
  ```bash
  .\run_all.bat
  ```
- Hoặc khởi chạy riêng ứng dụng Web:
  ```bash
  .\run_app.bat
  ```
- Hoặc chạy qua lệnh Python:
  ```bash
  python run.py
  ```

Giao diện Web mặc định truy cập tại: `http://localhost:8000` hoặc cổng được cấu hình trong `app/config/`.
