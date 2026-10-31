
/**
 * Kiểm tra một điểm có nằm trên đoạn thẳng hay không.
 *
 * @param {number} x1 Tọa độ X điểm đầu đoạn thẳng
 * @param {number} y1 Tọa độ Y điểm đầu đoạn thẳng
 * @param {number} x2 Tọa độ X điểm cuối đoạn thẳng
 * @param {number} y2 Tọa độ Y điểm cuối đoạn thẳng
 * @param {number} px Tọa độ X điểm cần kiểm tra
 * @param {number} py Tọa độ Y điểm cần kiểm tra
 * @param {number} tolerance Sai số cho phép (pixel)
 *
 * @returns {boolean}
 * true  -> điểm nằm trên đoạn thẳng
 * false -> điểm không nằm trên đoạn thẳng
 */

export function isPointOnLineSegment(x1, y1, x2, y2, px, py, tolerance = 10) {

    const dx = x2 - x1;
    const dy = y2 - y1;

    const length = Math.sqrt(dx * dx + dy * dy);
    if (length === 0) return false;

    // Khoảng cách thực sự từ điểm tới đường
    const distance = Math.abs(dy * px - dx * py + x2*y1 - y2*x1) / length;

    if (distance > tolerance) return false;

    const dot = (px - x1) * dx + (py - y1) * dy;

    if (dot < 0) return false;
    if (dot > dx * dx + dy * dy) return false;

    return true;
}

/**
 * Kiểm tra điểm click có nằm trên
 * bất kỳ đường thẳng nào không.
 *
 * @param {Array<Object>} lines Danh sách đường thẳng
 * @param {number} x Tọa độ X điểm click
 * @param {number} y Tọa độ Y điểm click
 *
 * @returns {boolean}
 */


export function drawTextOnLine(
    ctx, x1, y1, x2, y2,
    text,
    color = "yellow"
) {
    const midX = (x1 + x2) / 2;
    const midY = (y1 + y2) / 2;
    const angle = Math.atan2(y2 - y1, x2 - x1);
    ctx.save();
    ctx.translate(midX, midY);
    ctx.rotate(angle);
    ctx.font = "18px Arial";
    ctx.fillStyle = color;
    ctx.textAlign = "center";
    ctx.fillText(text, 0, -5);
    ctx.restore();
}

/**
     * Draw a transparent preview line on canvas.
     *
     * @param {CanvasRenderingContext2D} ctx Canvas context
     * @param {number} x1 Start point X
     * @param {number} y1 Start point Y
     * @param {number} x2 End point X
     * @param {number} y2 End point Y
     * @param {number} alpha Line transparency (0~1)
     * @param {string} color Line color
*/
export function drawTransparentLine(
    ctx, x1, y1, x2, y2,
    alpha = 0.3,
    color = "yellow"
) {

    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.restore();
}

export function drawPoint(
    ctx,
    x,
    y,
    radius = 3,
    color = "yellow"
) {
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
}