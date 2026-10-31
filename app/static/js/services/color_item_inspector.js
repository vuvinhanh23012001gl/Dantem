import { ModelRectangle } from "../model/model_rectangle.js";
import { drawRoi, ROI_STYLE } from "../canvas/roi_style.js";

export class ColorItemInspector {
    static NAME = "ColorItemInspector";

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
                if (evalRes.status === "OK") {
                    strokeColor = "#00C853";
                    statusSuffix = ` [OK ΔE=${evalRes.delta_e00 ?? 0}]`;
                } else {
                    strokeColor = "#FF1744";
                    statusSuffix = ` [NG ΔE=${evalRes.delta_e00 ?? 0}]`;
                }
            }

            const active = rectangle.id === activeRoiId;
            drawRoi(context, rectangle, { active, color: strokeColor });
            context.save();
            if (active) strokeColor = ROI_STYLE.active;
            context.fillStyle = strokeColor;
            context.font = "bold 13px Arial";
            const baseName = rectangle.name || `Vùng màu ${Number(rectangle.id) + 1}`;
            context.fillText(
                `${baseName}${statusSuffix}`,
                rectangle.xStart + 4,
                Math.max(16, rectangle.yStart + 18),
            );

            // Vẽ ô màu mẫu swatch nhỏ ở góc trên bên phải khung (giống do_mau_roi.py)
            const rgb = evalRes?.measured_rgb || rectangle.ref_rgb;
            if (Array.isArray(rgb) && rgb.length === 3) {
                const swatchSize = 18;
                const swX = rectangle.xEnd - swatchSize - 2;
                const swY = rectangle.yStart + 2;
                if (swX > rectangle.xStart + 20) {
                    context.fillStyle = `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
                    context.fillRect(swX, swY, swatchSize, swatchSize);
                    context.strokeStyle = "#ffffff";
                    context.lineWidth = 1.5;
                    context.strokeRect(swX, swY, swatchSize, swatchSize);
                }
            }
            context.restore();
        }
    }

    toDict() {
        if (!this.rectangles.length) return null;
        const result = {};
        for (const rectangle of this.rectangles) {
            const data = rectangle.toDict();
            data.max_delta_e = rectangle.max_delta_e ?? 5.0;
            data.ref_rgb = rectangle.ref_rgb ?? [255, 255, 255];
            data.ref_lab = rectangle.ref_lab ?? null;
            result[String(rectangle.id)] = data;
        }
        return result;
    }

    static fromDict(data) {
        if (!data || typeof data !== "object") return new ColorItemInspector();
        const rectangles = [];

        const isSingleRect = ["xStart", "yStart", "xEnd", "yEnd"].every(k => k in data);
        if (isSingleRect) {
            const model = ModelRectangle.fromDict(data);
            model.id = Number.isFinite(Number(data.id)) && Number(data.id) >= 0 ? Number(data.id) : 0;
            if (!model.name) model.name = "Vùng màu 1";
            model.max_delta_e = data.max_delta_e ?? 5.0;
            model.ref_rgb = data.ref_rgb ?? [255, 255, 255];
            model.ref_lab = data.ref_lab ?? null;
            if (model.isValid()) rectangles.push(model);
            return new ColorItemInspector(rectangles);
        }

        for (const [key, value] of Object.entries(data)) {
            if (typeof value === "object" && value !== null) {
                const model = ModelRectangle.fromDict(value);
                model.id = Number(value?.id ?? key);
                model.max_delta_e = value.max_delta_e ?? 5.0;
                model.ref_rgb = value.ref_rgb ?? [255, 255, 255];
                model.ref_lab = value.ref_lab ?? null;
                if (model.isValid()) {
                    rectangles.push(model);
                }
            }
        }
        return new ColorItemInspector(rectangles);
    }
}
