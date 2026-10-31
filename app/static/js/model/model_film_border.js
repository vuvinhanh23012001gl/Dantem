
export class FilmBorder {
    constructor(id_line, nameLine, widthMin, widthMax, xStart, yStart, xEnd, yEnd) {
        this.id_line = id_line;
        this.nameLine = nameLine;
        this.widthMin = widthMin;
        this.widthMax = widthMax;
        this.xStart = xStart;
        this.yStart = yStart;
        this.xEnd = xEnd;
        this.yEnd = yEnd;
    }
    // Chuyển đối tượng thành Plain Object (Dict) với cấu trúc { id_line: { data } }
    toDict() {
        return {
            [this.id_line]: {
                nameLine: this.nameLine,
                widthMin: this.widthMin,
                widthMax: this.widthMax,
                xStart: this.xStart,
                yStart: this.yStart,
                xEnd: this.xEnd,
                yEnd: this.yEnd
            }
        };
    }

    // Khởi tạo đối tượng FilmBorder từ Dict dữ liệu đầu vào (SỬA LỖI Ở ĐÂY)
    static fromDict(dict) {
        if (!dict) return null;

        // Lấy key đầu tiên chính là id_line
        const id_line = Object.keys(dict)[0];
        if (!id_line) return null;
        const data = dict[id_line];
        return new FilmBorder(
            id_line,
            data.nameLine,
            data.widthMin,
            data.widthMax,
            data.xStart,
            data.yStart,
            data.xEnd,
            data.yEnd
        );
    }

    /**
     * Kiểm tra dữ liệu đo khe hở.
     */
    validateSlitLevelsIncreasing() {
        const result = { isValid: true, errors: [] };
        const { nameLine, widthMin, widthMax } = this;

        // 1. Kiểm tra tên đường
        if (typeof nameLine !== "string" || nameLine.trim() === "") {
            result.isValid = false;
            result.errors.push({
                rowName: "Tên đường",
                currentVal: nameLine,
                expected: "Không được để trống"
            });
        }

        // 2. Kiểm tra kiểu dữ liệu (Tối ưu hóa đoạn check NaN)
        let hasTypeError = false;

        if (typeof widthMin !== "number" || Number.isNaN(widthMin)) {
            result.isValid = false;
            hasTypeError = true;
            result.errors.push({
                rowName: "Độ rộng Min",
                currentVal: widthMin,
                expected: "Phải là một số hợp lệ"
            });
        }

        if (typeof widthMax !== "number" || Number.isNaN(widthMax)) {
            result.isValid = false;
            hasTypeError = true;
            result.errors.push({
                rowName: "Độ rộng Max",
                currentVal: widthMax,
                expected: "Phải là một số hợp lệ"
            });
        }

        // Nếu sai kiểu dữ liệu thì dừng lại luôn, không so sánh giá trị nữa
        if (hasTypeError) {
            return result;
        }

        // 3. Kiểm tra giá trị số học
        if (widthMin < 0) {
            result.isValid = false;
            result.errors.push({
                rowName: "Độ rộng Min",
                currentVal: widthMin,
                expected: "Phải lớn hơn hoặc bằng 0"
            });
        }

        if (widthMax <= 0) {
            result.isValid = false;
            result.errors.push({
                rowName: "Độ rộng Max",
                currentVal: widthMax,
                expected: "Phải lớn hơn 0"
            });
        }

        if (widthMin >= widthMax) {
            result.isValid = false;
            result.errors.push({
                rowName: "Khoảng giới hạn",
                currentVal: `Min = ${widthMin}, Max = ${widthMax}`,
                expected: "Độ rộng Min phải nhỏ hơn Độ rộng Max"
            });
        }

        return result;
    }
}


