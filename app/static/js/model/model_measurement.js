export class Measurement {
    constructor(
        lineId = "",
        nameLine = "",
        level1 = 0,
        level2 = 0,
        level3 = 0,
        level4 = 0,
        level5 = 0,
        xStart = 0,
        yStart = 0,
        xEnd = 0,
        yEnd = 0
    ) {
        // Lưu trữ trực tiếp làm thuộc tính của class (cấu trúc phẳng)
        this.lineId = lineId;
        this.nameLine = nameLine;
        this.level1 = level1;
        this.level2 = level2;
        this.level3 = level3;
        this.level4 = level4;
        this.level5 = level5;
        this.xStart = xStart;
        this.yStart = yStart;
        this.xEnd = xEnd;
        this.yEnd = yEnd;
    }

    // Khi cần export dữ liệu ra dict tổng thì mới bọc lại theo cấu trúc cũ
    toDict() {
        return {
            [this.lineId]: {
                name_line: this.nameLine,
                level1: this.level1,
                level2: this.level2,
                level3: this.level3,
                level4: this.level4,
                level5: this.level5,
                xStart: this.xStart,
                yStart: this.yStart,
                xEnd: this.xEnd,
                yEnd: this.yEnd
            }
        };
    }
    toDictForDraw() {
        return {
                name_line: this.nameLine,
                xStart: this.xStart,
                yStart: this.yStart,
                xEnd: this.xEnd,
                yEnd: this.yEnd
        };
    }
    
    validateWeldLevelsIncreasing() {
                const errors = [];
                if (typeof this.nameLine !== 'string' || this.nameLine.trim() === "") {
                    errors.push({
                        rowName: "Tên Line",
                        currentVal: `"${this.nameLine}"`,
                        expected: "Một chuỗi chữ/số bất kỳ và không được để trống"
                    });
                }
                const l1 = parseFloat(this.level1);
                const l2 = parseFloat(this.level2);
                const l3 = parseFloat(this.level3);
                const l4 = parseFloat(this.level4);
                const l5 = parseFloat(this.level5);
                const rawLevels = [this.level1, this.level2, this.level3, this.level4, this.level5];
                const parsedLevels = [l1, l2, l3, l4, l5];
                let hasInvalidLevel = false;
                parsedLevels.forEach((val, idx) => {
                    const currentRaw = rawLevels[idx];
                    if (isNaN(val)) {
                        hasInvalidLevel = true;
                        errors.push({
                            rowName: `Level ${idx + 1}`,
                            currentVal: currentRaw === "" ? "Trống" : `"${currentRaw}"`,
                            expected: "Phải là một số hợp lệ (Int hoặc Float)"
                        });
                    } else if (val <= 0) {
                        hasInvalidLevel = true;
                        errors.push({
                            rowName: `Level ${idx + 1}`,
                            currentVal: val,
                            expected: "Phải là số lớn hơn 0 (> 0)"
                        });
                    }
                });

                if (!hasInvalidLevel) {
                    if (!(l1 < l2)) {
                        errors.push({ rowName: "Level 2", currentVal: l2, expected: `Phải lớn hơn Level 1 (${l1})` });
                    }
                    if (!(l2 < l3)) {
                        errors.push({ rowName: "Level 3", currentVal: l3, expected: `Phải lớn hơn Level 2 (${l2})` });
                    }
                    if (!(l3 < l4)) {
                        errors.push({ rowName: "Level 4", currentVal: l4, expected: `Phải lớn hơn Level 3 (${l3})` });
                    }
                    if (!(l4 < l5)) {
                        errors.push({ rowName: "Level 5", currentVal: l5, expected: `Phải lớn hơn Level 4 (${l4})` });
                    }
                }

                const coords = {
                    xStart: this.xStart,
                    yStart: this.yStart,
                    xEnd: this.xEnd,
                    yEnd: this.yEnd
                };

                for (const [key, val] of Object.entries(coords)) {
                    const numVal = Number(val);
                    if (val === undefined || val === null || val === "" || isNaN(numVal) || !Number.isInteger(numVal)) {
                        errors.push({
                            rowName: `Tọa độ ${key}`,
                            currentVal: (val === "" || val === null || val === undefined) ? "Trống" : `"${val}"`,
                            expected: "Phải là một số nguyên (Integer)"
                        });
                    } else if (numVal <= 0) {
                        errors.push({
                            rowName: `Tọa độ ${key}`,
                            currentVal: numVal,
                            expected: "Phải là số nguyên lớn hơn 0 (> 0)"
                        });
                    }
                }

                return {
                    isValid: errors.length === 0,
                    errors: errors
                };
            }
    
            static fromDict(lineId, value) { // <-- Sửa nhận 2 tham số rõ ràng
                // console.log("lineId",lineId);
                // console.log("value",value);
                return new Measurement(
                    lineId,
                    value.name_line ?? "",
                    value.level1 ?? 0,
                    value.level2 ?? 0,
                    value.level3 ?? 0,
                    value.level4 ?? 0,
                    value.level5 ?? 0,
                    value.xStart ?? 0,
                    value.yStart ?? 0,
                    value.xEnd ?? 0,
                    value.yEnd ?? 0
                );
            }
}