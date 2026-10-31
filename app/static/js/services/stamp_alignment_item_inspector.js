import { ModelRectangle } from "../model/model_rectangle.js";
import { drawRoi, ROI_STYLE } from "../canvas/roi_style.js";

export class StampAlignmentItemInspector {
    static NAME = "StampAlignmentInspector";

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
            this.drawDetectedOBBs(canvasManager);
        }
    }

    drawDetectedOBBs(canvasManager) {
        if (!this.boxs?.length) return;
        const context = canvasManager.ctxShape;
        const canvasWidth = canvasManager.canvasWidth || 1024;

        for (const obj of this.boxs) {
            const corners = obj.corners;
            if (!corners || corners.length < 4) continue;
            const imgWidth = obj.image_width || 2048;
            const scale = canvasWidth / imgWidth;

            context.save();
            context.beginPath();
            const startX = corners[0][0] * scale;
            const startY = corners[0][1] * scale;
            context.moveTo(startX, startY);
            for (let i = 1; i < corners.length; i++) {
                context.lineTo(corners[i][0] * scale, corners[i][1] * scale);
            }
            context.closePath();

            context.strokeStyle = obj.color || "#00E676";
            context.lineWidth = 2.5;
            context.stroke();

            // Nhãn hiển thị OBB
            const label = obj.type === "obb_frame" ? "Khung" : "Tem";
            context.fillStyle = obj.color || "#00E676";
            context.font = "bold 11px Arial";
            context.fillText(label, startX, Math.max(12, startY - 4));

            // Vẽ vector độ lệch tâm (nếu có)
            if (obj.center_vector && obj.center_vector.start && obj.center_vector.end) {
                const sx = obj.center_vector.start[0] * scale;
                const sy = obj.center_vector.start[1] * scale;
                const ex = obj.center_vector.end[0] * scale;
                const ey = obj.center_vector.end[1] * scale;

                // Tâm Khung
                context.fillStyle = "#00E676";
                context.beginPath();
                context.arc(sx, sy, 3.5, 0, Math.PI * 2);
                context.fill();

                // Tâm Tem
                context.fillStyle = obj.is_ok ? "#2979FF" : "#FF1744";
                context.beginPath();
                context.arc(ex, ey, 3.5, 0, Math.PI * 2);
                context.fill();

                // Mũi tên vector lệch
                context.strokeStyle = "#FF9100";
                context.lineWidth = 2;
                context.setLineDash([4, 2]);
                context.beginPath();
                context.moveTo(sx, sy);
                context.lineTo(ex, ey);
                context.stroke();
                context.setLineDash([]);
            }
            context.restore();
        }
    }

    toDict() {
        if (!this.rectangles.length) return null;
        const result = {};
        for (const rectangle of this.rectangles) {
            const data = rectangle.toDict();
            data.max_du = rectangle.max_du ?? 15.0;
            data.max_dv = rectangle.max_dv ?? 15.0;
            data.max_deg = rectangle.max_deg ?? 3.0;
            data.margin = rectangle.margin ?? 5.0;
            result[String(rectangle.id)] = data;
        }
        return result;
    }

    static fromDict(data) {
        if (!data || typeof data !== "object") return new StampAlignmentItemInspector();
        const rectangles = [];

        const isSingleRect = ["xStart", "yStart", "xEnd", "yEnd"].every(k => k in data);
        if (isSingleRect) {
            const model = ModelRectangle.fromDict(data);
            model.id = Number.isFinite(Number(data.id)) && Number(data.id) >= 0 ? Number(data.id) : 0;
            if (!model.name) model.name = "Tem 1";
            model.max_du = data.max_du ?? 15.0;
            model.max_dv = data.max_dv ?? 15.0;
            model.max_deg = data.max_deg ?? 3.0;
            model.margin = data.margin ?? 5.0;
            if (model.isValid()) rectangles.push(model);
            return new StampAlignmentItemInspector(rectangles);
        }

        for (const [key, value] of Object.entries(data)) {
            if (typeof value === "object" && value !== null) {
                const model = ModelRectangle.fromDict(value);
                model.id = Number(value?.id ?? key);
                model.max_du = value.max_du ?? 15.0;
                model.max_dv = value.max_dv ?? 15.0;
                model.max_deg = value.max_deg ?? 3.0;
                model.margin = value.margin ?? 5.0;
                if (model.isValid()) {
                    rectangles.push(model);
                }
            }
        }
        return new StampAlignmentItemInspector(rectangles);
    }
}
