import { ModelRectangle } from "../model/model_rectangle.js";
import { canvasManager, scroll_container, WIDTH_IMG_SHAPE, HEIGH_IMG_SHAPE } from "../common_value.js";
import { RectangleDrawer } from "../canvas/rectangel_drawer_canvas.js";
import { QRItemInspector } from "../services/qr_item_inspector.js";
import { ItemsInspector } from "../services/items_inspector.js";
import { postData } from "../utills/api.js";
import { drawRoi } from "../canvas/roi_style.js";
import { setRegionPanel, hideRegionEditor, closeRegionPanel } from "./region_tool_ui.js";
import {
    ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    COLOR_RECT_SHAPE_REGION_DETECT,
    additional_events,
    boxContentQR,
    create_obj_cross_item,
    get_obj_product,
    obj_region_qr_canvas,
    panner_region_qr,
    refesh_btn,
    selected,
    setNameEventActivate,
    write_log_append,
    write_log_clear,
    tool_log,
    capture_log,
} from "./common_value_tool.js";

const EVENT_NAME = "qr_tool";
const logQR = tool_log(EVENT_NAME);
const closeButton = document.getElementById("btn-exit-qr");
const runButton = document.getElementById("btn-judment-qr");
let activeRoiId = null;
let viewVersion = 0;

additional_events.set(EVENT_NAME, event_transition_items);

obj_region_qr_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT,
    rectangle => openRectangleEditor(rectangle, true),
);
obj_region_qr_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT_HAVE_ALREADY,
    selectStoredRectangle,
);
obj_region_qr_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_RIGHT_RECT,
    removeStoredRectangle,
);

const originalOnClick = obj_region_qr_canvas.onClick.bind(obj_region_qr_canvas);
obj_region_qr_canvas.onClick = (position, manager) => {
    const wasDrawing = obj_region_qr_canvas.isDrawing;
    const hadUnsavedRect = obj_region_qr_canvas.is_available_one_rect;
    originalOnClick(position, manager);
    const inspector = getInspector();

    if (!wasDrawing && obj_region_qr_canvas.isDrawing) {
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_qr, null);
        inspector?.drawAll(manager, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(manager, position);
    }

    if (hadUnsavedRect && obj_region_qr_canvas.isDrawing) {
        if (boxContentQR) boxContentQR.innerHTML = "";
        inspector?.drawAll(manager, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(manager, position);
        return;
    }

    if (
        wasDrawing
        && !obj_region_qr_canvas.isDrawing
        && obj_region_qr_canvas.is_available_one_rect
    ) {
        inspector?.drawAll(manager, COLOR_RECT_SHAPE_REGION_DETECT);
        drawPendingRectangle(manager, obj_region_qr_canvas.rect_current);
        openRectangleEditor(obj_region_qr_canvas.rect_current, true);
    }
};

function getInspector() {
    return create_obj_cross_item(
        ItemsInspector.TYPE_QR,
        QRItemInspector,
        "setQRItems",
    );
}

function drawStartPoint(manager, position) {
    const context = manager.ctxShape;
    context.save();
    context.fillStyle = "#FF1744";
    context.beginPath();
    context.arc(position.x, position.y, 4, 0, Math.PI * 2);
    context.fill();
    context.restore();
}

function drawPendingRectangle(manager, rectangle) {
    if (!rectangle || rectangle.width <= 0 || rectangle.height <= 0) return;
    drawRoi(manager.ctxShape, rectangle, {pending: true});
}

function selectStoredRectangle(coordinate) {
    if (obj_region_qr_canvas.isDrawing) return;
    if (
        obj_region_qr_canvas.is_available_one_rect
        && obj_region_qr_canvas.isPointOnRectBorder(
            obj_region_qr_canvas.rect_current,
            coordinate.x,
            coordinate.y,
            ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
        )
    ) return;

    const inspector = getInspector();
    const rectangle = inspector?.findRectangleOnBorder(
        coordinate.x,
        coordinate.y,
        ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    );
    if (!rectangle) return;

    obj_region_qr_canvas.reset();
    obj_region_qr_canvas.have_return = true;
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
        setRegionPanel(panner_region_qr, null);
        if (boxContentQR) boxContentQR.innerHTML = "";
        inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        write_log_clear(logQR, "Đã hủy khung vừa vẽ.");
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
    if (boxContentQR) boxContentQR.innerHTML = "";
    obj_region_qr_canvas.reset();
    inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
    const activeRectangle = inspector.rectangles.find(item => item.id === activeRoiId);
    if (activeRectangle) openRectangleEditor(activeRectangle, false);
    else setRegionPanel(panner_region_qr, null);
    updateHighlight();
    write_log_clear(logQR, `Đã xóa khung "${rectangle.name}".`);
}

function openRectangleEditor(rectangle, isNewPending = false) {
    if (!rectangle || rectangle.xStart < 0 || !boxContentQR) return;
    const inspector = getInspector();
    if (!inspector) return;

    activeRoiId = isNewPending ? null : rectangle.id;
    setRegionPanel(panner_region_qr, isNewPending ? "pending" : activeRoiId, !isNewPending);
    boxContentQR.innerHTML = "";

    const wrapper = document.createElement("div");
    wrapper.className = "region-editor";
    const nameLabel = document.createElement("label");
    nameLabel.htmlFor = "qr-roi-name";
    nameLabel.textContent = isNewPending
        ? "Đặt tên vùng kiểm tra QR mới"
        : "Đổi tên vùng kiểm tra QR";

    const nameInput = document.createElement("input");
    nameInput.id = "qr-roi-name";
    nameInput.type = "text";
    nameInput.className = "config-input";
    nameInput.placeholder = "Ví dụ: Mã QR truy xuất";
    nameInput.value = rectangle.name || `QR ${inspector.getNextId() + 1}`;

    const expectedLabel = document.createElement("label");
    expectedLabel.htmlFor = "qr-roi-expected-text";
    expectedLabel.textContent = "Nội dung QR code, barcode bắt buộc phải nhận diện";

    const expectedInput = document.createElement("textarea");
    expectedInput.id = "qr-roi-expected-text";
    expectedInput.className = "config-input";
    expectedInput.rows = 3;
    expectedInput.placeholder = "Nhập chính xác chuỗi mã QR cần kiểm tra";
    expectedInput.value = String(rectangle.expected_text || "");

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
        const name = nameInput.value.trim();
        const expectedText = expectedInput.value.trim();
        if (!name) {
            write_log_clear(logQR, "Tên vùng QR không được để trống.");
            nameInput.focus();
            return;
        }
        if (!expectedText) {
            write_log_clear(logQR, "Nội dung mã QR bắt buộc không được để trống.");
            expectedInput.focus();
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
        model.expected_text = expectedText;
        if (!model.isValid() || !inspector.addRectangle(model)) {
            write_log_clear(logQR, "Dữ liệu khung QR không hợp lệ.");
            return;
        }

        boxContentQR.innerHTML = "";
        obj_region_qr_canvas.reset();
        activeRoiId = model.id;
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        openRectangleEditor(model, false);
        hideRegionEditor(panner_region_qr);
        updateHighlight();
        write_log_clear(
            logQR,
            `Đã lưu "${name}". Bấm "Chạy model" để kiểm tra đọc thử mã QR bằng ZXing-C++.`,
        );
    };

    const handleCancel = () => {
        boxContentQR.innerHTML = "";
        obj_region_qr_canvas.reset();
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_qr, null);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        updateHighlight();
        write_log_clear(logQR, isNewPending ? "Đã hủy khung vừa vẽ." : "Đã hủy chỉnh sửa vùng QR.");
    };

    acceptButton.addEventListener("click", handleAccept);
    cancelButton.addEventListener("click", handleCancel);
    nameInput.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            event.preventDefault();
            handleAccept();
        } else if (event.key === "Escape") {
            event.preventDefault();
            handleCancel();
        }
    });
    expectedInput.addEventListener("keydown", event => {
        if (event.key === "Enter" && event.ctrlKey) {
            event.preventDefault();
            handleAccept();
        } else if (event.key === "Escape") {
            event.preventDefault();
            handleCancel();
        }
    });

    actions.append(acceptButton, cancelButton);
    wrapper.append(nameLabel, nameInput, expectedLabel, expectedInput, actions);
    boxContentQR.appendChild(wrapper);
    requestAnimationFrame(() => {
        (isNewPending ? nameInput : expectedInput).focus();
        (isNewPending ? nameInput : expectedInput).select();
    });
}

function updateHighlight() {
    get_obj_product()?.highlightItems(
        scroll_container,
        ItemsInspector.TYPE_QR,
        "rectangles",
    );
}

function renderQRResult(data = {}) {
    if (!boxContentQR) return;
    boxContentQR.innerHTML = "";
    const boxes = Array.isArray(data.boxes) ? data.boxes : [];
    if (!boxes.length) return;

    const isOk = Boolean(data.ok);
    const wrapper = document.createElement("div");
    wrapper.className = "patchcore-inference-result";
    wrapper.style.display = "flex";
    wrapper.style.flexDirection = "column";
    wrapper.style.gap = "8px";

    const badge = document.createElement("div");
    badge.className = `inference-badge ${isOk ? "ok" : "ng"}`;
    badge.style.padding = "6px 10px";
    badge.style.borderRadius = "6px";
    badge.style.fontWeight = "bold";
    badge.style.color = isOk ? "#00c853" : "#d50000";
    badge.style.backgroundColor = isOk ? "#e8f5e9" : "#ffebee";
    badge.textContent = `${isOk ? "✓ KẾT QUẢ: OK" : "✗ KẾT QUẢ: NG"} — ${data.message || ""}`;
    wrapper.appendChild(badge);

    const table = document.createElement("table");
    table.className = "patchcore-inference-table";
    table.style.width = "100%";
    table.style.fontSize = "12px";
    const header = table.createTHead().insertRow();
    ["Vùng", "Chuỗi quy định", "QR nhận diện", "Chuẩn mã", "Thời gian", "KQ"]
        .forEach(text => {
            const cell = document.createElement("th");
            cell.textContent = text;
            cell.style.padding = "5px 8px";
            cell.style.background = "#eceff1";
            cell.style.textAlign = "left";
            header.appendChild(cell);
        });

    const body = table.createTBody();
    for (const box of boxes) {
        const row = body.insertRow();
        row.insertCell().textContent = box.name || "Vùng QR";
        row.insertCell().textContent = box.expected_text || "";
        const recognizedCell = row.insertCell();
        recognizedCell.textContent = box.text || "Không tìm thấy mã QR";
        recognizedCell.style.whiteSpace = "pre-wrap";
        row.insertCell().textContent = box.format || "—";
        row.insertCell().textContent = box.processing_time_ms ? `${box.processing_time_ms} ms` : "—";
        const statusCell = row.insertCell();
        statusCell.textContent = box.ok ? "OK" : "NG";
        statusCell.style.color = box.ok ? "#00c853" : "#d50000";
        statusCell.style.fontWeight = "bold";
    }
    wrapper.appendChild(table);
    boxContentQR.appendChild(wrapper);
}

runButton?.addEventListener("click", async () => {
    const version = viewVersion;
    const log = capture_log(logQR, () =>
        version === viewVersion && canvasManager.currentTool === obj_region_qr_canvas);
    const inspector = getInspector();
    const region = inspector?.rectangles.find(item => item.id === activeRoiId);
    if (!selected || selected.product_id < 0 || selected.frame_id < 0 || selected.items_id < 0) {
        write_log_clear(log, "Chưa chọn đầy đủ sản phẩm, frame và item.");
        return;
    }
    if (!region) {
        write_log_clear(log, "Hãy chọn một khung QR đã lưu để chạy nhận diện.");
        return;
    }
    if (!String(region.expected_text || "").trim()) {
        write_log_clear(log, "Hãy nhập nội dung QR bắt buộc cho vùng đang chọn.");
        return;
    }

    write_log_clear(log, "Đang quét mã QR bằng ZXing-C++ cho vùng đang chọn...");
    try {
        const response = await postData("/law_regulation/qr/run_model", {
            select: {...selected},
            roi: region.toDict
                ? {...region.toDict(), expected_text: region.expected_text}
                : {
                    id: region.id,
                    name: region.name,
                    xStart: region.xStart,
                    yStart: region.yStart,
                    xEnd: region.xEnd,
                    yEnd: region.yEnd,
                    expected_text: region.expected_text,
                },
            WidthCanvas: WIDTH_IMG_SHAPE,
            HeightCanvas: HEIGH_IMG_SHAPE,
        });
        if (version !== viewVersion || canvasManager.currentTool !== obj_region_qr_canvas) return;
        if (!response?.ok) {
            write_log_clear(log, `Quét QR thất bại: ${response?.message || "Lỗi không xác định"}`);
            return;
        }

        const data = response.data || {};
        const boxes = Array.isArray(data.boxes) ? data.boxes : [];
        inspector.setDetectionResults([], boxes);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        renderQRResult(data);
        if (data.ok) {
            write_log_clear(log, `Mã QR khớp nội dung yêu cầu tại "${region.name}".`);
        } else {
            write_log_clear(log, data.message || `Mã QR không khớp nội dung tại "${region.name}".`);
        }
    } catch (error) {
        write_log_clear(log, `Lỗi kết nối API QR: ${error.message}`);
    }
});

export function event_transition_items() {
    activeRoiId = null;
    viewVersion++;
    setRegionPanel(panner_region_qr, null);
    if (boxContentQR) boxContentQR.innerHTML = "";
    obj_region_qr_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();
    const inspector = getInspector();
    inspector?.removeBoxs();
    inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
    updateHighlight();
    write_log_clear(
        logQR,
        "Vẽ 2 điểm để tạo vùng QR; nhập chuỗi mã bắt buộc nhận diện. Click viền khung để mở cấu hình.",
    );
}

closeButton?.addEventListener("click", async () => {
    activeRoiId = null;
    viewVersion++;
    obj_region_qr_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();
    canvasManager.setTool(null);
    refesh_btn();
    get_obj_product()?.clearHighlight(scroll_container);
    setNameEventActivate(null);
    if (await closeRegionPanel(panner_region_qr)) {
        if (boxContentQR) boxContentQR.innerHTML = "";
    }
});
