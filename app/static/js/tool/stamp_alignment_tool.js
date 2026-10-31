import { ModelRectangle } from "../model/model_rectangle.js";
import { canvasManager, scroll_container, WIDTH_IMG_SHAPE } from "../common_value.js";
import { RectangleDrawer } from "../canvas/rectangel_drawer_canvas.js";
import { StampAlignmentItemInspector } from "../services/stamp_alignment_item_inspector.js";
import { ItemsInspector } from "../services/items_inspector.js";
import { postData } from "../utills/api.js";
import { drawRoi } from "../canvas/roi_style.js";
import { setRegionPanel, hideRegionEditor, closeRegionPanel } from "./region_tool_ui.js";
import {
    ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    COLOR_RECT_SHAPE_REGION_DETECT,
    additional_events,
    boxContentStampAlignment,
    create_obj_cross_item,
    get_obj_product,
    obj_region_stamp_alignment_canvas,
    panner_region_stamp_alignment,
    refesh_btn,
    selected,
    setNameEventActivate,
    write_log_append,
    write_log_clear,
    tool_log,
    capture_log,
} from "./common_value_tool.js";

const EVENT_NAME = "stamp_alignment_tool";
const logStampAlignment = tool_log(EVENT_NAME);
const closeButton = document.getElementById("btn-exit-stamp-alignment");
const judgmentButton = document.getElementById("btn-judment-stamp-alignment");
let activeRoiId = null;
let viewVersion = 0;

additional_events.set(EVENT_NAME, event_transition_items);

obj_region_stamp_alignment_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT,
    (rect) => openRectangleEditor(rect, true),
);
obj_region_stamp_alignment_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT_HAVE_ALREADY,
    selectStoredRectangle,
);
obj_region_stamp_alignment_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_RIGHT_RECT,
    removeStoredRectangle,
);

// Bọc onClick của RectangleDrawer để:
// Khi vẽ xong điểm thứ 2 -> TỰ ĐỘNG MỞ TRƯỢT PANEL NGAY LẬP TỨC (không cần click vào viền)
const origOnClick = obj_region_stamp_alignment_canvas.onClick.bind(obj_region_stamp_alignment_canvas);
obj_region_stamp_alignment_canvas.onClick = (pos, cm) => {
    const wasDrawing = obj_region_stamp_alignment_canvas.isDrawing;
    const hadUnsavedRect = obj_region_stamp_alignment_canvas.is_available_one_rect;
    origOnClick(pos, cm);

    const inspector = getInspector();
    if (!wasDrawing && obj_region_stamp_alignment_canvas.isDrawing) {
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_stamp_alignment, null);
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(cm, pos);
    }

    if (hadUnsavedRect && obj_region_stamp_alignment_canvas.isDrawing) {
        if (boxContentStampAlignment) boxContentStampAlignment.innerHTML = "";
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(cm, pos);
        return;
    }

    // Hoàn tất điểm thứ 2 của khung mới -> hiển thị khung tạm và TỰ ĐỘNG TRƯỢT PANEL MỞ RA
    if (wasDrawing && !obj_region_stamp_alignment_canvas.isDrawing && obj_region_stamp_alignment_canvas.is_available_one_rect) {
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawPendingRectangle(cm, obj_region_stamp_alignment_canvas.rect_current);
        openRectangleEditor(obj_region_stamp_alignment_canvas.rect_current, true);
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
        ItemsInspector.TYPE_STAMP_ALIGNMENT,
        StampAlignmentItemInspector,
        "setStampAlignmentItems",
    );
}

function selectStoredRectangle(coordinate) {
    if (obj_region_stamp_alignment_canvas.isDrawing) return;
    if (obj_region_stamp_alignment_canvas.is_available_one_rect && obj_region_stamp_alignment_canvas.isPointOnRectBorder(
        obj_region_stamp_alignment_canvas.rect_current, coordinate.x, coordinate.y, ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE
    )) return;

    const inspector = getInspector();
    const rectangle = inspector?.findRectangleOnBorder(
        coordinate.x,
        coordinate.y,
        ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    );
    if (!rectangle) return;

    obj_region_stamp_alignment_canvas.reset();
    obj_region_stamp_alignment_canvas.have_return = true;
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
        setRegionPanel(panner_region_stamp_alignment, null);
        if (boxContentStampAlignment) boxContentStampAlignment.innerHTML = "";
        inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        updateHighlight();
        write_log_clear(logStampAlignment, "Đã hủy khung vừa vẽ.");
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
    if (boxContentStampAlignment) boxContentStampAlignment.innerHTML = "";
    obj_region_stamp_alignment_canvas.reset();
    inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
    const activeRectangle = inspector.rectangles.find(item => item.id === activeRoiId);
    if (activeRectangle) openRectangleEditor(activeRectangle, false);
    else setRegionPanel(panner_region_stamp_alignment, null);
    updateHighlight();
    write_log_clear(logStampAlignment, `Đã xóa khung "${rectangle.name}".`);
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
    if (!rectangle || rectangle.xStart < 0 || !boxContentStampAlignment) return;
    const inspector = getInspector();
    if (!inspector) return;
    activeRoiId = isNewPending ? null : rectangle.id;

    // Tự động kích hoạt hiệu ứng trượt Panel từ phải sang trái
    setRegionPanel(panner_region_stamp_alignment, isNewPending ? "pending" : activeRoiId, !isNewPending);

    boxContentStampAlignment.innerHTML = "";
    const wrapper = document.createElement("div");
    wrapper.className = "region-editor";

    const table = document.createElement("table");
    table.className = "measure-weld-width-config-table";

    // 1. Tên khung
    const inputName = document.createElement("input");
    inputName.id = "stamp-align-roi-name";
    inputName.type = "text";
    inputName.className = "config-input";
    inputName.placeholder = "Ví dụ: Tem 1";
    inputName.value = rectangle.name || `Tem ${inspector.getNextId() + 1}`;

    // 2. Δu max (px)
    const inpDu = document.createElement("input");
    inpDu.type = "number";
    inpDu.step = "1";
    inpDu.className = "config-input";
    inpDu.value = rectangle.max_du !== undefined ? rectangle.max_du : 15;

    // 3. Δv max (px)
    const inpDv = document.createElement("input");
    inpDv.type = "number";
    inpDv.step = "1";
    inpDv.className = "config-input";
    inpDv.value = rectangle.max_dv !== undefined ? rectangle.max_dv : 15;

    // 4. Δθ max (độ)
    const inpDeg = document.createElement("input");
    inpDeg.type = "number";
    inpDeg.step = "0.5";
    inpDeg.className = "config-input";
    inpDeg.value = rectangle.max_deg !== undefined ? rectangle.max_deg : 3.0;

    // 5. Margin lề an toàn (px)
    const inpMargin = document.createElement("input");
    inpMargin.type = "number";
    inpMargin.step = "1";
    inpMargin.className = "config-input";
    inpMargin.value = rectangle.margin !== undefined ? rectangle.margin : 5;

    table.append(
        createConfigRow(isNewPending ? "Tên khung mới" : "Tên khung", inputName),
        createConfigRow("Δu max (px)", inpDu),
        createConfigRow("Δv max (px)", inpDv),
        createConfigRow("Δθ max (°)", inpDeg),
        createConfigRow("Lề an toàn (px)", inpMargin),
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
            write_log_clear(logStampAlignment, "❌ Tên khung kiểm tra tem không được để trống.");
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
        model.max_du = parseFloat(inpDu.value) || 15.0;
        model.max_dv = parseFloat(inpDv.value) || 15.0;
        model.max_deg = parseFloat(inpDeg.value) || 3.0;
        model.margin = parseFloat(inpMargin.value) || 5.0;

        if (!model.isValid() || !inspector.addRectangle(model)) {
            write_log_clear(logStampAlignment, "❌ Dữ liệu khung hình chữ nhật không hợp lệ.");
            return;
        }
        boxContentStampAlignment.innerHTML = "";
        obj_region_stamp_alignment_canvas.reset();
        activeRoiId = model.id;
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        openRectangleEditor(model, false);
        hideRegionEditor(panner_region_stamp_alignment);
        updateHighlight();
        write_log_clear(
            logStampAlignment,
            `✅ Đã lưu khung "${name}" (Dung sai: Δu=${model.max_du}px, Δv=${model.max_dv}px, Δθ=${model.max_deg}°, margin=${model.margin}px). Có thể tiếp tục vẽ khung mới.`,
        );
    };

    const handleCancel = () => {
        boxContentStampAlignment.innerHTML = "";
        obj_region_stamp_alignment_canvas.reset();
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_stamp_alignment, null);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        updateHighlight();
        write_log_clear(
            logStampAlignment,
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
    boxContentStampAlignment.appendChild(wrapper);

    requestAnimationFrame(() => {
        inputName.focus();
        inputName.select();
    });
}

function updateHighlight() {
    get_obj_product()?.highlightItems(
        scroll_container,
        ItemsInspector.TYPE_STAMP_ALIGNMENT,
        "rectangles",
    );
}

function renderStampAlignmentResultSummary(data = {}) {
    if (!boxContentStampAlignment) return;
    boxContentStampAlignment.innerHTML = "";

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
    titleSpan.textContent = allOk ? "✓ KẾT QUẢ: ĐẠT (OK)" : "✗ KẾT QUẢ: LỆCH (NG)";
    const subSpan = document.createElement("span");
    subSpan.style.fontSize = "11px";
    subSpan.textContent = `${okCount}/${boxResults.length} khung đạt`;
    badge.append(titleSpan, subSpan);
    wrapper.appendChild(badge);

    // Bảng chi tiết: Khung -> Δu (px) -> Δv (px) -> Δθ (°) -> Tem nằm trong -> Kết quả
    const table = document.createElement("table");
    table.className = "stamp-alignment-summary-table";

    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    ["Khung", "Δu (px)", "Δv (px)", "Δθ (°)", "Tem nằm trong", "Kết quả"].forEach((headerText) => {
        const th = document.createElement("th");
        th.textContent = headerText;
        headerRow.appendChild(th);
    });

    const tbody = table.createTBody();
    boxResults.forEach((box, idx) => {
        const row = tbody.insertRow();
        const isOk = box.status === "OK";
        const metrics = box.metrics || {};
        const tolerances = box.tolerances || {};

        // 1. Tên khung (in đậm)
        const cellName = row.insertCell();
        cellName.textContent = box.name || `Tem ${idx + 1}`;
        cellName.style.setProperty("font-weight", "bold", "important");
        cellName.style.setProperty("color", "#1a202c", "important");
        cellName.style.setProperty("text-align", "left", "important");
        cellName.style.setProperty("padding-left", "8px", "important");

        // 2. Δu (px)
        const cellDu = row.insertCell();
        cellDu.textContent = `${metrics.du ?? 0}`;
        cellDu.title = `Ngưỡng tối đa: ${tolerances.max_du ?? 15} px`;
        if (Math.abs(metrics.du ?? 0) > (tolerances.max_du ?? 15)) {
            cellDu.style.setProperty("color", "#d50000", "important");
            cellDu.style.setProperty("font-weight", "bold", "important");
        } else {
            cellDu.style.setProperty("color", "#2c3e50", "important");
        }

        // 3. Δv (px)
        const cellDv = row.insertCell();
        cellDv.textContent = `${metrics.dv ?? 0}`;
        cellDv.title = `Ngưỡng tối đa: ${tolerances.max_dv ?? 15} px`;
        if (Math.abs(metrics.dv ?? 0) > (tolerances.max_dv ?? 15)) {
            cellDv.style.setProperty("color", "#d50000", "important");
            cellDv.style.setProperty("font-weight", "bold", "important");
        } else {
            cellDv.style.setProperty("color", "#2c3e50", "important");
        }

        // 4. Δθ (°)
        const cellDeg = row.insertCell();
        cellDeg.textContent = `${metrics.delta_angle_deg ?? 0}°`;
        cellDeg.title = `Ngưỡng tối đa: ${tolerances.max_deg ?? 3.0}°`;
        if (Math.abs(metrics.delta_angle_deg ?? 0) > (tolerances.max_deg ?? 3.0)) {
            cellDeg.style.setProperty("color", "#d50000", "important");
            cellDeg.style.setProperty("font-weight", "bold", "important");
        } else {
            cellDeg.style.setProperty("color", "#2c3e50", "important");
        }

        // 5. Tem nằm trong (Nằm trong: xanh, Chạm viền: đỏ)
        const cellCont = row.insertCell();
        const isContained = Boolean(metrics.is_contained);
        cellCont.textContent = isContained ? "Nằm trong" : "Chạm viền";
        cellCont.style.setProperty("font-weight", "bold", "important");
        cellCont.style.setProperty("color", isContained ? "#00c853" : "#d50000", "important");

        // 6. Kết quả (OK: xanh, NG: đỏ)
        const cellStatus = row.insertCell();
        cellStatus.textContent = isOk ? "OK" : "NG";
        cellStatus.style.setProperty("font-weight", "bold", "important");
        cellStatus.style.setProperty("color", isOk ? "#00c853" : "#d50000", "important");
    });

    wrapper.appendChild(table);
    boxContentStampAlignment.appendChild(wrapper);
}

judgmentButton?.addEventListener("click", async () => {
    const version = viewVersion;
    const logStampAlign = capture_log(tool_log(EVENT_NAME), () =>
        version === viewVersion && canvasManager.currentTool === obj_region_stamp_alignment_canvas);
    const inspector = getInspector();
    const region = inspector?.rectangles.find(rect => rect.id === activeRoiId);
    if (!selected || selected.product_id < 0 || selected.frame_id < 0 || selected.items_id < 0) {
        write_log_clear(logStampAlign, "❌ Chưa chọn đầy đủ sản phẩm, frame và item.");
        return;
    }
    if (!region) {
        write_log_clear(logStampAlign, "⚠️ Hãy chọn một khung kiểm tra lệch tem đã chấp nhận trên ảnh.");
        return;
    }

    write_log_clear(logStampAlign, "⏳ Đang chạy model YOLO OBB kiểm tra độ lệch tem...");
    try {
        const payload = {
            select: { ...selected },
            boxes: [region.toDict()],
            WidthCanvas: WIDTH_IMG_SHAPE,
        };
        const result = await postData("/law_regulation/stamp_alignment/run_model", payload);
        if (version !== viewVersion || canvasManager.currentTool !== obj_region_stamp_alignment_canvas) return;
        if (!result?.ok) {
            write_log_clear(logStampAlign, `❌ Phán định thất bại: ${result?.message || "Lỗi không xác định"}`);
            return;
        }

        const data = result.data || {};
        const boxResults = Array.isArray(data.boxes) ? data.boxes : [];
        const objects = (data.objects || []).map(obj => ({
            ...obj,
            image_width: obj.image_width || data.width || 2048,
            canvasWidth: WIDTH_IMG_SHAPE,
        }));

        obj_region_stamp_alignment_canvas.reset();
        inspector.setDetectionResults(objects, boxResults);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        renderStampAlignmentResultSummary(data);

        const ngBoxes = boxResults.filter(item => item.status !== "OK");

        if (ngBoxes.length === 0) {
            const firstBox = boxResults[0];
            const m = firstBox?.metrics || {};
            write_log_clear(
                logStampAlign,
                `✅ Phán định OK: Khung "${region.name}" đạt chuẩn vị trí (Δu=${m.du}px, Δv=${m.dv}px, Δθ=${m.delta_angle_deg}°, Tem nằm trong=Nằm trong).`,
            );
        } else {
            write_log_clear(
                logStampAlign,
                `❌ Phán định NG: Tem lệch tại ${ngBoxes.length}/${boxResults.length} khung:`,
            );
            ngBoxes.forEach((box) => {
                const m = box.metrics || {};
                const err = box.error ? ` (${box.error})` : ` (Δu=${m.du}px, Δv=${m.dv}px, Δθ=${m.delta_angle_deg}°)`;
                write_log_append(
                    logStampAlign,
                    ` - [Kiểm tra lệch tem] NG - Khung "${box.name}"${err}`,
                );
            });
        }
    } catch (error) {
        write_log_clear(logStampAlign, `❌ Lỗi kết nối API kiểm tra lệch tem: ${error.message}`);
    }
});

export function event_transition_items() {
    activeRoiId = null;
    viewVersion++;
    setRegionPanel(panner_region_stamp_alignment, null);
    if (boxContentStampAlignment) boxContentStampAlignment.innerHTML = "";
    obj_region_stamp_alignment_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();

    const inspector = getInspector();
    inspector?.removeBoxs();
    inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
    updateHighlight();
    write_log_clear(
        logStampAlignment,
        "Vẽ 2 điểm trên ảnh để tạo khung kiểm tra độ lệch tem. Khung vẽ xong sẽ tự động trượt mở panel cấu hình.",
    );
}

closeButton?.addEventListener("click", async () => {
    activeRoiId = null;
    viewVersion++;
    obj_region_stamp_alignment_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();
    canvasManager.setTool(null);
    refesh_btn();
    get_obj_product()?.clearHighlight(scroll_container);
    setNameEventActivate(null);
    if (await closeRegionPanel(panner_region_stamp_alignment)) {
        if (boxContentStampAlignment) boxContentStampAlignment.innerHTML = "";
    }
});
