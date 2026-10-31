import { ModelRectangle } from "../model/model_rectangle.js";
import { canvasManager, scroll_container, WIDTH_IMG_SHAPE } from "../common_value.js";
import { RectangleDrawer } from "../canvas/rectangel_drawer_canvas.js";
import { ColorItemInspector } from "../services/color_item_inspector.js";
import { ItemsInspector } from "../services/items_inspector.js";
import { postData } from "../utills/api.js";
import { drawRoi } from "../canvas/roi_style.js";
import { setRegionPanel, hideRegionEditor, closeRegionPanel } from "./region_tool_ui.js";
import {
    ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    COLOR_RECT_SHAPE_REGION_DETECT,
    additional_events,
    boxContentColor,
    create_obj_cross_item,
    get_obj_product,
    obj_region_color_canvas,
    panner_region_color,
    refesh_btn,
    selected,
    setNameEventActivate,
    write_log_append,
    write_log_clear,
    tool_log,
} from "./common_value_tool.js";

const EVENT_NAME = "color_tool";
const logColor = tool_log(EVENT_NAME);
const closeButton = document.getElementById("btn-exit-color");
const judgmentButton = document.getElementById("btn-judment-color");
let activeRoiId = null;
let viewVersion = 0;

additional_events.set(EVENT_NAME, event_transition_items);

// Đăng ký các sự kiện cơ bản từ RectangleDrawer
obj_region_color_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT,
    (rect) => openRectangleEditor(rect, true),
);
obj_region_color_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT_HAVE_ALREADY,
    selectStoredRectangle,
);
obj_region_color_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_RIGHT_RECT,
    removeStoredRectangle,
);

// Bọc onClick của RectangleDrawer để:
// Khi vẽ xong điểm thứ 2 -> TỰ ĐỘNG TRƯỢT PANEL MỞ RA NGAY LẬP TỨC (không cần click viền)
const origOnClick = obj_region_color_canvas.onClick.bind(obj_region_color_canvas);
obj_region_color_canvas.onClick = (pos, cm) => {
    const wasDrawing = obj_region_color_canvas.isDrawing;
    const hadUnsavedRect = obj_region_color_canvas.is_available_one_rect;
    origOnClick(pos, cm);

    const inspector = getInspector();
    if (!wasDrawing && obj_region_color_canvas.isDrawing) {
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_color, null);
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(cm, pos);
    }

    if (hadUnsavedRect && obj_region_color_canvas.isDrawing) {
        if (boxContentColor) boxContentColor.innerHTML = "";
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawStartPoint(cm, pos);
        return;
    }

    // Hoàn tất điểm thứ 2 của khung mới -> hiển thị khung tạm và TỰ ĐỘNG MỞ PANEL TRƯỢT SANG TRÁI
    if (wasDrawing && !obj_region_color_canvas.isDrawing && obj_region_color_canvas.is_available_one_rect) {
        inspector?.drawAll(cm, COLOR_RECT_SHAPE_REGION_DETECT);
        drawPendingRectangle(cm, obj_region_color_canvas.rect_current);
        openRectangleEditor(obj_region_color_canvas.rect_current, true);
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
        ItemsInspector.TYPE_COLOR,
        ColorItemInspector,
        "setColorItems",
    );
}

function selectStoredRectangle(coordinate) {
    if (obj_region_color_canvas.isDrawing) return;
    if (obj_region_color_canvas.is_available_one_rect && obj_region_color_canvas.isPointOnRectBorder(
        obj_region_color_canvas.rect_current, coordinate.x, coordinate.y, ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE
    )) return;

    const inspector = getInspector();
    const rectangle = inspector?.findRectangleOnBorder(
        coordinate.x,
        coordinate.y,
        ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    );
    if (!rectangle) return;

    obj_region_color_canvas.reset();
    obj_region_color_canvas.have_return = true;
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
        setRegionPanel(panner_region_color, null);
        if (boxContentColor) boxContentColor.innerHTML = "";
        inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        write_log_clear(logColor, "Đã hủy khung vừa vẽ.");
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
    if (boxContentColor) boxContentColor.innerHTML = "";
    obj_region_color_canvas.reset();
    inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
    const activeRectangle = inspector.rectangles.find(item => item.id === activeRoiId);
    if (activeRectangle) openRectangleEditor(activeRectangle, false);
    else setRegionPanel(panner_region_color, null);
    updateHighlight();
    write_log_clear(logColor, `Đã xóa khung "${rectangle.name}".`);
}

function extractAverageRgb(cm, rect) {
    if (!rect || !cm?.ctxImg) return [255, 255, 255];
    const x = Math.max(0, Math.min(rect.xStart, rect.xEnd));
    const y = Math.max(0, Math.min(rect.yStart, rect.yEnd));
    const w = Math.abs(rect.xEnd - rect.xStart);
    const h = Math.abs(rect.yEnd - rect.yStart);
    if (w <= 1 || h <= 1) return [255, 255, 255];

    try {
        const imgData = cm.ctxImg.getImageData(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
        const data = imgData.data;
        let r = 0, g = 0, b = 0;
        const total = data.length / 4;
        if (total === 0) return [255, 255, 255];
        for (let i = 0; i < data.length; i += 4) {
            r += data[i];
            g += data[i + 1];
            b += data[i + 2];
        }
        return [
            Math.round(r / total),
            Math.round(g / total),
            Math.round(b / total),
        ];
    } catch {
        return [255, 255, 255];
    }
}

// Chuyển RGB chuẩn sang CIE L*a*b* (chuẩn quốc tế giống color_service.py)
function rgbToLab(r, g, b) {
    let rLinear = r / 255.0;
    let gLinear = g / 255.0;
    let bLinear = b / 255.0;

    rLinear = (rLinear > 0.04045) ? Math.pow((rLinear + 0.055) / 1.055, 2.4) : (rLinear / 12.92);
    gLinear = (gLinear > 0.04045) ? Math.pow((gLinear + 0.055) / 1.055, 2.4) : (gLinear / 12.92);
    bLinear = (bLinear > 0.04045) ? Math.pow((bLinear + 0.055) / 1.055, 2.4) : (bLinear / 12.92);

    // sRGB sang XYZ (D65)
    let X = (rLinear * 0.4124564 + gLinear * 0.3575761 + bLinear * 0.1804375) * 100.0;
    let Y = (rLinear * 0.2126729 + gLinear * 0.7151522 + bLinear * 0.0721750) * 100.0;
    let Z = (rLinear * 0.0193339 + gLinear * 0.1191920 + bLinear * 0.9503041) * 100.0;

    // D65 reference white
    const Xn = 95.047, Yn = 100.000, Zn = 108.883;
    let xR = X / Xn, yR = Y / Yn, zR = Z / Zn;

    const f = (val) => (val > 0.008856) ? Math.cbrt(val) : (7.787 * val + 16.0 / 116.0);
    const fx = f(xR), fy = f(yR), fz = f(zR);

    const L = Math.max(0, 116.0 * fy - 16.0);
    const a = 500.0 * (fx - fy);
    const bb = 200.0 * (fy - fz);
    return [parseFloat(L.toFixed(2)), parseFloat(a.toFixed(2)), parseFloat(bb.toFixed(2))];
}

// ΔE CIE76
function deltaE76(lab1, lab2) {
    return Math.sqrt(
        Math.pow(lab1[0] - lab2[0], 2) +
        Math.pow(lab1[1] - lab2[1], 2) +
        Math.pow(lab1[2] - lab2[2], 2)
    );
}

// ΔE CIE2000 (chuẩn quốc tế theo do_mau_roi.py)
function deltaE2000(lab1, lab2) {
    const [L1, a1, b1] = lab1;
    const [L2, a2, b2] = lab2;

    const kL = 1.0, kC = 1.0, kH = 1.0;
    const C1 = Math.hypot(a1, b1);
    const C2 = Math.hypot(a2, b2);
    const Cbar = (C1 + C2) / 2.0;

    const G = 0.5 * (1.0 - Math.sqrt(Math.pow(Cbar, 7) / (Math.pow(Cbar, 7) + Math.pow(25.0, 7))));
    const a1p = (1.0 + G) * a1;
    const a2p = (1.0 + G) * a2;

    const C1p = Math.hypot(a1p, b1);
    const C2p = Math.hypot(a2p, b2);

    const hueAngle = (ap, b) => {
        if (ap === 0 && b === 0) return 0.0;
        let h = Math.atan2(b, ap) * (180.0 / Math.PI);
        return h < 0 ? h + 360.0 : h;
    };

    const h1p = hueAngle(a1p, b1);
    const h2p = hueAngle(a2p, b2);

    const dLp = L2 - L1;
    const dCp = C2p - C1p;

    let dhp = 0.0;
    if (C1p * C2p !== 0) {
        let diff = h2p - h1p;
        if (diff > 180.0) diff -= 360.0;
        else if (diff < -180.0) diff += 360.0;
        dhp = diff;
    }

    const dHp = 2.0 * Math.sqrt(C1p * C2p) * Math.sin((dhp / 2.0) * (Math.PI / 180.0));
    const Lbar_p = (L1 + L2) / 2.0;
    const Cbar_p = (C1p + C2p) / 2.0;

    let Hbar_p = 0.0;
    if (C1p * C2p === 0) {
        Hbar_p = h1p + h2p;
    } else {
        const s = h1p + h2p;
        const diff = Math.abs(h1p - h2p);
        if (diff > 180.0) {
            Hbar_p = s < 360.0 ? (s + 360.0) / 2.0 : (s - 360.0) / 2.0;
        } else {
            Hbar_p = s / 2.0;
        }
    }

    const rad = Math.PI / 180.0;
    const T = 1.0 - 0.17 * Math.cos((Hbar_p - 30.0) * rad)
        + 0.24 * Math.cos(2.0 * Hbar_p * rad)
        + 0.32 * Math.cos((3.0 * Hbar_p + 6.0) * rad)
        - 0.20 * Math.cos((4.0 * Hbar_p - 63.0) * rad);

    const dTheta = 30.0 * Math.exp(-Math.pow((Hbar_p - 275.0) / 25.0, 2));
    const Rc = 2.0 * Math.sqrt(Math.pow(Cbar_p, 7) / (Math.pow(Cbar_p, 7) + Math.pow(25.0, 7)));
    const Sl = 1.0 + (0.015 * Math.pow(Lbar_p - 50.0, 2)) / Math.sqrt(20.0 + Math.pow(Lbar_p - 50.0, 2));
    const Sc = 1.0 + 0.045 * Cbar_p;
    const Sh = 1.0 + 0.015 * Cbar_p * T;
    const Rt = -Math.sin(2.0 * dTheta * rad) * Rc;

    return Math.sqrt(
        Math.pow(dLp / (kL * Sl), 2) +
        Math.pow(dCp / (kC * Sc), 2) +
        Math.pow(dHp / (kH * Sh), 2) +
        Rt * (dCp / (kC * Sc)) * (dHp / (kH * Sh))
    );
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
    if (!rectangle || rectangle.xStart < 0 || !boxContentColor) return;
    const inspector = getInspector();
    if (!inspector) return;
    activeRoiId = isNewPending ? null : rectangle.id;

    // Tự động kích hoạt hiệu ứng trượt Panel từ phải sang trái
    setRegionPanel(panner_region_color, isNewPending ? "pending" : activeRoiId, !isNewPending);

    boxContentColor.innerHTML = "";
    const wrapper = document.createElement("div");
    wrapper.className = "region-editor";

    const table = document.createElement("table");
    table.className = "measure-weld-width-config-table";

    // Đo màu tức thì từ vùng ROI trên canvas
    const measuredRgb = extractAverageRgb(canvasManager, rectangle);
    const measuredLab = rgbToLab(...measuredRgb);

    // Giá trị tham chiếu đã lưu hoặc lấy từ đo tức thời
    let refRgb = Array.isArray(rectangle.ref_rgb) ? [...rectangle.ref_rgb] : [...measuredRgb];
    let refLab = Array.isArray(rectangle.ref_lab) ? [...rectangle.ref_lab] : rgbToLab(...refRgb);

    // 1. Tên khung
    const inputName = document.createElement("input");
    inputName.type = "text";
    inputName.className = "config-input";
    inputName.placeholder = "Ví dụ: Màu tem 1";
    inputName.value = rectangle.name || `Vùng màu ${inspector.getNextId() + 1}`;

    // 2. Màu chuẩn (Swatch + Mã màu Hex/Picker)
    const refContainer = document.createElement("div");
    refContainer.className = "color-preview-container";

    const refSwatch = document.createElement("span");
    refSwatch.className = "color-swatch-box";
    refSwatch.style.backgroundColor = `rgb(${refRgb.join(",")})`;

    const refColorPicker = document.createElement("input");
    refColorPicker.type = "color";
    refColorPicker.style.width = "30px";
    refColorPicker.style.height = "26px";
    refColorPicker.style.padding = "0";
    refColorPicker.style.border = "none";
    refColorPicker.style.cursor = "pointer";
    const toHex = (c) => "#" + c.map(x => x.toString(16).padStart(2, "0")).join("");
    refColorPicker.value = toHex(refRgb);

    const refText = document.createElement("span");
    refText.className = "color-chip-text";
    refText.textContent = `RGB(${refRgb.join(",")})`;

    const btnPickCurrent = document.createElement("button");
    btnPickCurrent.type = "button";
    btnPickCurrent.className = "color-btn-pick";
    btnPickCurrent.textContent = "Lấy màu ROI";
    btnPickCurrent.title = "Đặt màu đo được của ROI này làm màu chuẩn";

    refContainer.append(refSwatch, refColorPicker, refText, btnPickCurrent);

    // 3. Màu đo được tức thì từ ảnh ROI
    const measContainer = document.createElement("div");
    measContainer.className = "color-preview-container";

    const measSwatch = document.createElement("span");
    measSwatch.className = "color-swatch-box";
    measSwatch.style.backgroundColor = `rgb(${measuredRgb.join(",")})`;

    const measText = document.createElement("span");
    measText.className = "color-chip-text";
    measText.innerHTML = `RGB(${measuredRgb.join(",")})<br>Lab(${measuredLab.join(", ")})`;
    measContainer.append(measSwatch, measText);

    // 4. Ngưỡng ΔE max (CIE2000)
    const inpMaxDe = document.createElement("input");
    inpMaxDe.type = "number";
    inpMaxDe.step = "0.5";
    inpMaxDe.min = "0.5";
    inpMaxDe.className = "config-input";
    inpMaxDe.value = rectangle.max_delta_e !== undefined ? rectangle.max_delta_e : 5.0;

    // 5. Sai lệch tức thời
    const diffContainer = document.createElement("div");
    diffContainer.className = "color-chip-text";
    const updateDiffView = () => {
        const de00 = deltaE2000(refLab, measuredLab);
        const de76 = deltaE76(refLab, measuredLab);
        const sim = Math.max(0, Math.min(100, (1.0 - de00 / 100.0) * 100.0));
        const maxLimit = parseFloat(inpMaxDe.value) || 5.0;
        const isOk = de00 <= maxLimit;
        diffContainer.innerHTML = `
            <strong>ΔE00:</strong> <span style="color:${isOk ? '#00c853' : '#d50000'}; font-weight:bold;">${de00.toFixed(2)}</span> / max ${maxLimit} (${isOk ? 'ĐẠT' : 'LỆCH'})<br>
            <strong>ΔE76:</strong> ${de76.toFixed(2)} | <strong>Tương đồng:</strong> ${sim.toFixed(1)}%
        `;
    };
    updateDiffView();

    refColorPicker.addEventListener("input", (e) => {
        const hex = e.target.value;
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        refRgb = [r, g, b];
        refLab = rgbToLab(r, g, b);
        refSwatch.style.backgroundColor = hex;
        refText.textContent = `RGB(${r},${g},${b})`;
        updateDiffView();
    });

    btnPickCurrent.addEventListener("click", () => {
        refRgb = [...measuredRgb];
        refLab = [...measuredLab];
        refSwatch.style.backgroundColor = `rgb(${refRgb.join(",")})`;
        refColorPicker.value = toHex(refRgb);
        refText.textContent = `RGB(${refRgb.join(",")})`;
        updateDiffView();
    });

    inpMaxDe.addEventListener("input", updateDiffView);

    table.append(
        createConfigRow(isNewPending ? "Tên vùng mới" : "Tên vùng", inputName),
        createConfigRow("Màu chuẩn", refContainer),
        createConfigRow("Màu đo được", measContainer),
        createConfigRow("ΔE max cho phép", inpMaxDe),
        createConfigRow("Sai lệch tức thời", diffContainer),
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
            write_log_clear(logColor, "❌ Tên vùng kiểm tra màu không được để trống.");
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
        model.max_delta_e = parseFloat(inpMaxDe.value) || 5.0;
        model.ref_rgb = refRgb;
        model.ref_lab = refLab;

        if (!model.isValid() || !inspector.addRectangle(model)) {
            write_log_clear(logColor, "❌ Dữ liệu khung kiểm tra màu không hợp lệ.");
            return;
        }
        boxContentColor.innerHTML = "";
        obj_region_color_canvas.reset();
        activeRoiId = model.id;
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        openRectangleEditor(model, false);
        hideRegionEditor(panner_region_color);
        updateHighlight();
        write_log_clear(
            logColor,
            `✅ Đã lưu vùng "${name}" (Chuẩn RGB: [${refRgb.join(', ')}], Ngưỡng ΔE=${model.max_delta_e}). Có thể tiếp tục vẽ vùng khác.`,
        );
    };

    const handleCancel = () => {
        boxContentColor.innerHTML = "";
        obj_region_color_canvas.reset();
        activeRoiId = null;
        viewVersion++;
        setRegionPanel(panner_region_color, null);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
        write_log_clear(
            logColor,
            isNewPending ? "Đã hủy khung vừa vẽ." : "Đã hủy chỉnh sửa cấu hình màu.",
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
    boxContentColor.appendChild(wrapper);

    requestAnimationFrame(() => {
        inputName.focus();
        inputName.select();
    });
}

function updateHighlight() {
    get_obj_product()?.highlightItems(
        scroll_container,
        ItemsInspector.TYPE_COLOR,
        "rectangles",
    );
}

function renderColorResultSummary(data = {}) {
    if (!boxContentColor) return;
    boxContentColor.innerHTML = "";

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

    // Badge tổng quan (giống Ảnh 3)
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
    titleSpan.textContent = allOk ? "✓ KẾT QUẢ: ĐẠT (OK)" : "✗ KẾT QUẢ: LỆCH MÀU (NG)";
    const subSpan = document.createElement("span");
    subSpan.style.fontSize = "11px";
    subSpan.textContent = `${okCount}/${boxResults.length} khung đạt`;
    badge.append(titleSpan, subSpan);
    wrapper.appendChild(badge);

    // Bảng chi tiết: Khung | Chuẩn / Đo | ΔE00 | % Giống | Kết quả (giống Ảnh 3)
    const table = document.createElement("table");
    table.className = "color-summary-table stamp-alignment-summary-table";

    const thead = table.createTHead();
    const headerRow = thead.insertRow();
    ["Khung", "Chuẩn / Đo", "ΔE00", "% Giống", "Kết quả"].forEach((headerText) => {
        const th = document.createElement("th");
        th.textContent = headerText;
        headerRow.appendChild(th);
    });

    const tbody = table.createTBody();
    boxResults.forEach((box, idx) => {
        const row = tbody.insertRow();
        const isOk = box.status === "OK";

        // 1. Tên khung (in đậm, căn trái)
        const cellName = row.insertCell();
        cellName.textContent = box.name || `Vùng màu ${idx + 1}`;
        cellName.style.setProperty("font-weight", "bold", "important");
        cellName.style.setProperty("color", "#1a202c", "important");
        cellName.style.setProperty("text-align", "left", "important");
        cellName.style.setProperty("padding-left", "8px", "important");

        // 2. Chuẩn / Đo (2 ô màu mẫu và mũi tên)
        const cellSwatch = row.insertCell();
        cellSwatch.style.setProperty("text-align", "center", "important");
        cellSwatch.style.setProperty("vertical-align", "middle", "important");
        const refRgb = box.ref_rgb || [255, 255, 255];
        const measRgb = box.measured_rgb || [255, 255, 255];

        const sw1 = document.createElement("span");
        sw1.className = "color-swatch-badge";
        sw1.style.backgroundColor = `rgb(${refRgb.join(",")})`;
        sw1.title = `Màu chuẩn: RGB(${refRgb.join(",")})`;

        const arrow = document.createElement("span");
        arrow.textContent = " ➔ ";
        arrow.style.fontSize = "11px";
        arrow.style.color = "#78909c";
        arrow.style.margin = "0 3px";

        const sw2 = document.createElement("span");
        sw2.className = "color-swatch-badge";
        sw2.style.backgroundColor = `rgb(${measRgb.join(",")})`;
        sw2.title = `Màu đo được: RGB(${measRgb.join(",")})`;

        cellSwatch.append(sw1, arrow, sw2);

        // 3. ΔE00
        const cellDe = row.insertCell();
        const deVal = Number(box.delta_e00 !== undefined ? box.delta_e00 : box.delta_e !== undefined ? box.delta_e : 0);
        const maxLimit = Number(box.max_delta_e || 5.0);
        cellDe.textContent = `${deVal.toFixed(2)}`;
        cellDe.title = `Dung sai tối đa: ${maxLimit}`;
        if (!isOk || deVal > maxLimit) {
            cellDe.style.setProperty("color", "#d50000", "important");
            cellDe.style.setProperty("font-weight", "bold", "important");
        } else {
            cellDe.style.setProperty("color", "#2c3e50", "important");
        }

        // 4. % Giống
        const cellSim = row.insertCell();
        const simVal = Number(box.similarity !== undefined ? box.similarity : box.similarity_percent !== undefined ? box.similarity_percent : 100);
        cellSim.textContent = `${simVal.toFixed(1)}%`;
        if (simVal < 80) {
            cellSim.style.setProperty("color", "#d50000", "important");
            cellSim.style.setProperty("font-weight", "bold", "important");
        } else {
            cellSim.style.setProperty("color", "#2c3e50", "important");
        }

        // 5. Kết quả (OK: xanh, NG: đỏ)
        const cellStatus = row.insertCell();
        cellStatus.textContent = isOk ? "OK" : "NG";
        cellStatus.style.setProperty("font-weight", "bold", "important");
        cellStatus.style.setProperty("color", isOk ? "#00c853" : "#d50000", "important");
    });

    wrapper.appendChild(table);
    boxContentColor.appendChild(wrapper);
}

// Chạy đo thử màu bằng nút Chạy model
judgmentButton?.addEventListener("click", async () => {
    const inspector = getInspector();
    if (!inspector || !inspector.rectangles.length) {
        write_log_clear(logColor, "⚠️ Vui lòng vẽ ít nhất một vùng để đo màu.");
        return;
    }
    if (selected.product_id < 0 || selected.frame_id < 0 || selected.items_id < 0) {
        write_log_clear(logColor, "⚠️ Vui lòng chọn một ảnh hợp lệ trước khi đo.");
        return;
    }

    const payload = {
        select: {
            product_id: selected.product_id,
            frame_id: selected.frame_id,
            items_id: selected.items_id,
        },
        boxes: inspector.rectangles.map(r => ({
            id: r.id,
            name: r.name,
            xStart: r.xStart,
            yStart: r.yStart,
            xEnd: r.xEnd,
            yEnd: r.yEnd,
            max_delta_e: r.max_delta_e ?? 5.0,
            ref_rgb: r.ref_rgb ?? [255, 255, 255],
            ref_lab: r.ref_lab ?? null,
        })),
        WidthCanvas: WIDTH_IMG_SHAPE,
    };

    write_log_clear(logColor, "📡 Đang đo màu bằng backend...");
    try {
        const res = await postData("/law_regulation/color/run_model", payload);
        if (!res?.ok) {
            write_log_clear(logColor, `❌ Lỗi đo màu: ${res?.message || "Không xác định"}`);
            return;
        }

        const data = res.data || {};
        const boxResults = Array.isArray(data.boxes) ? data.boxes : [];
        inspector.setDetectionResults([], boxResults);
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
        renderColorResultSummary(data);

        const ngBoxes = boxResults.filter(item => item.status !== "OK");
        if (ngBoxes.length === 0) {
            write_log_clear(
                logColor,
                `✅ Tất cả ${boxResults.length} vùng kiểm tra màu đều ĐẠT (sai lệch màu trong giới hạn cho phép).`,
            );
        } else {
            write_log_clear(
                logColor,
                `❌ Phát hiện ${ngBoxes.length}/${boxResults.length} vùng sai lệch màu vượt ngưỡng:`,
            );
            ngBoxes.forEach(b => {
                write_log_append(
                    logColor,
                    ` - [Kiểm tra màu] NG - Vùng "${b.name}": ΔE00 = ${b.delta_e00} (ngưỡng ${b.max_delta_e}), Tương đồng = ${b.similarity}%`,
                );
            });
        }
    } catch (err) {
        write_log_clear(logColor, `❌ Lỗi kết nối API đo màu: ${err.message}`);
    }
});

export function event_transition_items() {
    activeRoiId = null;
    viewVersion++;
    setRegionPanel(panner_region_color, null);
    if (boxContentColor) boxContentColor.innerHTML = "";
    obj_region_color_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();

    const inspector = getInspector();
    inspector?.removeBoxs();
    inspector?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT);
    updateHighlight();
    write_log_clear(
        logColor,
        "Vẽ 2 điểm trên ảnh để chọn vùng kiểm tra màu. Vùng vẽ xong sẽ tự động trượt mở panel cấu hình.",
    );
}

closeButton?.addEventListener("click", async () => {
    activeRoiId = null;
    viewVersion++;
    obj_region_color_canvas.reset();
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();
    canvasManager.setTool(null);
    refesh_btn();
    get_obj_product()?.clearHighlight(scroll_container);
    setNameEventActivate(null);
    if (await closeRegionPanel(panner_region_color)) {
        if (boxContentColor) boxContentColor.innerHTML = "";
    }
});
