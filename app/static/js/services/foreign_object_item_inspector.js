import { ModelRectangle } from "../model/model_rectangle.js";
import { drawRoi, ROI_STYLE } from "../canvas/roi_style.js";

export class ForeignObjectRegion extends ModelRectangle {
    constructor(id = 0, name = "", xStart = -1, yStart = -1, xEnd = -1, yEnd = -1,
        saveRuntimeImages = false) {
        super(Number(id), name || `Dị vật ${Number(id) + 1}`,
            Number(xStart), Number(yStart), Number(xEnd), Number(yEnd));
        this.saveRuntimeImages = saveRuntimeImages === true;
    }

    isValid() {
        return super.isValid() && Number.isSafeInteger(this.id) && this.id >= 0 &&
            [this.xStart, this.yStart, this.xEnd, this.yEnd].every(Number.isFinite) &&
            this.xStart >= 0 && this.yStart >= 0 &&
            this.xEnd > this.xStart && this.yEnd > this.yStart;
    }

    toDict() {
        return {
            ...super.toDict(),
            saveRuntimeImages: this.saveRuntimeImages,
        };
    }

    static fromDict(data) {
        // Legacy thresholds are ignored; YOLO detections determine the verdict.
        const rect = ModelRectangle.fromDict(data);
        return new ForeignObjectRegion(rect.id, rect.name, rect.xStart, rect.yStart,
            rect.xEnd, rect.yEnd, data.saveRuntimeImages);
    }
}

export class ForeignObjectInspector {
    static NAME = "ForeignObjectInspector";

    constructor() {
        this.regions = [];
        this.nextId = 0;
    }

    addOrUpdateRegion(region) {
        if (!(region instanceof ForeignObjectRegion) || !region.isValid()) {
            throw new Error("Vùng dị vật không hợp lệ.");
        }
        const index = this.regions.findIndex(item => item.id === region.id);
        if (index < 0) this.regions.push(region);
        else this.regions[index] = region;
        this.nextId = Math.max(this.nextId, region.id + 1);
    }

    getNextId() {
        return this.nextId;
    }

    getRegionById(id) {
        if (id === null || id === undefined) return null;
        return this.regions.find(region => region.id === Number(id)) || null;
    }

    removeRegion(id) {
        const index = this.regions.findIndex(region => region.id === Number(id));
        if (index < 0) return false;
        this.regions.splice(index, 1);
        return true;
    }

    findRegionOnBorder(px, py, offset = 5) {
        return [...this.regions].reverse().find(region => {
            const withinX = px >= region.xStart - offset && px <= region.xEnd + offset;
            const withinY = py >= region.yStart - offset && py <= region.yEnd + offset;
            return (withinX && (Math.abs(py - region.yStart) <= offset ||
                Math.abs(py - region.yEnd) <= offset)) ||
                (withinY && (Math.abs(px - region.xStart) <= offset ||
                Math.abs(px - region.xEnd) <= offset));
        }) || null;
    }

    drawAll(canvasManager, defaultColor = ROI_STYLE.normal, activeRoiId = null) {
        canvasManager.clearShapeCanvas();
        const ctx = canvasManager.ctxShape;
        for (const region of this.regions) {
            const active = region.id === activeRoiId;
            drawRoi(ctx, region, {active, color: defaultColor});
            ctx.save();
            ctx.fillStyle = active ? ROI_STYLE.active : defaultColor;
            ctx.font = "bold 13px Arial";
            ctx.fillText(region.name, region.xStart + 4, region.yStart + 16);
            ctx.restore();
        }
    }

    toDict() {
        return this.regions.length
            ? Object.fromEntries(this.regions.map(region => [region.id, region.toDict()]))
            : null;
    }

    static fromDict(data) {
        const inspector = new ForeignObjectInspector();
        if (!data) return inspector;
        const legacy = "xStart" in data || "x_start" in data;
        const entries = legacy ? [["0", { ...data, id: 0 }]] : Object.entries(data);
        for (const [id, region] of entries) {
            inspector.addOrUpdateRegion(ForeignObjectRegion.fromDict({ ...region, id: region.id ?? id }));
        }
        return inspector;
    }
}
