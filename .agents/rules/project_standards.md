---
trigger: always_on
---

# Project Standards — Python & Computer Vision

## 1. Mục tiêu

Đảm bảo mã nguồn dễ hiểu, dễ bảo trì, hạn chế lỗi hồi quy và giữ ổn định các chức năng hiện có.

Ưu tiên:

* Đúng yêu cầu nghiệp vụ.
* Thay đổi tối thiểu, đúng phạm vi.
* Tương thích với kiến trúc và interface hiện tại.
* An toàn về dữ liệu, tài nguyên và xử lý đồng thời.
* Có thể kiểm tra và truy vết khi xảy ra lỗi.

## 2. Quy tắc sửa đổi mã nguồn

* Khảo sát cấu trúc và logic hiện có trước khi thay đổi.
* Tái sử dụng module, class, function và cấu hình hiện có khi phù hợp.
* Không tự ý đổi tên, xóa hoặc thay đổi public API, schema, giao thức thiết bị hay hành vi đang được sử dụng.
* Không sửa các thành phần ngoài phạm vi nếu không cần thiết.
* Không tạo abstraction, dependency hoặc lớp trung gian không mang lại lợi ích rõ ràng.
* Không giả định hành vi của hệ thống khi chưa xác minh từ source code hoặc kiểm thử.

## 3. Python Coding Standards

* Dùng tên biến, hàm, class rõ nghĩa; tuân thủ `snake_case` và `PascalCase`.
* Sử dụng type hints cho interface và hàm quan trọng.
* Dùng `dataclass` hoặc kiểu dữ liệu có cấu trúc khi cần truyền nhiều trường liên quan.
* Mỗi function/class có trách nhiệm rõ ràng; tránh logic nghiệp vụ bị lặp ở nhiều nơi.
* Validate dữ liệu tại ranh giới tiếp nhận: API, file, UI, camera, serial, database.
* Không dùng `except: pass`; chỉ bắt lỗi có chủ đích và giữ ngữ cảnh lỗi.
* Dùng `logging` thay cho `print()` trong ứng dụng.
* Không hardcode đường dẫn máy cá nhân, credential hoặc thông số vận hành cần cấu hình.
* Không thêm hoặc nâng cấp dependency nếu chưa đánh giá tính cần thiết và tương thích.

## 4. Kiến trúc và dữ liệu

* Tách trách nhiệm UI/API, xử lý nghiệp vụ, truy cập dữ liệu và giao tiếp thiết bị khi độ phức tạp yêu cầu.
* Không để UI chứa toàn bộ logic nghiệp vụ hoặc điều khiển thiết bị.
* Tránh import vòng, phụ thuộc ngược và trạng thái global có thể bị sửa từ nhiều nơi.
* Xác định rõ nơi sở hữu cấu hình, trạng thái và tài nguyên.
* Giữ nhất quán giữa dữ liệu đầu vào, dữ liệu trung gian và kết quả.
* Không thay đổi schema, định dạng file hoặc response API mà không đánh giá tương thích.

## 5. Graphify & phân tích kiến trúc

Graphify hỗ trợ xác định cấu trúc, dependency, luồng gọi và phạm vi ảnh hưởng; không thay thế việc kiểm tra source code.

* Ưu tiên sử dụng graph hiện có để tìm entry point, module, class, function và quan hệ liên quan.
* Kiểm tra graph có phù hợp với trạng thái mã nguồn hiện tại hay không.
* Chỉ đọc sâu các file và đoạn code liên quan đến yêu cầu.
* Xác minh bằng source code các logic, interface, shared state và side effect quan trọng.
* Trước thay đổi, xem xét thành phần phụ thuộc, dữ liệu, API, thiết bị và kiểm thử hồi quy bị ảnh hưởng.
* Cập nhật graph khi thay đổi đáng kể cấu trúc hoặc dependency, theo cấu hình dự án.
* Nếu Graphify không khả dụng, dùng tìm kiếm symbol, import, call hierarchy và source code; không suy diễn quan hệ chưa xác minh.

Quy trình bắt buộc sử dụng Graphify và báo cáo tiến độ được quy định trong `AGENTS.md`.

## 6. Computer Vision & AI

* Xác định rõ định dạng ảnh, kích thước, channel, color space, kiểu dữ liệu và hệ tọa độ.
* Kiểm tra ảnh rỗng, dữ liệu lỗi, ROI và cấu hình trước khi xử lý.
* Giữ nhất quán quy ước tọa độ và calibration.
* Tách các bước preprocessing, inference, postprocessing và kiểm tra kết quả khi phù hợp.
* Phân biệt lỗi xử lý với kết quả OK/NG hoặc anomaly.
* Không tải lại model ở mỗi ảnh/request nếu có thể tái sử dụng an toàn.
* Khi thay đổi model hoặc preprocessing, đánh giá ảnh hưởng đến kết quả và dữ liệu hiện có.

## 7. Concurrency & Performance

* Chọn thread, process hoặc async theo đặc tính I/O, CPU và GPU; không mặc định tăng worker sẽ tăng tốc.
* Xác định giới hạn queue và chính sách khi queue đầy.
* Kiểm soát shared state, lock và quyền sở hữu tài nguyên giữa các thread/process.
* Tránh thao tác blocking trên UI thread.
* Đo bottleneck trước khi tối ưu; so sánh trước/sau trong điều kiện tương đương.
* Không đánh đổi độ chính xác hoặc tính ổn định để tăng tốc nếu chưa được chấp thuận.

## 8. Hardware & External Integration

Áp dụng cho camera, serial, STM32, PLC, IAI, socket và dịch vụ bên ngoài.

* Đóng gói giao tiếp thiết bị trong module/adapter có trách nhiệm rõ ràng.
* Xác định timeout, retry, trạng thái kết nối và cách xử lý lỗi.
* Không mở hoặc điều khiển cùng tài nguyên từ nhiều nơi nếu chưa có cơ chế phối hợp.
* Không tự ý thay đổi command format, baud rate, register mapping hoặc giao thức.
* Quản lý đầy đủ vòng đời tài nguyên: khởi tạo, sử dụng, lỗi và giải phóng.
* Không coi việc gửi lệnh thành công là bằng chứng thiết bị đã thực thi thành công.

## 9. API, UI, File & Database

* Giữ request/response, event và payload nhất quán.
* Validate dữ liệu đầu vào; không để lộ exception nội bộ hoặc credential cho client.
* Không thực hiện tác vụ blocking hoặc xử lý nặng trực tiếp trong UI/API handler nếu gây nghẽn.
* Dùng đường dẫn cấu hình phù hợp; không xóa hoặc ghi đè dữ liệu người dùng ngoài yêu cầu.
* Dùng truy vấn có tham số; quản lý transaction khi cần.
* Không thay đổi cấu trúc dữ liệu lưu trữ mà thiếu đánh giá tương thích hoặc phương án chuyển đổi.

## 10. Kiểm thử & hoàn thiện

Tùy phạm vi thay đổi, kiểm tra:

* Import, khởi tạo và luồng xử lý chính.
* Dữ liệu hợp lệ, dữ liệu lỗi và tình huống biên quan trọng.
* Interface, cấu hình và tương thích với module liên quan.
* Tài nguyên được giải phóng đúng cách.
* Regression đối với chức năng có nguy cơ bị ảnh hưởng.

Nếu thiếu thiết bị hoặc môi trường triển khai, kiểm thử phần có thể xác minh và nêu rõ giới hạn. Không tuyên bố đã kiểm thử thành công nếu chưa thực hiện.

Cập nhật tài liệu khi thay đổi interface, cấu hình, triển khai hoặc hành vi vận hành.

## 11. Nguyên tắc kết thúc thay đổi

Chỉ kết luận hoàn tất khi:

* Đáp ứng yêu cầu đã xác nhận.
* Không có thay đổi ngoài ý muốn đã biết.
* Các kiểm tra phù hợp đã được thực hiện.
* Giới hạn hoặc phần chưa xác minh được nêu rõ.

Quy trình thực hiện và định dạng báo cáo kết quả tuân theo `AGENTS.md`.
