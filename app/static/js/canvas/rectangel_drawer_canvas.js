import * as draw from "../utills/draw.js";

const NUMBER_OF_POINTS_TO_DRAW_RECT = 2;
const DISTANCE_DEFINE_IS_POINT_IN_RECT_BORDER = 10;

/**
 * Lớp quản lý logic vẽ, xem trước và tương tác với hình chữ nhật (Rectangle) trên Canvas.
 */
export class RectangleDrawer {
    static NAME_EVENT_WHEN_CLICK_ON_RECT = "setting-config-measure-rectangle";
    static NAME_EVENT_WHEN_CLICK_RIGHT_RECT = "erase-rectangle-and-redraw";
    static NAME_EVENT_WHEN_CLICK_ON_RECT_HAVE_ALREADY = "NAME_EVENT_WHEN_CLICK_ON_RECT_HAVE_ALREADY";

    /**
     * Khởi tạo một thực thể RectangleDrawer mới với các trạng thái mặc định.
     */
    constructor() {
        this.isDrawing = false;
        this.is_available_one_rect = false;
        this.callbacks = {};
        this.cout_click = 0;
        this.start = { x: -1, y: -1 };
        this.rect_current = {
            xStart: -1,
            yStart: -1,
            xEnd: -1,
            yEnd: -1,
            width: 0,
            height: 0
        };
        this.have_return = false;
    }

    /**
     * Đăng ký một callback xử lý cho một sự kiện cụ thể.
     * @param {string} eventName - Tên của sự kiện cần lắng nghe.
     * @param {Function} callback - Hàm thực thi khi sự kiện được kích hoạt.
     */
    on(eventName, callback) {
        if (!this.callbacks[eventName]) {
            this.callbacks[eventName] = [];
        }
        this.callbacks[eventName].push(callback);
    }

    /**
     * Kích hoạt một sự kiện và truyền dữ liệu tới toàn bộ các callback đã đăng ký.
     * @param {string} eventName - Tên của sự kiện cần kích hoạt.
     * @param {*} [data=null] - Dữ liệu đi kèm gửi tới các hàm callback.
     */
    emit(eventName, data = null) {
        if (!this.callbacks[eventName]) return;
        this.callbacks[eventName].forEach(callback => callback(data));
    }

    /**
     * Kiểm tra xem một điểm tọa độ có nằm đè lên đường viền của hình chữ nhật hay không.
     * @param {Object} rect - Đối tượng hình chữ nhật hiện tại cần kiểm tra.
     * @param {number} px - Tọa độ X của điểm cần kiểm tra.
     * @param {number} py - Tọa độ Y của điểm cần kiểm tra.
     * @param {number} threshold - Khoảng cách sai số cho phép tính từ viền hình chữ nhật.
     * @returns {boolean} Trả về true nếu điểm nằm trong phạm vi viền, ngược lại là false.
     */
    isPointOnRectBorder(rect, px, py, threshold) {
        const left = rect.xStart;
        const right = rect.xEnd;
        const top = rect.yStart;
        const bottom = rect.yEnd;

        const nearLeft = Math.abs(px - left) <= threshold && py >= top && py <= bottom;
        const nearRight = Math.abs(px - right) <= threshold && py >= top && py <= bottom;
        const nearTop = Math.abs(py - top) <= threshold && px >= left && px <= right;
        const nearBottom = Math.abs(py - bottom) <= threshold && px >= left && px <= right;

        return (nearLeft || nearRight || nearTop || nearBottom);
    }

    /**
     * Xử lý sự kiện click chuột trái để thực hiện vẽ điểm đầu, hoàn thành hình chữ nhật hoặc tương tác với hình sẵn có.
     * @param {Object} pos - Tọa độ chuột {x, y}.
     * @param {Object} canvasManager - Quản lý các ngữ cảnh canvas (ctxShape, ctxPrev, clearPreviewCanvas).
     */
    onClick(pos, canvasManager) {
        this.emit(RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT_HAVE_ALREADY, { x: pos.x, y: pos.y });
        if (this.have_return) {
            this.have_return = false;
            return;
        }

        // Đã có hình chữ nhật từ trước -> kiểm tra tương tác viền
        if (this.is_available_one_rect) {
            const status = this.isPointOnRectBorder(this.rect_current, pos.x, pos.y, DISTANCE_DEFINE_IS_POINT_IN_RECT_BORDER);
            console.log("Click vào rectangle:", status);

            if (status) {
                this.emit(RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT, this.rect_current);
                return;
            }

            this.reset();
            canvasManager.clearShapeCanvas();
        }

        // Tiến trình vẽ hình chữ nhật mới
        this.cout_click++;

        // Click lần thứ 1: Xác định điểm bắt đầu vẽ
        if (this.cout_click === 1) {
            this.start = { x: pos.x, y: pos.y };
            this.isDrawing = true;
            draw.drawPoint(canvasManager.ctxShape, pos.x, pos.y);
            return;
        }

        // Click lần thứ 2: Hoàn thành và lưu trữ hình chữ nhật
        if (this.cout_click === NUMBER_OF_POINTS_TO_DRAW_RECT) {
            const xStart = Math.min(this.start.x, pos.x);
            const yStart = Math.min(this.start.y, pos.y);
            const xEnd = Math.max(this.start.x, pos.x);
            const yEnd = Math.max(this.start.y, pos.y);
            const width = xEnd - xStart;
            const height = yEnd - yStart;

            if (width <= 0 || height <= 0) {
                this.cout_click--;
                return;
            }

            canvasManager.clearPreviewCanvas();

            this.rect_current = { xStart, yStart, xEnd, yEnd, width, height };

            const ctx = canvasManager.ctxShape;
            ctx.save();
            ctx.strokeStyle = "blue";
            ctx.lineWidth = 2;
            ctx.strokeRect(xStart, yStart, width, height);
            ctx.restore();

            this.is_available_one_rect = true;
            this.isDrawing = false;
            this.cout_click = 0;
            this.start = { x: -1, y: -1 };
        }
    }

    /**
     * Xử lý sự kiện di chuột để cập nhật bản vẽ xem trước (preview) của hình chữ nhật và đường chéo định hướng.
     * @param {Object} pos - Tọa độ chuột hiện tại {x, y}.
     * @param {Object} canvasManager - Quản lý các ngữ cảnh canvas (ctxPrev, clearPreviewCanvas).
     */
    onMouseMove(pos, canvasManager) {
        if (!this.isDrawing) return;

        canvasManager.clearPreviewCanvas();
        const ctx = canvasManager.ctxPrev;
        const width = pos.x - this.start.x;
        const height = pos.y - this.start.y;

        ctx.save();
        // Cấu hình nét vẽ xem trước hình chữ nhật
        ctx.strokeStyle = "blue";
        ctx.lineWidth = 2;
        ctx.setLineDash([]);
        ctx.strokeRect(this.start.x, this.start.y, width, height);

        // Cấu hình nét đứt cho đường chéo bám theo con trỏ chuột
        ctx.strokeStyle = "red";
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(this.start.x, this.start.y);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
        ctx.restore();
    }

    /**
     * Xử lý sự kiện click chuột phải để xóa hình chữ nhật hiện tại nếu click trúng viền.
     * @param {Object} pos - Tọa độ chuột khi click phải {x, y}.
     * @param {Object} canvasManager - Quản lý các ngữ cảnh canvas (ctxShape, clearPreviewCanvas).
     */
    onMouseRightClick(pos, canvasManager) {
        const status = this.isPointOnRectBorder(this.rect_current, pos.x, pos.y, DISTANCE_DEFINE_IS_POINT_IN_RECT_BORDER);

        if (status) {
            const canvas = canvasManager.ctxShape.canvas;
            canvasManager.ctxShape.clearRect(0, 0, canvas.width, canvas.height);
            canvasManager.clearPreviewCanvas();
            this.reset();
            console.log("Đã xóa rectangle");
        }

        this.emit(RectangleDrawer.NAME_EVENT_WHEN_CLICK_RIGHT_RECT, {
            status_check_point_in_rect_current: status,
            x: pos.x,
            y: pos.y
        });
    }

    onDoubleClick() {}
    onMouseDown() {}
    onMouseUp() {}

    /**
     * Đưa toàn bộ các trạng thái tọa độ và biến cờ kiểm tra của lớp vẽ về trạng thái mặc định ban đầu.
     */
    reset() {
        this.rect_current = {
            xStart: -1,
            yStart: -1,
            xEnd: -1,
            yEnd: -1,
            width: 0,
            height: 0
        };
        this.start = { x: -1, y: -1 };
        this.isDrawing = false;
        this.cout_click = 0;
        this.is_available_one_rect = false;
    }

    /**
     * Nạp rectangle đã tồn tại vào trạng thái tương tác của drawer.
     * @param {Object} rectangle - Rectangle có xStart, yStart, xEnd, yEnd.
     */
    setCurrentRectangle(rectangle) {
        if (!rectangle) return false;
        const xStart = Number(rectangle.xStart);
        const yStart = Number(rectangle.yStart);
        const xEnd = Number(rectangle.xEnd);
        const yEnd = Number(rectangle.yEnd);
        if (![xStart, yStart, xEnd, yEnd].every(Number.isFinite)) return false;
        if (xStart >= xEnd || yStart >= yEnd) return false;
        this.rect_current = {
            xStart,
            yStart,
            xEnd,
            yEnd,
            width: xEnd - xStart,
            height: yEnd - yStart,
        };
        this.is_available_one_rect = true;
        this.isDrawing = false;
        this.cout_click = 0;
        this.start = { x: -1, y: -1 };
        return true;
    }
}