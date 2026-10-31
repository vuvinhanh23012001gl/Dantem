import { ModelRectangle } from "../model/model_rectangle.js";
import { drawRoi, ROI_STYLE } from "../canvas/roi_style.js";


export class StampItemInspector {
    static NAME = "StampItemInspector";

    constructor(rectangles = []) {
        this.rectangles = Array.isArray(rectangles) ? rectangles : [];
        this.boxs = [];
        this.boxResults = [];
    }

    addRectangle(rectangle) {
        if (!(rectangle instanceof ModelRectangle)) return false;
        const index = this.rectangles.findIndex(item => item.id === rectangle.id);
        if (index >= 0) this.rectangles[index] = rectangle;
        else this.rectangles.push(rectangle);
        this.removeBoxs();
        return true;
    }

    getNextId() {
        if (!this.rectangles.length) return 0;
        return Math.max(...this.rectangles.map(item => Number(item.id) || 0)) + 1;
    }

    findRectangleOnBorder(px, py, offset = 10) {
        for (let index = this.rectangles.length - 1; index >= 0; index--) {
            const rectangle = this.rectangles[index];
            const nearHorizontal = px >= rectangle.xStart - offset && px <= rectangle.xEnd + offset;
            const nearVertical = py >= rectangle.yStart - offset && py <= rectangle.yEnd + offset;
            if (
                (Math.abs(py - rectangle.yStart) <= offset && nearHorizontal) ||
                (Math.abs(py - rectangle.yEnd) <= offset && nearHorizontal) ||
                (Math.abs(px - rectangle.xStart) <= offset && nearVertical) ||
                (Math.abs(px - rectangle.xEnd) <= offset && nearVertical)
            ) return rectangle;
        }
        return null;
    }

    removeRectangle(id) {
        const index = this.rectangles.findIndex(item => item.id === id);
        if (index < 0) return false;
        this.rectangles.splice(index, 1);
        this.removeBoxs();
        return true;
    }

    clear() {
        this.rectangles = [];
        this.removeBoxs();
    }

    setDetectionResults(objects = [], boxResults = []) {
        this.boxs = Array.isArray(objects) ? [...objects] : [];
        this.boxResults = Array.isArray(boxResults) ? [...boxResults] : [];
    }

    removeBoxs() {
        this.boxs = [];
        this.boxResults = [];
    }

    drawAll(canvasManager, color = ROI_STYLE.normal, activeRoiId = null) {
        canvasManager.clearShapeCanvas();
        const context = canvasManager.ctxShape;

        const resultById = new Map();
        for (const res of this.boxResults || []) {
            if (res && res.id !== undefined && res.id !== null) {
                resultById.set(String(res.id), res);
            }
        }

        for (const rectangle of this.rectangles) {
            const evalRes = resultById.get(String(rectangle.id));
            let strokeColor = color;
            let statusSuffix = "";
            if (evalRes) {
                if (evalRes.exists === true) {
                    strokeColor = "#00C853";
                    statusSuffix = " [OK]";
                } else if (evalRes.exists === false) {
                    strokeColor = "#FF1744";
                    statusSuffix = " [NG]";
                }
            }

            const active = rectangle.id === activeRoiId;
            drawRoi(context, rectangle, {active, color: strokeColor});
            context.save();
            if (active) strokeColor = ROI_STYLE.active;
            context.fillStyle = strokeColor;
            context.font = "bold 13px Arial";
            const baseName = rectangle.name || `Tem ${Number(rectangle.id) + 1}`;
            context.fillText(
                `${baseName}${statusSuffix}`,
                rectangle.xStart + 4,
                Math.max(16, rectangle.yStart + 18),
            );
            context.restore();
        }

        if (this.boxs && this.boxs.length > 0) {
            this.drawDetectedObjects(canvasManager);
        }
    }

    drawDetectedObjects(canvasManager, color = "#FF9100") {
        if (!this.boxs?.length) return;
        const context = canvasManager.ctxShape;
        for (const object of this.boxs) {
            const bbox = object.bbox;
            if (!bbox) continue;
            const scale = (object.canvasWidth || canvasManager.canvasWidth || 1024)
                / (object.image_width || 2048);
            const x = bbox.x1 * scale;
            const y = bbox.y1 * scale;
            const width = (bbox.x2 - bbox.x1) * scale;
            const height = (bbox.y2 - bbox.y1) * scale;

            context.save();
            context.strokeStyle = color;
            context.lineWidth = 2;
            context.strokeRect(x, y, width, height);

            context.fillStyle = color;
            context.font = "bold 12px Arial";
            const confText = ` (${((object.confidence || 0) * 100).toFixed(1)}%)`;
            context.fillText(
                `${object.class_name || "stamp"}${confText}`,
                x + 4,
                Math.max(14, y - 4),
            );
            context.restore();
        }
    }

    toDict() {
        if (!this.rectangles.length) return null;
        const result = {};
        for (const rectangle of this.rectangles) {
            result[String(rectangle.id)] = rectangle.toDict();
        }
        return result;
    }

    static fromDict(data) {
        if (!data || typeof data !== "object") return new StampItemInspector();
        const rectangles = [];

        // Hỗ trợ cả định dạng đa khung {"0": {...}, "1": {...}} và định dạng đơn khung cũ
        const isSingleRect = ["xStart", "yStart", "xEnd", "yEnd"].every(k => k in data);
        if (isSingleRect) {
            const model = ModelRectangle.fromDict(data);
            model.id = Number.isFinite(Number(data.id)) && Number(data.id) >= 0 ? Number(data.id) : 0;
            if (!model.name) model.name = "Tem 1";
            if (model.isValid()) rectangles.push(model);
            return new StampItemInspector(rectangles);
        }

        for (const [key, value] of Object.entries(data)) {
            if (typeof value === "object" && value !== null) {
                const model = ModelRectangle.fromDict(value);
                model.id = Number(value?.id ?? key);
                if (model.isValid()) {
                    rectangles.push(model);
                }
            }
        }
        return new StampItemInspector(rectangles);
    }
}
