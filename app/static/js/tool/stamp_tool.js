import { ModelRectangle } from "../model/model_rectangle.js";
import { canvasManager, scroll_container, WIDTH_IMG_SHAPE } from "../common_value.js";
import { RectangleDrawer } from "../canvas/rectangel_drawer_canvas.js";
import { StampItemInspector } from "../services/stamp_item_inspector.js";
import { ItemsInspector } from "../services/items_inspector.js";
import { postData } from "../utills/api.js";
import { drawRoi } from "../canvas/roi_style.js";
import { setRegionPanel, hideRegionEditor, closeRegionPanel } from "./region_tool_ui.js";
import {
    ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    COLOR_RECT_SHAPE_REGION_DETECT,
    additional_events,
    boxContentStamp,
    create_obj_cross_item,
    get_obj_product,
    obj_region_stamp_canvas,
    panner_region_stamp,
    refesh_btn,
    selected,
    setNameEventActivate,
    write_log_append,
    write_log_clear,
    tool_log,
    capture_log,
} from "./common_value_tool.js";

const EVENT_NAME = "stamp_tool";
const logStamp = tool_log(EVENT_NAME);
const closeButton = document.getElementById("btn-exit-stamp");
const judgmentButton = document.getElementById("btn-judment-stamp");
let activeRoiId = null;
let viewVersion = 0;

additional_events.set(EVENT_NAME, event_transition_items);

obj_region_stamp_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT,
    (rect) => openRectangleEditor(rect, true),
);
obj_region_stamp_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT_HAVE_ALREADY,
    selectStoredRectangle,
);
obj_region_stamp_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_RIGHT_RECT,
    removeStoredRectangle,
);

// Bọc onClick của RectangleDrawer để:
// 1. Giữ nguyên các khung đã lưu trên Canvas khi đang vẽ hoặc hủy khung tạm.
// 2. Mở ngay ô đặt tên khung ("Tem 1", "Tem 2", ...) ngay sau click thứ 2 hoàn tất vẽ khung.
const origOnClick = obj_region_stamp_canvas.onClick.bind(obj_region_stamp_canvas);
obj_region_stamp_canvas.onClick = (pos, cm) => {
    const wasDrawing = obj_region_stamp_canvas.isDrawing;
    const hadUnsavedRect = obj_region_stamp_canvas.is_available_one_rect;
    origOnClick(pos, cm);

    const inspector = getInspector();
    if (!wasDrawing && obj_region_stamp_canvas.isDrawing) {
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_stamp, null);
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(cm, pos);
    }

    // Người dùng bỏ qua khung tạm chưa lưu để click điểm đầu vẽ khung mới
    if (hadUnsavedRect && obj_region_stamp_canvas.isDrawing) {
        if (boxContentStamp) boxContentStamp.innerHTML = "";
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(cm, pos);
        return;
    }

    // Hoàn tất điểm thứ 2 của khung mới -> hiển thị khung tạm + mở ngay ô nhập tên
    if (wasDrawing && !obj_region_stamp_canvas.isDrawing && obj_region_stamp_canvas.is_available_one_rect) {
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawPendingRectangle(cm, obj_region_stamp_canvas.rect_current);
        openRectangleEditor(obj_region_stamp_canvas.rect_current, true);
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
    drawRoi(cm.ctxShape, rect, {pending: true});
}

function getInspector() {
    return create_obj_cross_item(
        ItemsInspector.TYPE_STAMP,
        StampItemInspector,
        "setStampItems",
    );
}

function selectStoredRectangle(coordinate) {
    // Không chặn click thứ 2 khi người dùng đang vẽ dở khung mới
    if (obj_region_stamp_canvas.isDrawing) return;
    if (obj_region_stamp_canvas.is_available_one_rect && obj_region_stamp_canvas.isPointOnRectBorder(
        obj_region_stamp_canvas.rect_current, coordinate.x, coordinate.y, ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE
    )) return;

    const inspector = getInspector();
    const rectangle = inspector?.findRectangleOnBorder(
        coordinate.x,
        coordinate.y,
        ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    );
    if (!rectangle) return;

    obj_region_stamp_canvas.reset();
    obj_region_stamp_canvas.have_return = true;
    activeRoiId = rectangle.id;
    viewVersion++;
    inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
    openRectangleEditor(rectangle, false);
}

function removeStoredRectangle(payload) {
    const inspector = getInspector();

    // Nếu vừa click chuột phải xóa khung tạm chưa lưu (RectangleDrawer đã clear ctxShape)
    if (payload?.status_check_point_in_rect_current) {
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_stamp, null);
        if (boxContentStamp) boxContentStamp.innerHTML = "";
        inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        write_log_clear(logStamp, "Đã hủy khung vừa vẽ.");
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
    if (boxContentStamp) boxContentStamp.innerHTML = "";
    obj_region_stamp_canvas.reset();
    inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
    const activeRectangle = inspector.rectangles.find(item => item.id === activeRoiId);
    if (activeRectangle) openRectangleEditor(activeRectangle, false);
    else setRegionPanel(panner_region_stamp, null);
    updateHighlight();
    write_log_clear(logStamp, `Đã xóa khung "${rectangle.name}".`);
}

function openRectangleEditor(rectangle, isNewPending = false) {
    if (!rectangle || rectangle.xStart < 0 || !boxContentStamp) return;
    const inspector = getInspector();
    if (!inspector) return;
    activeRoiId = isNewPending ? null : rectangle.id;
    setRegionPanel(panner_region_stamp, isNewPending ? "pending" : activeRoiId, !isNewPending);

    boxContentStamp.innerHTML = "";
    const wrapper = document.createElement("div");
    wrapper.className = "region-editor";

    const label = document.createElement("label");
    label.textContent = isNewPending ? "Đặt tên khung kiểm tra tem mới" : "Đổi tên khung kiểm tra tem";
    label.htmlFor = "stamp-roi-name";

    const input = document.createElement("input");
    input.id = "stamp-roi-name";
    input.type = "text";
    input.className = "config-input";
    input.placeholder = "Ví dụ: Tem 1";
    input.value = rectangle.name || `Tem ${inspector.getNextId() + 1}`;

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
        const name = input.value.trim();
        if (!name) {
            write_log_clear(logStamp, "❌ Tên khung kiểm tra tem không được để trống.");
            input.focus();
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
        if (!model.isValid() || !inspector.addRectangle(model)) {
            write_log_clear(logStamp, "❌ Dữ liệu khung hình chữ nhật không hợp lệ.");
            return;
        }
        boxContentStamp.innerHTML = "";
        obj_region_stamp_canvas.reset();
        activeRoiId = model.id;
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        openRectangleEditor(model, false);
        hideRegionEditor(panner_region_stamp);
        updateHighlight();
        write_log_clear(
            logStamp,
            `✅ Đã lưu khung "${name}" (Quy định: Có tem). Có thể tiếp tục vẽ khung mới.`,
        );
    };

    const handleCancel = () => {
        boxContentStamp.innerHTML = "";
        obj_region_stamp_canvas.reset();
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_stamp, null);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        write_log_clear(
            logStamp,
            isNewPending ? "Đã hủy khung vừa vẽ." : "Đã hủy chỉnh sửa tên khung.",
        );
    };

    acceptButton.addEventListener("click", handleAccept);
    cancelButton.addEventListener("click", handleCancel);

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            handleAccept();
        } else if (event.key === "Escape") {
            event.preventDefault();
            handleCancel();
        }
    });

    actions.append(acceptButton, cancelButton);
    wrapper.append(label, input, actions);
    boxContentStamp.appendChild(wrapper);

    requestAnimationFrame(() => {
        input.focus();
        input.select();
    });
}

function updateHighlight() {
    get_obj_product()?.highlightItems(
        scroll_container,
        ItemsInspector.TYPE_STAMP,
        "rectangles",
    );
}

function renderStampResultSummary(data = {}) {
    if (!boxContentStamp) return;
    boxContentStamp.innerHTML = "";

    const boxResults = Array.isArray(data.boxes) ? data.boxes : [];
    if (!boxResults.length) return;

    const allOk = boxResults.every(item => item.exists === true);
    const statusColor = allOk ? "#00c853" : "#d50000";
    const statusBg = allOk ? "#e8f5e9" : "#ffebee";

    const wrapper = document.createElement("div");
    wrapper.style.padding = "10px";
    wrapper.style.display = "flex";
    wrapper.style.flexDirection = "column";
    wrapper.style.gap = "8px";

    const badge = document.createElement("div");
    badge.style.display = "flex";
    badge.style.alignItems = "center";
    badge.style.justifyContent = "space-between";
    badge.style.padding = "8px 12px";
    badge.style.borderRadius = "8px";
    badge.style.fontWeight = "bold";
    badge.style.fontSize = "13px";
    badge.style.backgroundColor = statusBg;
    badge.style.color = statusColor;
    badge.style.border = `1.5px solid ${statusColor}`;

    const okCount = boxResults.filter(item => item.exists === true).length;
    const titleSpan = document.createElement("span");
    titleSpan.textContent = allOk ? "✓ KẾT QUẢ: OK" : "✗ KẾT QUẢ: NG";
    const subSpan = document.createElement("span");
    subSpan.style.fontSize = "12px";
    subSpan.textContent = `${okCount}/${boxResults.length} khung có tem`;
    badge.append(titleSpan, subSpan);
    wrapper.appendChild(badge);

    const table = document.createElement("table");
    table.className = "patchcore-inference-table";
    table.style.width = "100%";
    table.style.fontSize = "12px";

    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    ["Khung", "Quy định", "Thực tế", "KQ"].forEach((headerText) => {
        const th = document.createElement("th");
        th.textContent = headerText;
        th.style.padding = "5px 8px";
        th.style.background = "#eceff1";
        th.style.textAlign = "left";
        headerRow.appendChild(th);
    });

    const tbody = table.createTBody();
    boxResults.forEach((box, idx) => {
        const row = tbody.insertRow();
        const exists = box.exists === true;
        row.insertCell().textContent = box.name || `Tem ${idx + 1}`;
        row.insertCell().textContent = "Có tem";
        row.insertCell().textContent = exists ? `Có tem (${box.count || 1})` : "Không có tem";

        const statusCell = row.insertCell();
        statusCell.textContent = exists ? "OK" : "NG";
        statusCell.style.fontWeight = "bold";
        statusCell.style.color = exists ? "#00c853" : "#d50000";
    });
    wrapper.appendChild(table);
    boxContentStamp.appendChild(wrapper);
}

judgmentButton?.addEventListener("click", async () => {
    const version = viewVersion;
    const logStamp = capture_log(tool_log(EVENT_NAME), () =>
        version === viewVersion && canvasManager.currentTool === obj_region_stamp_canvas);
    const inspector = getInspector();
    const region = inspector?.rectangles.find(rect => rect.id === activeRoiId);
    if (!selected || selected.product_id < 0 || selected.frame_id < 0 || selected.items_id < 0) {
        write_log_clear(logStamp, "❌ Chưa chọn đầy đủ sản phẩm, frame và item.");
        return;
    }
    if (!region) {
        write_log_clear(logStamp, "⚠️ Hãy chọn một khung kiểm tra tem đã chấp nhận trên ảnh.");
        return;
    }

    write_log_clear(logStamp, "⏳ Đang chạy model kiểm tra Có/Không tem...");
    try {
        const payload = {
            select: {...selected},
            boxes: [region.toDict()],
            WidthCanvas: WIDTH_IMG_SHAPE,
        };
        const result = await postData("/law_regulation/stamp/run_model", payload);
        if (version !== viewVersion || canvasManager.currentTool !== obj_region_stamp_canvas) return;
        if (!result?.ok) {
            write_log_clear(logStamp, `❌ Phán định thất bại: ${result?.message || "Lỗi không xác định"}`);
            return;
        }

        const data = result.data || {};
        const boxResults = Array.isArray(data.boxes) ? data.boxes : [];
        const objects = (data.objects || []).map(obj => ({
            ...obj,
            image_width: obj.image_width || data.width || 2048,
            canvasWidth: WIDTH_IMG_SHAPE,
        }));

        obj_region_stamp_canvas.reset();
        inspector.setDetectionResults(objects, boxResults);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        renderStampResultSummary(data);

        const missingBoxes = boxResults.filter(item => !item.exists);

        if (missingBoxes.length === 0) {
            write_log_clear(
                logStamp,
                `✅ Phán định OK: Khung "${region.name}" có tem.`,
            );
        } else {
            write_log_clear(
                logStamp,
                `❌ Phán định NG: Thiếu tem tại ${missingBoxes.length}/${boxResults.length} khung:`,
            );
            missingBoxes.forEach((box) => {
                write_log_append(
                    logStamp,
                    ` - [Kiểm tra tem] NG - Khung "${box.name}" - Quy định: "Có tem" - Thực tế: "Không có tem"`,
                );
            });
        }
    } catch (error) {
        write_log_clear(logStamp, `❌ Lỗi kết nối API kiểm tra tem: ${error.message}`);
    }
});

export function event_transition_items() {
    activeRoiId = null;
    viewVersion++;
    setRegionPanel(panner_region_stamp, null);
    if (boxContentStamp) boxContentStamp.innerHTML = "";
    obj_region_stamp_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();

    const inspector = getInspector();
    inspector?.removeBoxs();
    inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
    updateHighlight();
    write_log_clear(
        logStamp,
        "Vẽ 2 điểm trên ảnh để tạo khung kiểm tra tem (chuột trái vào viền để sửa tên, chuột phải vào viền để xóa).",
    );
}

closeButton?.addEventListener("click", async () => {
    activeRoiId = null;
    viewVersion++;
    obj_region_stamp_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();
    canvasManager.setTool(null);
    refesh_btn();
    get_obj_product()?.clearHighlight(scroll_container);
    setNameEventActivate(null);
    if (await closeRegionPanel(panner_region_stamp)) {
        if (boxContentStamp) boxContentStamp.innerHTML = "";
    }
});
