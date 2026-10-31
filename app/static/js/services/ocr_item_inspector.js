import { ModelRectangle } from "../model/model_rectangle.js";
import { drawRoi, ROI_STYLE } from "../canvas/roi_style.js";
import { StampItemInspector } from "./stamp_item_inspector.js";

export class OCRItemInspector extends StampItemInspector {
    static NAME = "OCRTextInspector";

    toDict() {
        if (!this.rectangles.length) return null;
        const result = {};
        for (const rectangle of this.rectangles) {
            result[String(rectangle.id)] = {
                ...rectangle.toDict(),
                expected_text: String(rectangle.expected_text || ""),
            };
        }
        return result;
    }

    drawAll(canvasManager, color = ROI_STYLE.normal, activeRoiId = null) {
        canvasManager.clearShapeCanvas();
        const context = canvasManager.ctxShape;
        const resultById = new Map(
            (this.boxResults || [])
                .filter(result => result && result.id !== undefined && result.id !== null)
                .map(result => [String(result.id), result]),
        );

        for (const rectangle of this.rectangles) {
            const result = resultById.get(String(rectangle.id));
            const statusColor = result?.ok === true
                ? "#00C853"
                : result?.ok === false ? "#FF1744" : color;
            const active = rectangle.id === activeRoiId;
            drawRoi(context, rectangle, {
                active,
                color: active ? ROI_STYLE.active : statusColor,
            });
            context.save();
            context.fillStyle = active ? ROI_STYLE.active : statusColor;
            context.font = "bold 13px Arial";
            const name = rectangle.name || `OCR ${Number(rectangle.id) + 1}`;
            const suffix = result ? (result.ok ? " [OK]" : " [NG]") : "";
            context.fillText(
                `${name}${suffix}`,
                rectangle.xStart + 4,
                Math.max(16, rectangle.yStart + 18),
            );
            context.restore();
        }
    }

    static fromDict(data) {
        if (!data || typeof data !== "object") return new OCRItemInspector();
        const entries = ["xStart", "yStart", "xEnd", "yEnd"].every(key => key in data)
            ? [[String(data.id ?? 0), data]]
            : Object.entries(data);
        const rectangles = [];

        for (const [key, value] of entries) {
            if (!value || typeof value !== "object") continue;
            const rectangle = ModelRectangle.fromDict(value);
            rectangle.id = Number(value.id ?? key);
            rectangle.expected_text = String(value.expected_text ?? "");
            if (rectangle.isValid()) rectangles.push(rectangle);
        }
        return new OCRItemInspector(rectangles);
    }
}
