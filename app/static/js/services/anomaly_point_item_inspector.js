import { ModelRectangle } from "../model/model_rectangle.js";
import { drawRoi, ROI_STYLE } from "../canvas/roi_style.js";

export class AnomalyPointRegion {
    constructor(
        id = 0,
        name = "",
        xStart = -1,
        yStart = -1,
        xEnd = -1,
        yEnd = -1,
        threshold = 0.2,
        saveRuntimeImages = false,
    ) {
        this.id = Number(id) || 0;
        this.name = name || `Điểm bất thường ${this.id + 1}`;
        this.xStart = Number(xStart);
        this.yStart = Number(yStart);
        this.xEnd = Number(xEnd);
        this.yEnd = Number(yEnd);
        this.width = Math.abs(this.xEnd - this.xStart);
        this.height = Math.abs(this.yEnd - this.yStart);
        const numericThreshold = Number(threshold);
        this.threshold =
            Number.isFinite(numericThreshold) && numericThreshold >= 0 && numericThreshold <= 1
                ? numericThreshold
                : 0.2;
        this.saveRuntimeImages = Boolean(saveRuntimeImages);
    }

    isValid() {
        return (
            this.xStart >= 0 &&
            this.yStart >= 0 &&
            this.xEnd > this.xStart &&
            this.yEnd > this.yStart &&
            this.width > 0 &&
            this.height > 0 &&
            Boolean(this.name && this.name.trim())
        );
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
            height: this.height,
            threshold: this.threshold,
            saveRuntimeImages: this.saveRuntimeImages,
        };
    }

    static fromDict(data) {
        if (!data || typeof data !== "object") return new AnomalyPointRegion();
        const id = Number(data.id) >= 0 ? Number(data.id) : 0;
        const name = data.name || `Điểm bất thường ${id + 1}`;
        let xStart = Number(data.xStart ?? data.x_start ?? -1);
        let yStart = Number(data.yStart ?? data.y_start ?? -1);
        let xEnd = Number(data.xEnd ?? data.x_end ?? -1);
        let yEnd = Number(data.yEnd ?? data.y_end ?? -1);
        if (xEnd === -1 && data.width && xStart !== -1) {
            xEnd = xStart + Number(data.width);
        }
        if (yEnd === -1 && data.height && yStart !== -1) {
            yEnd = yStart + Number(data.height);
        }
        const rawThreshold = data.threshold ?? data.thresholdNG;
        const numericThreshold = Number(rawThreshold);
        const threshold =
            Number.isFinite(numericThreshold) && numericThreshold >= 0 && numericThreshold <= 1
                ? numericThreshold
                : 0.2;
        const saveRuntime = data.saveRuntimeImages === true;
        return new AnomalyPointRegion(id, name, xStart, yStart, xEnd, yEnd, threshold, saveRuntime);
    }
}


export class AnomalyPointInspector {
    static NAME = "AnomalyPointInspector";

    constructor(regions = []) {
        /** @type {AnomalyPointRegion[]} Danh sách các vùng kiểm tra bất thường trên item */
        this.regions = Array.isArray(regions) ? regions : [];
    }

    addOrUpdateRegion(region) {
        if (!region || !(region instanceof AnomalyPointRegion)) return false;
        const index = this.regions.findIndex(r => r.id === region.id);
        if (index >= 0) {
            this.regions[index] = region;
        } else {
            this.regions.push(region);
        }
        return true;
    }

    getNextId() {
        if (!this.regions.length) return 0;
        return Math.max(...this.regions.map(r => Number(r.id) || 0)) + 1;
    }

    getRegionById(id) {
        const numId = Number(id);
        return this.regions.find(r => r.id === numId) || null;
    }

    findRegionOnBorder(px, py, offset = 10) {
        for (let i = this.regions.length - 1; i >= 0; i--) {
            const r = this.regions[i];
            const nearHorizontal = px >= r.xStart - offset && px <= r.xEnd + offset;
            const nearVertical = py >= r.yStart - offset && py <= r.yEnd + offset;
            if (
                (Math.abs(py - r.yStart) <= offset && nearHorizontal) ||
                (Math.abs(py - r.yEnd) <= offset && nearHorizontal) ||
                (Math.abs(px - r.xStart) <= offset && nearVertical) ||
                (Math.abs(px - r.xEnd) <= offset && nearVertical)
            ) {
                return r;
            }
        }
        return null;
    }

    removeRegion(id) {
        const numId = Number(id);
        const index = this.regions.findIndex(r => r.id === numId);
        if (index < 0) return false;
        this.regions.splice(index, 1);
        return true;
    }

    clear() {
        this.regions = [];
    }

    drawAll(canvasManager, defaultColor = ROI_STYLE.normal, activeRoiId = null) {
        canvasManager.clearShapeCanvas();
        const ctx = canvasManager.ctxShape;

        for (const region of this.regions) {
            const isActive = activeRoiId !== null && Number(activeRoiId) === Number(region.id);
            const strokeColor = isActive ? ROI_STYLE.active : defaultColor;
            drawRoi(ctx, region, {active: isActive, color: defaultColor});
            ctx.save();
            ctx.fillStyle = strokeColor;
            ctx.font = "bold 13px Arial";
            const labelText = `${region.name} (<= ${region.threshold.toFixed(2)})`;
            ctx.fillText(
                labelText,
                region.xStart + 4,
                Math.max(16, region.yStart + 16),
            );
            ctx.restore();
        }
    }

    toDict() {
        if (!this.regions.length) return null;
        const result = {};
        for (const region of this.regions) {
            result[String(region.id)] = region.toDict();
        }
        return result;
    }

    static fromDict(data) {
        if (!data || typeof data !== "object") return new AnomalyPointInspector();
        const regions = [];

        // Hỗ trợ cả định dạng đơn khung cũ (EndChipping legacy)
        const isSingleRect = ["xStart", "yStart", "xEnd", "yEnd"].every(k => k in data);
        if (isSingleRect) {
            const reg = AnomalyPointRegion.fromDict(data);
            if (reg.isValid()) regions.push(reg);
            return new AnomalyPointInspector(regions);
        }

        // Định dạng đa khung {"0": {...}, "1": {...}}
        for (const [key, value] of Object.entries(data)) {
            if (typeof value === "object" && value !== null) {
                const reg = AnomalyPointRegion.fromDict({
                    ...value,
                    id: value.id !== undefined ? value.id : key,
                });
                if (reg.isValid()) {
                    regions.push(reg);
                }
            }
        }
        return new AnomalyPointInspector(regions);
    }
}
