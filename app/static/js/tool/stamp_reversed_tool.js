import { ModelRectangle } from "../model/model_rectangle.js";
import { canvasManager, scroll_container, WIDTH_IMG_SHAPE } from "../common_value.js";
import { RectangleDrawer } from "../canvas/rectangel_drawer_canvas.js";
import { StampReversedItemInspector } from "../services/stamp_reversed_item_inspector.js";
import { ItemsInspector } from "../services/items_inspector.js";
import { postData } from "../utills/api.js";
import { drawRoi } from "../canvas/roi_style.js";
import { setRegionPanel, hideRegionEditor, closeRegionPanel } from "./region_tool_ui.js";
import {
    ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    COLOR_RECT_SHAPE_REGION_DETECT,
    additional_events,
    boxContentStampReversed,
    create_obj_cross_item,
    get_obj_product,
    obj_region_stamp_reversed_canvas,
    panner_region_stamp_reversed,
    refesh_btn,
    selected,
    setNameEventActivate,
    write_log_append,
    write_log_clear,
    tool_log,
    capture_log,
} from "./common_value_tool.js";

const EVENT_NAME = "stamp_reversed_tool";
const logStampReversed = tool_log(EVENT_NAME);
const closeButton = document.getElementById("btn-exit-stamp-reversed");
const judgmentButton = document.getElementById("btn-judment-stamp-reversed");
let activeRoiId = null;
let viewVersion = 0;

additional_events.set(EVENT_NAME, event_transition_items);

obj_region_stamp_reversed_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT,
    (rect) => openRectangleEditor(rect, true),
);
obj_region_stamp_reversed_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT_HAVE_ALREADY,
    selectStoredRectangle,
);
obj_region_stamp_reversed_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_RIGHT_RECT,
    removeStoredRectangle,
);

// Bọc onClick của RectangleDrawer để:
// Khi vẽ xong điểm thứ 2 -> TỰ ĐỘNG MỞ TRƯỢT PANEL NGAY LẬP TỨC (slideRightToLeft)
const origOnClick = obj_region_stamp_reversed_canvas.onClick.bind(obj_region_stamp_reversed_canvas);
obj_region_stamp_reversed_canvas.onClick = (pos, cm) => {
    const wasDrawing = obj_region_stamp_reversed_canvas.isDrawing;
    const hadUnsavedRect = obj_region_stamp_reversed_canvas.is_available_one_rect;
    origOnClick(pos, cm);

    const inspector = getInspector();
    if (!wasDrawing && obj_region_stamp_reversed_canvas.isDrawing) {
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_stamp_reversed, null);
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(cm, pos);
    }

    if (hadUnsavedRect && obj_region_stamp_reversed_canvas.isDrawing) {
        if (boxContentStampReversed) boxContentStampReversed.innerHTML = "";
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(cm, pos);
        return;
    }

    // Hoàn tất điểm thứ 2 của khung mới -> hiển thị khung tạm và TỰ ĐỘNG TRƯỢT PANEL MỞ RA
    if (wasDrawing && !obj_region_stamp_reversed_canvas.isDrawing && obj_region_stamp_reversed_canvas.is_available_one_rect) {
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawPendingRectangle(cm, obj_region_stamp_reversed_canvas.rect_current);
        openRectangleEditor(obj_region_stamp_reversed_canvas.rect_current, true);
    }
};

function drawStartPoint(cm, pos) {
    const ctx = cm.ctxShape;
    ctx.save();
    ctx.fillStyle = "#FF1744";
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
}

function drawPendingRectangle(cm, rect) {
    if (!rect || rect.width <= 0 || rect.height <= 0) return;
    drawRoi(cm.ctxShape, rect, { pending: true });
}

function getInspector() {
    return create_obj_cross_item(
        ItemsInspector.TYPE_STAMP_REVERSED,
        StampReversedItemInspector,
        "setStampReversedItems",
    );
}

function selectStoredRectangle(coordinate) {
    if (obj_region_stamp_reversed_canvas.isDrawing) return;
    if (obj_region_stamp_reversed_canvas.is_available_one_rect && obj_region_stamp_reversed_canvas.isPointOnRectBorder(
        obj_region_stamp_reversed_canvas.rect_current, coordinate.x, coordinate.y, ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE
    )) return;

    const inspector = getInspector();
    const rectangle = inspector?.findRectangleOnBorder(
        coordinate.x,
        coordinate.y,
        ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    );
    if (!rectangle) return;

    obj_region_stamp_reversed_canvas.reset();
    obj_region_stamp_reversed_canvas.have_return = true;
    activeRoiId = rectangle.id;
    viewVersion++;
    inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
    openRectangleEditor(rectangle, false);
}

function removeStoredRectangle(payload) {
    const inspector = getInspector();

    if (payload?.status_check_point_in_rect_current) {
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_stamp_reversed, null);
        if (boxContentStampReversed) boxContentStampReversed.innerHTML = "";
        inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        updateHighlight();
        write_log_clear(logStampReversed, "Đã hủy khung vừa vẽ.");
        return;
    }

    const rectangle = inspector?.findRectangleOnBorder(
        payload.x,
        payload.y,
        ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    );
    if (!rectangle) return;

    if (activeRoiId === rectangle.id) activeRoiId = null;
    viewVersion++;
    inspector.removeRectangle(rectangle.id);
    if (boxContentStampReversed) boxContentStampReversed.innerHTML = "";
    obj_region_stamp_reversed_canvas.reset();
    inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
    const activeRectangle = inspector.rectangles.find(item => item.id === activeRoiId);
    if (activeRectangle) openRectangleEditor(activeRectangle, false);
    else setRegionPanel(panner_region_stamp_reversed, null);
    updateHighlight();
    write_log_clear(logStampReversed, `Đã xóa khung "${rectangle.name}".`);
}

function createConfigRow(labelText, inputElement) {
    const tr = document.createElement("tr");
    tr.className = "config-row";
    const th = document.createElement("th");
    th.className = "config-label";
    th.textContent = labelText;
    const td = document.createElement("td");
    td.className = "config-value";
    td.appendChild(inputElement);
    tr.append(th, td);
    return tr;
}

function openRectangleEditor(rectangle, isNewPending = false) {
    if (!rectangle || rectangle.xStart < 0 || !boxContentStampReversed) return;
    const inspector = getInspector();
    if (!inspector) return;
    activeRoiId = isNewPending ? null : rectangle.id;

    // Tự động kích hoạt hiệu ứng trượt Panel từ phải sang trái (slideRightToLeft)
    setRegionPanel(panner_region_stamp_reversed, isNewPending ? "pending" : activeRoiId, !isNewPending);

    boxContentStampReversed.innerHTML = "";
    const wrapper = document.createElement("div");
    wrapper.className = "region-editor";

    const table = document.createElement("table");
    table.className = "measure-weld-width-config-table";

    // 1. Tên khung
    const inputName = document.createElement("input");
    inputName.id = "stamp-reversed-roi-name";
    inputName.type = "text";
    inputName.className = "config-input";
    inputName.placeholder = "Ví dụ: Tem ngược 1";
    inputName.value = rectangle.name || `Tem ngược ${inspector.getNextId() + 1}`;

    // 2. Δθ max (độ xoay cho phép)
    const inpDeg = document.createElement("input");
    inpDeg.type = "number";
    inpDeg.step = "1";
    inpDeg.className = "config-input";
    inpDeg.value = rectangle.max_deg !== undefined ? rectangle.max_deg : 15.0;

    table.append(
        createConfigRow(isNewPending ? "Tên khung mới" : "Tên khung", inputName),
        createConfigRow("Δθ max (°)", inpDeg),
    );
    wrapper.appendChild(table);

    // Nút Lưu và Hủy
    const actions = document.createElement("div");
    actions.className = "config-actions";

    const acceptButton = document.createElement("button");
    acceptButton.type = "button";
    acceptButton.className = "btn btn-accept";
    acceptButton.textContent = "Chấp nhận";

    const cancelButton = document.createElement("button");
    cancelButton.type = "button";
    cancelButton.className = "btn btn-clear";
    cancelButton.textContent = "Hủy";

    const handleAccept = () => {
        const name = inputName.value.trim();
        if (!name) {
            write_log_clear(logStampReversed, "❌ Tên khung kiểm tra tem in ngược không được để trống.");
            inputName.focus();
            return;
        }
        const id = Number.isInteger(rectangle.id) && rectangle.id >= 0
            ? rectangle.id
            : inspector.getNextId();
        const model = new ModelRectangle(
            id,
            name,
            rectangle.xStart,
            rectangle.yStart,
            rectangle.xEnd,
            rectangle.yEnd,
        );
        model.max_deg = parseFloat(inpDeg.value) || 15.0;

        if (!model.isValid() || !inspector.addRectangle(model)) {
            write_log_clear(logStampReversed, "❌ Dữ liệu khung hình chữ nhật không hợp lệ.");
            return;
        }
        boxContentStampReversed.innerHTML = "";
        obj_region_stamp_reversed_canvas.reset();
        activeRoiId = model.id;
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        openRectangleEditor(model, false);
        hideRegionEditor(panner_region_stamp_reversed);
        updateHighlight();
        write_log_clear(
            logStampReversed,
            `✅ Đã lưu khung "${name}" (Dung sai xoay: Δθ=±${model.max_deg}°). Có thể tiếp tục vẽ khung mới.`,
        );
    };

    const handleCancel = () => {
        boxContentStampReversed.innerHTML = "";
        obj_region_stamp_reversed_canvas.reset();
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_stamp_reversed, null);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        updateHighlight();
        write_log_clear(
            logStampReversed,
            isNewPending ? "Đã hủy khung vừa vẽ." : "Đã hủy chỉnh sửa cấu hình khung.",
        );
    };

    acceptButton.addEventListener("click", handleAccept);
    cancelButton.addEventListener("click", handleCancel);

    inputName.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            handleAccept();
        } else if (event.key === "Escape") {
            event.preventDefault();
            handleCancel();
        }
    });

    actions.append(acceptButton, cancelButton);
    wrapper.append(actions);
    boxContentStampReversed.appendChild(wrapper);

    requestAnimationFrame(() => {
        inputName.focus();
        inputName.select();
    });
}

function updateHighlight() {
    get_obj_product()?.highlightItems(
        scroll_container,
        ItemsInspector.TYPE_STAMP_REVERSED,
        "rectangles",
    );
}

function renderStampReversedResultSummary(data = {}) {
    if (!boxContentStampReversed) return;
    boxContentStampReversed.innerHTML = "";

    const boxResults = Array.isArray(data.boxes) ? data.boxes : [];
    if (!boxResults.length) return;

    const allOk = boxResults.every(item => item.status === "OK");
    const statusColor = allOk ? "#00c853" : "#d50000";
    const statusBg = allOk ? "#e8f5e9" : "#ffebee";

    const wrapper = document.createElement("div");
    wrapper.style.padding = "6px";
    wrapper.style.display = "flex";
    wrapper.style.flexDirection = "column";
    wrapper.style.gap = "6px";

    // Badge tổng quan
    const badge = document.createElement("div");
    badge.style.display = "flex";
    badge.style.alignItems = "center";
    badge.style.justifyContent = "space-between";
    badge.style.padding = "6px 10px";
    badge.style.borderRadius = "8px";
    badge.style.fontWeight = "bold";
    badge.style.fontSize = "12px";
    badge.style.backgroundColor = statusBg;
    badge.style.color = statusColor;
    badge.style.border = `1.5px solid ${statusColor}`;

    const okCount = boxResults.filter(item => item.status === "OK").length;
    const titleSpan = document.createElement("span");
    titleSpan.textContent = allOk ? "✓ KẾT QUẢ: ĐẠT (OK)" : "✗ KẾT QUẢ: PHÁT HIỆN LỖI (NG)";
    const subSpan = document.createElement("span");
    subSpan.style.fontSize = "11px";
    subSpan.textContent = `${okCount}/${boxResults.length} khung đạt`;
    badge.append(titleSpan, subSpan);
    wrapper.appendChild(badge);

    // Bảng chi tiết: Khung -> Hướng chữ -> Góc tem OBB -> Chữ nhận diện -> Kết quả
    const table = document.createElement("table");
    table.className = "stamp-reversed-summary-table";

    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    ["Khung", "Hướng chữ", "Góc tem OBB", "Chữ nhận diện", "Kết quả"].forEach((headerText) => {
        const th = document.createElement("th");
        th.textContent = headerText;
        headerRow.appendChild(th);
    });

    const tbody = table.createTBody();
    boxResults.forEach((box, idx) => {
        const row = tbody.insertRow();
        const isOk = box.status === "OK";

        // 1. Tên khung (in đậm)
        const cellName = row.insertCell();
        cellName.textContent = box.name || `Tem ngược ${idx + 1}`;
        cellName.style.setProperty("font-weight", "bold", "important");
        cellName.style.setProperty("color", "#1a202c", "important");
        cellName.style.setProperty("text-align", "left", "important");
        cellName.style.setProperty("padding-left", "8px", "important");

        // 2. Hướng chữ (0°: Xanh, 180°: Đỏ, khác: Vàng)
        const cellTextOri = row.insertCell();
        const textAngle = box.text_angle !== undefined ? `${box.text_angle}°` : "---";
        cellTextOri.textContent = box.text_angle === 0 ? "0° (Thuận)" : (box.text_angle === 180 ? "180° (Ngược)" : `${textAngle}`);
        cellTextOri.style.setProperty("font-weight", "bold", "important");
        cellTextOri.style.setProperty("color", box.text_angle === 0 ? "#00c853" : "#d50000", "important");

        // 3. Góc tem OBB
        const cellObb = row.insertCell();
        cellObb.textContent = box.obb_detected ? `${box.obb_angle}°` : "Không rõ";
        cellObb.style.setProperty("color", "#2c3e50", "important");

        // 4. Chữ nhận diện
        const cellText = row.insertCell();
        cellText.textContent = box.text_preview || "(Không phát hiện)";
        cellText.style.setProperty("font-size", "11px", "important");
        cellText.style.setProperty("color", "#37474f", "important");

        // 5. Kết quả (OK: xanh, NG: đỏ, UNKNOWN: cam)
        const cellStatus = row.insertCell();
        cellStatus.textContent = box.status;
        cellStatus.style.setProperty("font-weight", "bold", "important");
        const statusColors = { "OK": "#00c853", "NG": "#d50000", "UNKNOWN": "#ff9800" };
        cellStatus.style.setProperty("color", statusColors[box.status] || "#d50000", "important");
    });

    wrapper.appendChild(table);
    boxContentStampReversed.appendChild(wrapper);
}

judgmentButton?.addEventListener("click", async () => {
    const version = viewVersion;
    const logStampRev = capture_log(tool_log(EVENT_NAME), () =>
        version === viewVersion && canvasManager.currentTool === obj_region_stamp_reversed_canvas);
    const inspector = getInspector();
    const region = inspector?.rectangles.find(rect => rect.id === activeRoiId);
    if (!selected || selected.product_id < 0 || selected.frame_id < 0 || selected.items_id < 0) {
        write_log_clear(logStampRev, "❌ Chưa chọn đầy đủ sản phẩm, frame và item.");
        return;
    }
    if (!region) {
        write_log_clear(logStampRev, "⚠️ Hãy chọn một khung kiểm tra tem in ngược đã chấp nhận trên ảnh.");
        return;
    }

    write_log_clear(logStampRev, "⏳ Đang chạy model AI kiểm tra hướng tem và hướng chữ in...");
    try {
        const payload = {
            select: { ...selected },
            boxes: [region.toDict()],
            WidthCanvas: WIDTH_IMG_SHAPE,
        };
        const result = await postData("/law_regulation/stamp_reversed/run_model", payload);
        if (version !== viewVersion || canvasManager.currentTool !== obj_region_stamp_reversed_canvas) return;
        if (!result?.ok) {
            write_log_clear(logStampRev, `❌ Phán định thất bại: ${result?.message || "Lỗi không xác định"}`);
            return;
        }

        const data = result.data || {};
        const boxResults = Array.isArray(data.boxes) ? data.boxes : [];

        obj_region_stamp_reversed_canvas.reset();
        inspector.setDetectionResults([], boxResults);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        renderStampReversedResultSummary(data);

        const ngBoxes = boxResults.filter(item => item.status !== "OK");

        if (ngBoxes.length === 0) {
            const firstBox = boxResults[0];
            write_log_clear(
                logStampRev,
                `✅ Phán định OK: Khung "${region.name}" in đúng chiều (Hướng chữ=${firstBox?.text_angle}°, OBB tem=${firstBox?.obb_angle}°).`,
            );
        } else {
            write_log_clear(
                logStampRev,
                `❌ Phán định NG: Phát hiện tem in ngược/lỗi tại ${ngBoxes.length}/${boxResults.length} khung:`,
            );
            ngBoxes.forEach((box) => {
                write_log_append(
                    logStampRev,
                    ` - [Kiểm tra tem in ngược] ${box.status} - Khung "${box.name}": ${box.message}`,
                );
            });
        }
    } catch (error) {
        write_log_clear(logStampRev, `❌ Lỗi kết nối API kiểm tra tem in ngược: ${error.message}`);
    }
});

export function event_transition_items() {
    activeRoiId = null;
    viewVersion++;
    setRegionPanel(panner_region_stamp_reversed, null);
    if (boxContentStampReversed) boxContentStampReversed.innerHTML = "";
    obj_region_stamp_reversed_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();

    const inspector = getInspector();
    inspector?.removeBoxs();
    inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
    updateHighlight();
    write_log_clear(
        logStampReversed,
        "Vẽ 2 điểm trên ảnh để tạo khung kiểm tra tem in ngược. Khung vẽ xong sẽ tự động trượt mở panel cấu hình.",
    );
}

closeButton?.addEventListener("click", async () => {
    activeRoiId = null;
    viewVersion++;
    obj_region_stamp_reversed_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();
    canvasManager.setTool(null);
    refesh_btn();
    get_obj_product()?.clearHighlight(scroll_container);
    setNameEventActivate(null);
    if (await closeRegionPanel(panner_region_stamp_reversed)) {
        if (boxContentStampReversed) boxContentStampReversed.innerHTML = "";
    }
});
