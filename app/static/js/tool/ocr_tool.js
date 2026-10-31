import { ModelRectangle } from "../model/model_rectangle.js";
import { canvasManager, scroll_container, WIDTH_IMG_SHAPE, HEIGH_IMG_SHAPE } from "../common_value.js";
import { RectangleDrawer } from "../canvas/rectangel_drawer_canvas.js";
import { OCRItemInspector } from "../services/ocr_item_inspector.js";
import { ItemsInspector } from "../services/items_inspector.js";
import { postData } from "../utills/api.js";
import { drawRoi } from "../canvas/roi_style.js";
import { setRegionPanel, hideRegionEditor, closeRegionPanel } from "./region_tool_ui.js";
import {
    ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    COLOR_RECT_SHAPE_REGION_DETECT,
    additional_events,
    boxContentOCR,
    create_obj_cross_item,
    get_obj_product,
    obj_region_ocr_canvas,
    panner_region_ocr,
    refesh_btn,
    selected,
    setNameEventActivate,
    write_log_append,
    write_log_clear,
    tool_log,
    capture_log,
} from "./common_value_tool.js";

const EVENT_NAME = "ocr_tool";
const logOCR = tool_log(EVENT_NAME);
const closeButton = document.getElementById("btn-exit-ocr");
const runButton = document.getElementById("btn-judment-ocr");
let activeRoiId = null;
let viewVersion = 0;

additional_events.set(EVENT_NAME, event_transition_items);

obj_region_ocr_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT,
    rectangle => openRectangleEditor(rectangle, true),
);
obj_region_ocr_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT_HAVE_ALREADY,
    selectStoredRectangle,
);
obj_region_ocr_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_RIGHT_RECT,
    removeStoredRectangle,
);

const originalOnClick = obj_region_ocr_canvas.onClick.bind(obj_region_ocr_canvas);
obj_region_ocr_canvas.onClick = (position, manager) => {
    const wasDrawing = obj_region_ocr_canvas.isDrawing;
    const hadUnsavedRect = obj_region_ocr_canvas.is_available_one_rect;
    originalOnClick(position, manager);
    const inspector = getInspector();

    if (!wasDrawing && obj_region_ocr_canvas.isDrawing) {
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_ocr, null);
        inspector?.drawAll(manager, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(manager, position);
    }

    if (hadUnsavedRect && obj_region_ocr_canvas.isDrawing) {
        if (boxContentOCR) boxContentOCR.innerHTML = "";
        inspector?.drawAll(manager, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(manager, position);
        return;
    }

    if (
        wasDrawing
        && !obj_region_ocr_canvas.isDrawing
        && obj_region_ocr_canvas.is_available_one_rect
    ) {
        inspector?.drawAll(manager, COLOR_RECT_SHAPE_REGION_DETECT);
        drawPendingRectangle(manager, obj_region_ocr_canvas.rect_current);
        openRectangleEditor(obj_region_ocr_canvas.rect_current, true);
    }
};

function getInspector() {
    return create_obj_cross_item(
        ItemsInspector.TYPE_OCR,
        OCRItemInspector,
        "setOCRItems",
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
    if (obj_region_ocr_canvas.isDrawing) return;
    if (
        obj_region_ocr_canvas.is_available_one_rect
        && obj_region_ocr_canvas.isPointOnRectBorder(
            obj_region_ocr_canvas.rect_current,
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

    obj_region_ocr_canvas.reset();
    obj_region_ocr_canvas.have_return = true;
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
        setRegionPanel(panner_region_ocr, null);
        if (boxContentOCR) boxContentOCR.innerHTML = "";
        inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        write_log_clear(logOCR, "Đã hủy khung vừa vẽ.");
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
    if (boxContentOCR) boxContentOCR.innerHTML = "";
    obj_region_ocr_canvas.reset();
    inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
    const activeRectangle = inspector.rectangles.find(item => item.id === activeRoiId);
    if (activeRectangle) openRectangleEditor(activeRectangle, false);
    else setRegionPanel(panner_region_ocr, null);
    updateHighlight();
    write_log_clear(logOCR, `Đã xóa khung "${rectangle.name}".`);
}

function openRectangleEditor(rectangle, isNewPending = false) {
    if (!rectangle || rectangle.xStart < 0 || !boxContentOCR) return;
    const inspector = getInspector();
    if (!inspector) return;

    activeRoiId = isNewPending ? null : rectangle.id;
    setRegionPanel(panner_region_ocr, isNewPending ? "pending" : activeRoiId, !isNewPending);
    boxContentOCR.innerHTML = "";

    const wrapper = document.createElement("div");
    wrapper.className = "region-editor";
    const nameLabel = document.createElement("label");
    nameLabel.htmlFor = "ocr-roi-name";
    nameLabel.textContent = isNewPending
        ? "Đặt tên vùng kiểm tra OCR mới"
        : "Đổi tên vùng kiểm tra OCR";

    const nameInput = document.createElement("input");
    nameInput.id = "ocr-roi-name";
    nameInput.type = "text";
    nameInput.className = "config-input";
    nameInput.placeholder = "Ví dụ: Mã sản phẩm";
    nameInput.value = rectangle.name || `Vùng OCR ${inspector.getNextId() + 1}`;

    const expectedLabel = document.createElement("label");
    expectedLabel.htmlFor = "ocr-roi-expected-text";
    expectedLabel.textContent = "Nội dung OCR bắt buộc phải nhận diện";

    const expectedInput = document.createElement("textarea");
    expectedInput.id = "ocr-roi-expected-text";
    expectedInput.className = "config-input";
    expectedInput.rows = 3;
    expectedInput.placeholder = "Nhập chính xác nội dung cần kiểm tra";
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
        const expectedText = expectedInput.value;
        if (!name) {
            write_log_clear(logOCR, "Tên vùng OCR không được để trống.");
            nameInput.focus();
            return;
        }
        if (!expectedText.trim()) {
            write_log_clear(logOCR, "Nội dung OCR bắt buộc không được để trống.");
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
            write_log_clear(logOCR, "Dữ liệu khung OCR không hợp lệ.");
            return;
        }

        boxContentOCR.innerHTML = "";
        obj_region_ocr_canvas.reset();
        activeRoiId = model.id;
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        openRectangleEditor(model, false);
        hideRegionEditor(panner_region_ocr);
        updateHighlight();
        write_log_clear(
            logOCR,
            `Đã lưu "${name}". Chọn vùng này để chạy OCR; góc xoay chỉ hiển thị, không dùng phán định.`,
        );
    };

    const handleCancel = () => {
        boxContentOCR.innerHTML = "";
        obj_region_ocr_canvas.reset();
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_ocr, null);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        write_log_clear(logOCR, isNewPending ? "Đã hủy khung vừa vẽ." : "Đã hủy chỉnh sửa vùng OCR.");
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
    boxContentOCR.appendChild(wrapper);
    requestAnimationFrame(() => nameInput.focus());
}

function updateHighlight() {
    get_obj_product()?.highlightItems(
        scroll_container,
        ItemsInspector.TYPE_OCR,
        "rectangles",
    );
}

function renderOCRResult(data = {}) {
    if (!boxContentOCR) return;
    boxContentOCR.innerHTML = "";
    const boxes = Array.isArray(data.boxes) ? data.boxes : [];
    if (!boxes.length) return;

    const isOk = data.ok === true;
    const statusColor = isOk ? "#00c853" : "#d50000";
    const wrapper = document.createElement("div");
    wrapper.style.padding = "10px";
    wrapper.style.display = "flex";
    wrapper.style.flexDirection = "column";
    wrapper.style.gap = "8px";

    const badge = document.createElement("div");
    badge.style.padding = "8px 12px";
    badge.style.borderRadius = "8px";
    badge.style.fontWeight = "bold";
    badge.style.color = statusColor;
    badge.style.border = `1.5px solid ${statusColor}`;
    badge.style.backgroundColor = isOk ? "#e8f5e9" : "#ffebee";
    badge.textContent = `${isOk ? "✓ KẾT QUẢ: OK" : "✗ KẾT QUẢ: NG"} — ${data.message || ""}`;
    wrapper.appendChild(badge);

    const table = document.createElement("table");
    table.className = "patchcore-inference-table";
    table.style.width = "100%";
    table.style.fontSize = "12px";
    const header = table.createTHead().insertRow();
    ["Vùng", "Nội dung bắt buộc", "OCR nhận diện", "Độ tin cậy", "Góc xoay", "KQ"]
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
        row.insertCell().textContent = box.name || "Vùng OCR";
        row.insertCell().textContent = box.expected_text || "";
        const recognizedCell = row.insertCell();
        recognizedCell.textContent = box.text || "Không nhận diện được chữ";
        recognizedCell.style.whiteSpace = "pre-wrap";
        const confidence = Number(box.confidence || 0);
        row.insertCell().textContent = box.has_text ? `${(confidence * 100).toFixed(1)}%` : "—";
        const angles = Array.isArray(box.lines)
            ? [...new Set(box.lines.map(line => `${line.angle}°`))].join(", ")
            : "";
        row.insertCell().textContent = angles || "—";
        const statusCell = row.insertCell();
        statusCell.textContent = box.ok ? "OK" : "NG";
        statusCell.style.color = box.ok ? "#00c853" : "#d50000";
        statusCell.style.fontWeight = "bold";
    }
    wrapper.appendChild(table);
    boxContentOCR.appendChild(wrapper);
}

runButton?.addEventListener("click", async () => {
    const version = viewVersion;
    const log = capture_log(logOCR, () =>
        version === viewVersion && canvasManager.currentTool === obj_region_ocr_canvas);
    const inspector = getInspector();
    const region = inspector?.rectangles.find(item => item.id === activeRoiId);
    if (!selected || selected.product_id < 0 || selected.frame_id < 0 || selected.items_id < 0) {
        write_log_clear(log, "Chưa chọn đầy đủ sản phẩm, frame và item.");
        return;
    }
    if (!region) {
        write_log_clear(log, "Hãy chọn một khung OCR đã lưu để chạy nhận diện.");
        return;
    }
    if (!String(region.expected_text || "").trim()) {
        write_log_clear(log, "Hãy nhập nội dung OCR bắt buộc cho vùng đang chọn.");
        return;
    }

    write_log_clear(log, "Đang chạy OCR cho vùng đang chọn...");
    try {
        const response = await postData("/law_regulation/ocr/run_model", {
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
        if (version !== viewVersion || canvasManager.currentTool !== obj_region_ocr_canvas) return;
        if (!response?.ok) {
            write_log_clear(log, `Chạy OCR thất bại: ${response?.message || "Lỗi không xác định"}`);
            return;
        }

        const data = response.data || {};
        const boxes = Array.isArray(data.boxes) ? data.boxes : [];
        inspector.setDetectionResults([], boxes);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        renderOCRResult(data);
        if (data.ok) {
            write_log_clear(log, `OCR khớp nội dung yêu cầu tại "${region.name}".`);
        } else {
            write_log_clear(log, data.message || `OCR không khớp nội dung tại "${region.name}".`);
        }
    } catch (error) {
        write_log_clear(log, `Lỗi kết nối API OCR: ${error.message}`);
    }
});

export function event_transition_items() {
    activeRoiId = null;
    viewVersion++;
    setRegionPanel(panner_region_ocr, null);
    if (boxContentOCR) boxContentOCR.innerHTML = "";
    obj_region_ocr_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();
    const inspector = getInspector();
    inspector?.removeBoxs();
    inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
    updateHighlight();
    write_log_clear(
        logOCR,
        "Vẽ 2 điểm để tạo vùng OCR; nhập nội dung bắt buộc. Chọn vùng đã lưu để chạy riêng từng ROI.",
    );
}

closeButton?.addEventListener("click", async () => {
    activeRoiId = null;
    viewVersion++;
    obj_region_ocr_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();
    canvasManager.setTool(null);
    refesh_btn();
    get_obj_product()?.clearHighlight(scroll_container);
    setNameEventActivate(null);
    if (await closeRegionPanel(panner_region_ocr)) {
        if (boxContentOCR) boxContentOCR.innerHTML = "";
    }
});
