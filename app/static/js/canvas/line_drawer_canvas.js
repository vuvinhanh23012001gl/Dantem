import * as draw from "../utills/draw.js";

// File này định nghĩa lớp LineDrawer theo mô hình Event-driven (hướng sự kiện), 
// chịu trách nhiệm quản lý trạng thái, xử lý logic tương tác chuột (Click, Di chuyển, Chuột phải) để hỗ trợ người dùng vẽ, 
// xem trước (preview) và kiểm tra tương tác trên một đoạn thẳng (ứng dụng trong việc đo độ rộng mối hàn).

// --- CẤU HÌNH HẰNG SỐ ---
const NUMBER_OF_POINTS_ON_A_ATRAIGHT_LINE = 2; // Số điểm để tạo thành 1 đoạn thẳng (2 điểm)
const DISTANCE_DEFINE_IS_POINT_IN_LINE_SEGMENT = 50; // Khoảng cách tối đa (sai số px) để tính là click trúng line
 
export class LineDrawer {
    // Tên các sự kiện để bắn dữ liệu ra ngoài (Event Emmiters)
    static NAME_EVENT_WHEN_CLICK_ON_LINE = "setting-config-measure-width-line"; // Click chuột trái trúng line
    static NAME_EVENT_WHEN_CLICK_RIGHT_LINE = "erase-line-and-draw-arr-line";    // Click chuột phải vào line
    static NAME_EVENT_WHEN_CLICK_ON_LINE_HAVE_AREALY = "NAME_EVENT_WHEN_CLICK_ON_LINE_HAVE_AREALY"
    constructor() {
        this.isDrawing = false;             // Trạng thái: Có đang trong quá trình vẽ hay không
        this.is_available_one_line = false; // Trạng thái: Đã có đoạn thẳng nào được vẽ hoàn chỉnh chưa
        this.callbacks = {};                // Nơi lưu trữ danh sách các hàm lắng nghe sự kiện
        this.cout_click = 0;                // Bộ đếm số lần click chuột để vẽ line
        
        this.start = { x: -1, y: -1 };      // Tọa độ điểm click đầu tiên (điểm bắt đầu)
        
        this.line_current = {               // Tọa độ của đoạn thẳng hiện tại trên canvas
            xStart: -1, yStart: -1,
            xEnd: -1, yEnd: -1,
        };
        this.have_return =  false;
    }

    // Đăng ký lắng nghe sự kiện
    on(eventName, callback) {
        if (!this.callbacks[eventName]) {
            this.callbacks[eventName] = [];
        }
        this.callbacks[eventName].push(callback);
    }

    // Kích hoạt sự kiện và truyền dữ liệu đi
    emit(eventName, data = null) {
        if (!this.callbacks[eventName]) return;
        this.callbacks[eventName].forEach(callback => callback(data));
    }

    // Xử lý sự kiện click chuột trái
    onClick(pos, canvasManager) {
        this.emit(LineDrawer.NAME_EVENT_WHEN_CLICK_ON_LINE_HAVE_AREALY,{
            x:pos.x,
            y:pos.y,
        });
        if (this.have_return){
            this.have_return = false;
            return;
        }

        if (this.is_available_one_line) {
            let status_check_point_in_line = draw.isPointOnLineSegment(
                this.line_current.xStart, this.line_current.yStart,
                this.line_current.xEnd, this.line_current.yEnd,
                pos.x, pos.y, DISTANCE_DEFINE_IS_POINT_IN_LINE_SEGMENT
            );

            console.log("Click vào line:", status_check_point_in_line);
            if (status_check_point_in_line) {
                this.emit(LineDrawer.NAME_EVENT_WHEN_CLICK_ON_LINE, this.line_current); // Bắn sự kiện cấu hình line
                return;
            }
            console.log("Hãy click vào line vừa vẽ");
            return;
        }

        // TRƯỜNG HỢP 2: Đang tiến hành vẽ line mới
        this.cout_click++;
        
        // Click lần 1: Ghi nhận điểm bắt đầu và kích hoạt chế độ vẽ
        if (this.cout_click === 1) {
            this.start.x = pos.x;
            this.start.y = pos.y;
            this.isDrawing = true;
            draw.drawPoint(canvasManager.ctxShape, pos.x, pos.y); // Vẽ điểm mốc đầu tiên
        }
        // Click lần 2: Đủ số điểm -> Kết thúc vẽ đường thẳng chính thức
        else if (this.cout_click === NUMBER_OF_POINTS_ON_A_ATRAIGHT_LINE) {
            this.is_available_one_line = true;
            this.cout_click = 0;
            this.isDrawing = false;
            
            draw.drawPoint(canvasManager.ctxShape, pos.x, pos.y); // Vẽ điểm mốc thứ hai
            canvasManager.clearPreviewCanvas(); // Xóa đường vẽ nháp (preview)
            
            // Vẽ đường thẳng trong suốt/chính thức lên canvas hình ảnh
            draw.drawTransparentLine(canvasManager.ctxShape, this.start.x, this.start.y, pos.x, pos.y);
            
            // Cập nhật tọa độ vào line hiện tại
            this.line_current = {
                xStart: this.start.x,
                yStart: this.start.y,
                xEnd: pos.x,
                yEnd: pos.y,
            };
            
            // Reset tọa độ điểm bắt đầu về mặc định
            this.start = { x: -1, y: -1 };
        }
    }

    // Xử lý double click (Chưa dùng)
    onDoubleClick(pos, canvasManager) {}

    // Xử lý click chuột phải -> Kiểm tra xóa line
    onMouseRightClick(pos, canvasManager) {
        // Kiểm tra vị trí click chuột phải có nằm trên đoạn thẳng hiện tại không
        const status_check_point_in_line_current = draw.isPointOnLineSegment(
            this.line_current.xStart, this.line_current.yStart,
            this.line_current.xEnd, this.line_current.yEnd,
            pos.x, pos.y, DISTANCE_DEFINE_IS_POINT_IN_LINE_SEGMENT
        );  
        // Bắn sự kiện ra ngoài kèm trạng thái check và tọa độ chuột phải
        this.emit(LineDrawer.NAME_EVENT_WHEN_CLICK_RIGHT_LINE, {
            status_check_point_in_line_current,
            x: pos.x,
            y: pos.y
        });
    }

    // Xử lý di chuột (Xem trước đường vẽ - Preview)
    onMouseMove(pos, canvasManager) {
        if (this.isDrawing) {
            canvasManager.clearPreviewCanvas(); // Xóa nét vẽ cũ của khung hình trước
            // Vẽ một nét line mờ nối từ điểm bắt đầu đến vị trí chuột hiện tại
            draw.drawTransparentLine(canvasManager.ctxPrev, this.start.x, this.start.y, pos.x, pos.y);
        }
    }

    // Xử lý nhấn chuột (Chưa dùng)
    onMouseDown(pos, canvasManager) {}
    
    // Xử lý nhả chuột (Chưa dùng)
    onMouseUp(pos, canvasManager) {}

    // Khôi phục tất cả các trạng thái và tọa độ về mặc định (Xóa làm lại từ đầu)
    reset() {
        this.line_current = { xStart: -1, yStart: -1, xEnd: -1, yEnd: -1 };
        this.start = { x: -1, y: -1 };
        this.isDrawing = false;
        this.cout_click = 0;
        this.is_available_one_line = false;
    }
}