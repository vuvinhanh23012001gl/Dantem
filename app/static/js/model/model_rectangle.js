export class ModelRectangle {
    constructor(id = -1, name = "", xStart = -1, yStart = -1, xEnd = -1, yEnd = -1) {
        console.log("Có dữ liệu");
        this.id = id;
        this.name = name;
        this.xStart = xStart;
        this.yStart = yStart;
        this.xEnd = xEnd;
        this.yEnd = yEnd;
        this.width = Math.abs(xEnd - xStart);
        this.height = Math.abs(yEnd - yStart);
    }

    updatePosition(xStart, yStart, xEnd, yEnd) {
        this.xStart = xStart;
        this.yStart = yStart;
        this.xEnd = xEnd;
        this.yEnd = yEnd;
        this.width = Math.abs(xEnd - xStart);
        this.height = Math.abs(yEnd - yStart);
    }

    toDict() {
        return {
            id: this.id,
            name: this.name,
            xStart: this.xStart,
            yStart: this.yStart,
            xEnd: this.xEnd,
            yEnd: this.yEnd,
            width: this.width,
            height: this.height
        };
    }

    static fromDict(data) {
        if (!data || typeof data !== "object") {
            return new ModelRectangle();
        }
        const id = data.id ?? -1;
        const name = data.name ?? "";
        const xStart = data.xStart ?? data.x_start ?? -1;
        const yStart = data.yStart ?? data.y_start ?? -1;
        // Nếu API gửi xEnd/yEnd thì dùng, nếu gửi width/height thì tự tính xEnd/yEnd
        let xEnd = data.xEnd ?? data.x_end ?? -1;
        let yEnd = data.yEnd ?? data.y_end ?? -1;
        if (xEnd === -1 && (data.width || data.width === 0) && xStart !== -1) {
            xEnd = xStart + data.width;
        }
        if (yEnd === -1 && (data.height || data.height === 0) && yStart !== -1) {
            yEnd = yStart + data.height;
        }
        console.log("Tạo lớp regtangle.");
        return new ModelRectangle(id, name, xStart, yStart, xEnd, yEnd);
    }

    isValid() {
        // 1. Kiểm tra các tọa độ không được ở trạng thái mặc định (-1)
        const hasValidCoords = 
            this.xStart !== -1 && 
            this.yStart !== -1 && 
            this.xEnd !== -1 && 
            this.yEnd !== -1;
        // 2. Kích thước hình chữ nhật phải lớn hơn 0
        const hasValidSize = this.width > 0 && this.height > 0;
        // 3. Kết hợp với hàm validate() hiện tại của class
        const isNameValid = this.validate().isValid;
        return hasValidCoords && hasValidSize && isNameValid;
    }

    validate() {
    const errors = [];

    if (!this.name || this.name.trim() === "") {
        errors.push({
            field: "name",
            rowName: "Tên hình",
            currentVal: this.name,
            expected: "Không được để trống"
        });
    }
    return {
        isValid: errors.length === 0,
        errors
    };
}
}