import { ModelRectangle } from "../model/model_rectangle.js";
import { drawRoi, ROI_STYLE } from "../canvas/roi_style.js";

export class StampReversedItemInspector {
    static NAME = "StampReversedInspector";

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
                    statusSuffix = " [OK]";
                } else {
                    strokeColor = "#FF1744";
                    const err = evalRes.error_code === "TEXT_REVERSED" ? " [NG-NGƯỢC]" : (evalRes.error_code === "TEXT_ROTATED" ? " [NG-XOAY]" : " [NG]");
                    statusSuffix = err;
                }
            }

            const active = rectangle.id === activeRoiId;
            drawRoi(context, rectangle, {active, color: strokeColor});
            context.save();
            if (active) strokeColor = ROI_STYLE.active;
            context.fillStyle = strokeColor;
            context.font = "bold 13px Arial";
            const baseName = rectangle.name || `Tem ngược ${Number(rectangle.id) + 1}`;
            context.fillText(
                `${baseName}${statusSuffix}`,
                rectangle.xStart + 4,
                Math.max(16, rectangle.yStart + 18),
            );

            // Vẽ polygon OBB nếu có từ kết quả model
            if (evalRes?.obb_polygon && Array.isArray(evalRes.obb_polygon) && evalRes.obb_polygon.length >= 4) {
                context.strokeStyle = evalRes.status === "OK" ? "#00E676" : "#FF1744";
                context.lineWidth = 2;
                context.beginPath();
                evalRes.obb_polygon.forEach((pt, pIdx) => {
                    if (pIdx === 0) context.moveTo(pt[0], pt[1]);
                    else context.lineTo(pt[0], pt[1]);
                });
                context.closePath();
                context.stroke();
            }

            context.restore();
        }
    }

    toDict() {
        if (!this.rectangles.length) return null;
        const result = {};
        for (const rectangle of this.rectangles) {
            const data = rectangle.toDict();
            data.max_deg = rectangle.max_deg !== undefined ? rectangle.max_deg : 15.0;
            result[String(rectangle.id)] = data;
        }
        return result;
    }

    static fromDict(data) {
        if (!data || typeof data !== "object") return new StampReversedItemInspector();
        const rectangles = [];

        const isSingleRect = ["xStart", "yStart", "xEnd", "yEnd"].every(k => k in data);
        if (isSingleRect) {
            const model = ModelRectangle.fromDict(data);
            model.id = Number.isFinite(Number(data.id)) && Number(data.id) >= 0 ? Number(data.id) : 0;
            if (!model.name) model.name = "Tem ngược 1";
            model.max_deg = data.max_deg !== undefined ? Number(data.max_deg) : 15.0;
            if (model.isValid()) rectangles.push(model);
            return new StampReversedItemInspector(rectangles);
        }

        for (const [key, value] of Object.entries(data)) {
            if (typeof value === "object" && value !== null) {
                const model = ModelRectangle.fromDict(value);
                model.id = Number(value?.id ?? key);
                model.max_deg = value.max_deg !== undefined ? Number(value.max_deg) : 15.0;
                if (!model.name) model.name = `Tem ngược ${model.id + 1}`;
                if (model.isValid()) {
                    rectangles.push(model);
                }
            }
        }
        return new StampReversedItemInspector(rectangles);
    }
}
