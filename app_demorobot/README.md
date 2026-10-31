# PHẦN MỀM GIẢ LẬP PLC ROBOT (APP_DEMOROBOT)

Phần mềm giả lập **Bộ điều khiển PLC Robot công nghiệp (PROD4)** giao tiếp với phần mềm thị giác máy tính / xử lý ảnh (`Inspector_carton`) qua giao thức **Ethernet TCP Socket**.

Dự án được xây dựng hoàn toàn độc lập, sử dụng chuẩn **Clean Architecture** và giao diện **Desktop GUI Tkinter** sắc nét, nhẹ nhàng, không yêu cầu cài thêm bất kỳ thư viện bên ngoài nào.

---

## 1. Bảng Đặc Tả Tập Lệnh & Giao Thức (Theo `Bang_Giao_Tiep_Robot_PLC_PROD4.xlsx`)

### 1.1. Cấu hình Mạng TCP Socket
- **Vai trò PLC (`app_demorobot`)**: TCP Server (Listener) mở cổng chờ kết nối.
- **Vai trò PC Vision (`Inspector_carton`)**: TCP Client chủ động kết nối tới PLC.
- **Địa chỉ IP mặc định**: `127.0.0.1` (kiểm thử cục bộ cùng máy) hoặc `0.0.0.0` / IP card mạng LAN (`192.168.1.10`).
- **Cổng kết nối (Port)**: `2000` (hoặc `3000`).
- **Bảng mã (Encoding)**: `ASCII`.
- **Ký tự phân cách (Delimiter)**: Dấu phẩy `,`.
- **Ký tự kết thúc gói tin (Terminator)**: `\r\n` (CRLF) - **BẮT BUỘC**.

### 1.2. Danh mục Lệnh từ PC gửi tới PLC (PC -> PLC)

| Tên Lệnh | Cú pháp Gói tin | Ý nghĩa & Mô tả |
| :--- | :--- | :--- |
| **MOV** | `MOV,<X>,<Y>,<Z>,<Rx>,<Ry>,<Rz>\r\n` | Di chuyển Robot đến tọa độ 6-DOF (mm và độ). Ví dụ: `MOV,450.50,-120.25,210.00,180.00,0.00,45.00\r\n` |
| **HOME** | `HOME\r\n` | Đưa Robot về vị trí gốc/nghỉ an toàn ban đầu (`X=300, Y=0, Z=250, Rx=180, Ry=0, Rz=0`). |
| **GET_STATUS** | `GET_STATUS\r\n` | Truy vấn trạng thái tức thời của Robot để biết có sẵn sàng nhận lệnh mới không. |
| **STOP** | `STOP\r\n` | Yêu cầu dừng mềm chuyển động ngay lập tức từ giao diện máy tính. |
| **RESET** | `RESET\r\n` | Xóa trạng thái sự cố/dừng, đưa Robot về sẵn sàng (`READY`). |

### 1.3. Danh mục Phản hồi từ PLC trả về PC (PLC -> PC)

| Tín hiệu Phản hồi | Khi nào phát sinh? | Ý nghĩa & Hành động tương ứng |
| :--- | :--- | :--- |
| `READY\r\n` | Khi nhận `GET_STATUS` lúc rảnh rỗi hoặc sau lệnh `RESET` | Robot an toàn, cho phép PC gửi lệnh `MOV` tiếp theo. |
| `BUSY,MOV\r\n` | Ngay khi nhận được lệnh `MOV` hợp lệ | Báo Robot bắt đầu di chuyển -> PC khóa nút gửi, chờ đợi. |
| `ARRIVED,MOV\r\n` | Khi Robot đã chạy xong thời gian trễ và dừng ổn định | Báo Robot đã đến đúng tọa độ -> PC kích hoạt Camera chụp ảnh kiểm tra. |
| `BUSY,HOME\r\n` | Ngay khi nhận được lệnh `HOME` | Báo Robot đang quay về vị trí gốc. |
| `ARRIVED,HOME\r\n` | Khi Robot đã về tới vị trí gốc an toàn | Báo Robot đã về gốc ổn định. |
| `STOPPED\r\n` | Khi nhận lệnh `STOP` hoặc nút dừng ngoài tủ điện | Robot đã dừng chuyển động hoàn toàn. |
| `ERROR,<Mã_lỗi>\r\n` | Khi có sự cố an toàn hoặc bấm nút E-Stop (vd `ERROR,E01`) | Dừng khẩn cấp, cảnh báo lỗi lên màn hình PC. |

---

## 2. Cấu Trúc Thư Mục Dự Án

```
app_demorobot/
│
├── config/
│   ├── __init__.py
│   └── settings.py         # Toàn bộ thông số mặc định (IP, Port, Delimiter, Terminator, Mã lỗi)
│
├── core/
│   ├── __init__.py
│   ├── protocol.py         # Parser cú pháp lệnh, kiểm tra số thực 6-DOF, đóng gói chuỗi CRLF
│   ├── robot_state.py      # Quản lý máy trạng thái (READY, BUSY, STOPPED, ERROR) & tọa độ 6-DOF
│   └── motion_sim.py       # Bộ điều khiển giả lập thời gian trễ di chuyển có thể hủy tức thời
│
├── network/
│   ├── __init__.py
│   ├── tcp_server.py       # TCP Server đa luồng (multi-threaded), xử lý đệm ký tự CRLF an toàn
│   └── test_client.py      # Client TCP tiện ích tích hợp sẵn để tự kiểm thử nội bộ trên UI
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py      # Bố cục giao diện Desktop Tkinter Dashboard 2 cột chuyên nghiệp
│   ├── widgets.py          # Custom widgets: Đèn tháp tín hiệu 3 tầng + còi, Pose Cards, Log Viewer, Tables
│   └── theme.py            # Bảng màu sắc công nghiệp hiện đại (Industrial Dark Theme)
│
├── tests/
│   ├── __init__.py
│   └── test_protocol.py    # Bộ kiểm thử tự động (Unit & Integration Tests)
│
├── run_simulator.py        # File chạy chính để mở giao diện phần mềm giả lập
└── README.md               # Tài liệu hướng dẫn sử dụng và kiểm thử
```

---

## 3. Hướng Dẫn Cài Đặt & Khởi Động

Phần mềm sử dụng thư viện Python có sẵn (`tkinter`, `socket`, `threading`, `queue`, `unittest`), **không cần cài thêm thư viện phụ thuộc ngoài**.

### 3.1. Khởi động Giao diện Giả lập PLC
Chạy lệnh sau từ thư mục gốc của dự án:
```powershell
.\.venv\Scripts\python app_demorobot/run_simulator.py
```
Hoặc:
```powershell
cd app_demorobot
..\.venv\Scripts\python run_simulator.py
```

### 3.2. Chạy Kiểm thử Tự động (Unit Tests & Socket Integration Tests)
```powershell
.\.venv\Scripts\python -m unittest app_demorobot/tests/test_protocol.py -v
```

---

## 4. Các Tính Năng Nổi Bật Trên Giao Diện

1. **🌐 Cấu hình & Quản lý Server TCP**:
   - Cho phép nhập IP Listen (`127.0.0.1` hoặc `0.0.0.0`) và Cổng Port (`2000`).
   - Nút bật/tắt Server với huy hiệu trạng thái hiển thị số lượng Client đang kết nối.
2. **⚡ Giám sát Trạng thái & Đèn tháp (Tower Light & Buzzer)**:
   - Huy hiệu trạng thái to rõ: `READY` (xanh), `BUSY` (vàng), `STOPPED` (cam), `ERROR` (đỏ).
   - Đồ họa đèn tháp 3 màu (Đỏ / Vàng / Xanh) và biểu tượng Còi cảnh báo (Buzzer) phát sáng tương ứng với trạng thái thực tế của PLC.
3. **📍 Tọa độ 6-DOF Thời gian Thực**:
   - Thẻ hiển thị trực quan các trục: `X (mm)`, `Y (mm)`, `Z (mm)`, `Rx (°)`, `Ry (°)`, `Rz (°)`.
4. **🎛️ Giả lập Phần cứng & Nút bấm Tủ điện (Hardware Emulation)**:
   - Điều chỉnh thời gian trễ di chuyển (Delay) từ `0.1s` đến `10.0s` (mặc định `1.5s`).
   - Nút dừng khẩn cấp **🛑 E-STOP**: Hủy chuyển động ngay lập tức và phát tín hiệu cảnh báo.
   - Nút **START**, **STOP**, **RESET**.
   - Hộp chọn và kích hoạt lỗi mô phỏng: `E01` (Quá tải), `E02` (Vượt hành trình), `E03` (Mở cửa an toàn), `E04` (Tụt áp suất khí).
5. **🧪 Test Client Tích Hợp Sẵn**:
   - Nhập 6 tọa độ và bấm nút **Gửi MOV**.
   - Các nút gửi nhanh: `HOME`, `GET_STATUS`, `STOP`, `RESET` để kiểm tra phản hồi mà không cần mở app khác.
6. **📥📤 Bảng Lịch sử Lệnh Nhận & Lệnh Gửi**:
   - Ghi lại chi tiết từng gói tin: Thời gian chính xác đến mili-giây, IP Client, nội dung gói tin.
7. **📝 Nhật ký Hoạt động (Activity Log)**:
   - Phân biệt màu sắc: `[INFO]`, `[SUCCESS]`, `[WARN]`, `[ERROR]`, `[CMD_IN]`, `[CMD_OUT]`.
   - Tính năng Tự động cuộn (Auto-scroll) và Nút Xóa Log.

---

## 5. Kết Nối Với Phần Mềm Vision (`Inspector_carton`)

Cấu hình trong file [`app/storage/config/robot.json`](file:///c:/Disk%20D/Project/Inspector_carton/app/storage/config/robot.json):
```json
{
  "connection": {
    "protocol": "TCP_SOCKET",
    "plc_role": "SERVER",
    "plc_ip": "127.0.0.1",
    "plc_port": 2000,
    "pc_role": "CLIENT",
    "timeout_ms": 1500,
    "encoding": "ASCII",
    "delimiter": ",",
    "terminator": "\r\n"
  }
}
```

Khi `app_demorobot` đang bật server:
- Gọi API kiểm tra kết nối từ `Inspector_carton`:
  `POST http://127.0.0.1:8001/api/robot/test_connection`
  với payload `{"plc_ip": "127.0.0.1", "plc_port": 2000}` sẽ nhận được kết quả thành công và độ trễ ping mạng thấp (< 10ms).
