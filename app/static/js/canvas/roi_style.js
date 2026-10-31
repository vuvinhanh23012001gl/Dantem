export const ROI_STYLE = Object.freeze({
    normal: "#0000FF",
    active: "#FFD600",
    pending: "#00B0FF",
    dash: [6, 4],
});

export function drawRoi(context, rectangle, {active = false, pending = false, color = ROI_STYLE.normal} = {}) {
    context.save();
    context.strokeStyle = pending ? ROI_STYLE.pending : active ? ROI_STYLE.active : color;
    context.lineWidth = active ? 3 : 2;
    context.setLineDash(active || pending ? ROI_STYLE.dash : []);
    context.strokeRect(rectangle.xStart, rectangle.yStart, rectangle.width, rectangle.height);
    if (active) {
        context.fillStyle = "rgba(255, 214, 0, 0.08)";
        context.fillRect(rectangle.xStart, rectangle.yStart, rectangle.width, rectangle.height);
    }
    context.restore();
}
