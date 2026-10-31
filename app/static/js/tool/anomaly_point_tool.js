import { canvasManager, scroll_container, WIDTH_IMG_SHAPE } from "../common_value.js";
import { RectangleDrawer } from "../canvas/rectangel_drawer_canvas.js";
import { ItemsInspector } from "../services/items_inspector.js";
import { AnomalyPointInspector, AnomalyPointRegion } from "../services/anomaly_point_item_inspector.js";
import { postData } from "../utills/api.js";
import { drawRoi } from "../canvas/roi_style.js";
import { setRegionPanel, hideRegionEditor, closeRegionPanel, createRegionList, updateRegionModelStatus } from "./region_tool_ui.js";
import {
    ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    COLOR_RECT_SHAPE_REGION_DETECT,
    additional_events,
    boxContentAnomalyPoint,
    create_obj_cross_item,
    get_obj_product,
    obj_region_anomaly_point_canvas,
    panner_region_anomaly_point,
    refesh_btn,
    selected,
    setNameEventActivate,
    write_log_append,
    write_log_clear,
    tool_log,
    capture_log,
} from "./common_value_tool.js";

const EVENT_NAME = "anomaly-point-tool";
const API_BASE = "/law_regulation/anomaly_point";
const DEFAULT_THRESHOLD = 0.2;

const logAnomaly = tool_log(EVENT_NAME);
const btnCreateModel = document.getElementById("btn-create-model-anomaly-point");
const btnRuntimeImages = document.getElementById("btn-runtime-images-anomaly-point");
const btnRunModel = document.getElementById("btn-judment-anomaly-point");
const btnDeleteModel = document.getElementById("btn-delete-model-anomaly-point");
const btnExit = document.getElementById("btn-exit-anomaly-point");
const loadingPanel = document.getElementById("loading");
const loadingStatus = document.getElementById("loading-status");
const loadingBar = document.getElementById("loading-bar");
const loadingPercent = document.getElementById("loading-percent");

const runtimeImagesPanel = document.getElementById("runtime-train-images-panel-anomaly-point");
const resultPanel = document.getElementById("patchcore-result-panel-anomaly-point");
const anomalyPanels = [boxContentAnomalyPoint, runtimeImagesPanel, resultPanel];

/** Khung đang được chọn để các nút trong controler-tool thao tác (null nếu chưa chọn). */
let activeRoiId = null;
let viewVersion = 0;

function isCurrentContext(context, version) {
    return version === viewVersion && canvasManager.currentTool === obj_region_anomaly_point_canvas &&
        String(context.product_id) === String(selected.product_id) &&
        String(context.frame_id) === String(selected.frame_id) &&
        String(context.item_id) === String(selected.items_id) && context.roi_id === activeRoiId;
}

additional_events.set(EVENT_NAME, event_transition_items);

function activatePanel(activePanel) {
    anomalyPanels.forEach(panel => {
        if (panel) panel.hidden = panel !== activePanel;
    });
}
anomalyPanels.forEach(panel => {
    if (panel) panel.hidden = true;
});

// ==========================================
// TIỆN ÍCH
// ==========================================
function getInspector() {
    return create_obj_cross_item(
        ItemsInspector.TYPE_ANOMALY_POINT,
        AnomalyPointInspector,
        "setAnomalyPointItems",
    );
}

function updateHighlight() {
    get_obj_product()?.highlightItems(scroll_container, ItemsInspector.TYPE_ANOMALY_POINT, "regions");
}

function redrawAll() {
    getInspector()?.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, activeRoiId);
}

function hasValidSelection() {
    return selected.product_id >= 0 && selected.frame_id >= 0 && selected.items_id >= 0;
}

function drawPendingRectangle(rect, color = "#00B0FF") {
    if (!rect || rect.width <= 0 || rect.height <= 0) return;
    drawRoi(canvasManager.ctxShape, rect, {pending: true});
}

function drawStartPoint(pos) {
    const ctx = canvasManager.ctxShape;
    ctx.save();
    ctx.fillStyle = "#FF1744";
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
}

function clearResultViews() {
    if (resultPanel) resultPanel.innerHTML = "";
    if (runtimeImagesPanel) {
        runtimeImagesPanel.innerHTML = "";
        runtimeImagesPanel.hidden = true;
    }
}

/** Lấy khung đang chọn; ghi log nhắc nhở nếu chưa chọn. */
function requireActiveRegion() {
    if (!hasValidSelection()) {
        write_log_append(logAnomaly, "❌ Chưa xác định được product, frame hoặc item.");
        return null;
    }
    const inspector = getInspector();
    const region = activeRoiId === null ? null : inspector?.getRegionById(activeRoiId);
    if (!region || !region.isValid()) {
        write_log_append(
            logAnomaly,
            "⚠️ Vui lòng click vào viền một khung bất thường đã lưu để chọn trước khi thao tác.",
        );
        return null;
    }
    return region;
}

function selectRegion(region) {
    viewVersion++;
    activeRoiId = region ? region.id : null;
    setRegionPanel(panner_region_anomaly_point, activeRoiId, Boolean(region));
    clearResultViews();
    redrawAll();
}

// ==========================================
// SỰ KIỆN CANVAS
// ==========================================
obj_region_anomaly_point_canvas.on(RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT, (rect) => {
    // Click vào viền khung vừa vẽ (chưa lưu) -> mở bảng đặt Tên + Ngưỡng cho khung mới
    openRegionEditor(null, rect);
});
obj_region_anomaly_point_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_ON_RECT_HAVE_ALREADY,
    selectStoredRegion,
);
obj_region_anomaly_point_canvas.on(
    RectangleDrawer.NAME_EVENT_WHEN_CLICK_RIGHT_RECT,
    removeStoredRegion,
);

// Bọc onClick để các khung đã lưu không bị xóa khỏi Canvas khi người dùng bỏ khung tạm / vẽ khung mới.
const origOnClick = obj_region_anomaly_point_canvas.onClick.bind(obj_region_anomaly_point_canvas);
obj_region_anomaly_point_canvas.onClick = (pos, cm) => {
    const wasDrawing = obj_region_anomaly_point_canvas.isDrawing;
    const hadUnsavedRect = obj_region_anomaly_point_canvas.is_available_one_rect;
    origOnClick(pos, cm);
    if (!wasDrawing && obj_region_anomaly_point_canvas.isDrawing) {
        selectRegion(null);
        drawStartPoint(pos);
        if (boxContentAnomalyPoint) boxContentAnomalyPoint.innerHTML = "";
    }

    // Bỏ khung tạm chưa lưu để bắt đầu vẽ khung mới -> vẽ lại các khung đã lưu
    if (hadUnsavedRect && obj_region_anomaly_point_canvas.isDrawing) {
        if (boxContentAnomalyPoint) boxContentAnomalyPoint.innerHTML = "";
        redrawAll();
        drawStartPoint(pos);
        return;
    }

    // Hoàn tất điểm thứ 2 -> hiển thị lại khung đã lưu + khung tạm (người dùng click viền để mở bảng cấu hình)
    if (
        wasDrawing &&
        !obj_region_anomaly_point_canvas.isDrawing &&
        obj_region_anomaly_point_canvas.is_available_one_rect
    ) {
        redrawAll();
        drawPendingRectangle(obj_region_anomaly_point_canvas.rect_current);
        openRegionEditor(null, obj_region_anomaly_point_canvas.rect_current);
    }
};

function selectStoredRegion(coordinate) {
    // Không chặn click thứ 2 khi đang vẽ dở khung mới
    if (obj_region_anomaly_point_canvas.isDrawing) return;
    if (obj_region_anomaly_point_canvas.is_available_one_rect && obj_region_anomaly_point_canvas.isPointOnRectBorder(
        obj_region_anomaly_point_canvas.rect_current, coordinate.x, coordinate.y, ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE
    )) return;
    const inspector = getInspector();
    const region = inspector?.findRegionOnBorder(
        coordinate.x,
        coordinate.y,
        ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    );
    if (!region) return;

    obj_region_anomaly_point_canvas.reset();
    obj_region_anomaly_point_canvas.have_return = true;
    selectRegion(region);
    openRegionEditor(region, region);
    write_log_clear(logAnomaly, `✅ Đã chọn vùng "${region.name}" (ID ${region.id}).`);
}

function removeStoredRegion(payload) {
    const inspector = getInspector();
    if (!inspector) return;

    // Click phải trúng khung tạm chưa lưu: drawer đã tự xóa canvas -> vẽ lại các khung đã lưu
    if (payload?.status_check_point_in_rect_current) {
        selectRegion(null);
        if (boxContentAnomalyPoint) boxContentAnomalyPoint.innerHTML = "";
        redrawAll();
        write_log_clear(logAnomaly, "Đã hủy khung vừa vẽ.");
        return;
    }

    const region = inspector.findRegionOnBorder(
        payload.x,
        payload.y,
        ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE,
    );
    if (!region) return;

    removeRegion(region);
}

function removeRegion(region) {
    const inspector = getInspector();
    inspector.removeRegion(region.id);
    if (boxContentAnomalyPoint) boxContentAnomalyPoint.innerHTML = "";
    obj_region_anomaly_point_canvas.reset();
    const activeRegion = activeRoiId === null ? null : inspector.getRegionById(activeRoiId);
    selectRegion(activeRegion);
    if (activeRegion) openRegionEditor(activeRegion, activeRegion);
    updateHighlight();
    write_log_clear(
        logAnomaly,
        `Đã xóa khung "${region.name}". Bấm "Lưu" để cập nhật và dọn model của khung này.`,
    );
}

// ==========================================
// BẢNG CẤU HÌNH 1 KHUNG (Tên + Ngưỡng + Lưu ảnh train)
// ==========================================
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

/**
 * Mở bảng cấu hình cho một khung.
 * @param {AnomalyPointRegion|null} existingRegion Khung đã lưu (null nếu là khung mới vừa vẽ).
 * @param {object} rect Tọa độ khung {xStart, yStart, xEnd, yEnd}.
 */
function openRegionEditor(existingRegion, rect) {
    if (!rect || rect.xStart < 0 || !boxContentAnomalyPoint) return;
    const inspector = getInspector();
    if (!inspector) return;
    activeRoiId = existingRegion ? existingRegion.id : null;
    setRegionPanel(panner_region_anomaly_point, existingRegion ? existingRegion.id : "pending", Boolean(existingRegion));

    clearResultViews();
    activatePanel(boxContentAnomalyPoint);
    boxContentAnomalyPoint.innerHTML = "";
    const version = viewVersion;
    boxContentAnomalyPoint.appendChild(createRegionList(inspector.regions, activeRoiId, {
        select: region => {
            obj_region_anomaly_point_canvas.reset();
            selectRegion(region);
            openRegionEditor(region, region);
        },
        remove: removeRegion,
        statusUrl: region => `${API_BASE}/train_status?${new URLSearchParams(baseQuery(region))}`,
        isCurrent: () => version === viewVersion && canvasManager.currentTool === obj_region_anomaly_point_canvas,
        onError: (region, error) => write_log_append(logAnomaly, `❌ ${region.name}: ${error.message}`),
    }));

    const regionId = existingRegion ? existingRegion.id : inspector.getNextId();
    const wrapper = document.createElement("div");
    wrapper.id = "measure-anomaly-point-wrapper";
    wrapper.className = "region-editor";

    const table = document.createElement("table");
    table.className = "measure-weld-width-config-table";

    const nameInput = document.createElement("input");
    nameInput.className = "config-input";
    nameInput.type = "text";
    nameInput.placeholder = "Nhập tên vùng";
    nameInput.value = existingRegion?.name ?? `Điểm bất thường ${regionId + 1}`;

    const thresholdInput = document.createElement("input");
    thresholdInput.className = "config-input";
    thresholdInput.type = "number";
    thresholdInput.min = "0";
    thresholdInput.max = "1";
    thresholdInput.step = "any";
    thresholdInput.placeholder = "Nhập ngưỡng NG (0 - 1)";
    thresholdInput.value = existingRegion?.threshold ?? DEFAULT_THRESHOLD;

    const saveToggle = document.createElement("input");
    saveToggle.type = "checkbox";
    saveToggle.id = "save-runtime-images-anomaly-point";
    saveToggle.className = "end-chipping-save-runtime-toggle";
    saveToggle.checked = Boolean(existingRegion?.saveRuntimeImages);
    const saveSwitch = document.createElement("label");
    saveSwitch.className = "end-chipping-save-runtime-switch";
    saveSwitch.htmlFor = saveToggle.id;
    saveSwitch.title = "Bật để runtime lưu ảnh tại vùng này làm dữ liệu train PatchCore cho lần tạo model sau.";
    const saveControl = document.createElement("div");
    saveControl.className = "end-chipping-save-runtime-control";
    saveControl.append(saveToggle, saveSwitch);

    table.append(
        createConfigRow("Tên vùng", nameInput),
        createConfigRow("Ngưỡng bất thường", thresholdInput),
        createConfigRow("Lưu ảnh train", saveControl),
    );

    const actions = document.createElement("div");
    actions.className = "config-actions";

    const btnAccept = document.createElement("button");
    btnAccept.className = "btn btn-accept";
    btnAccept.textContent = "Chấp nhận";
    btnAccept.addEventListener("click", () => {
        if (!nameInput.value.trim()) {
            write_log_clear(logAnomaly, "❌ Tên vùng không được để trống.");
            nameInput.focus();
            return;
        }
        const threshold = Number(thresholdInput.value);
        if (thresholdInput.value === "" || !Number.isFinite(threshold) || threshold < 0 || threshold > 1) {
            write_log_clear(logAnomaly, "❌ Ngưỡng bất thường phải là số trong khoảng từ 0 đến 1.");
            thresholdInput.focus();
            return;
        }
        const region = new AnomalyPointRegion(
            regionId,
            nameInput.value.trim(),
            rect.xStart,
            rect.yStart,
            rect.xEnd,
            rect.yEnd,
            threshold,
            saveToggle.checked,
        );
        if (!region.isValid()) {
            write_log_clear(logAnomaly, "❌ Tên vùng không được để trống và khung phải hợp lệ.");
            nameInput.focus();
            return;
        }
        inspector.addOrUpdateRegion(region);
        activeRoiId = region.id;
        obj_region_anomaly_point_canvas.reset();
        boxContentAnomalyPoint.innerHTML = "";
        redrawAll();
        openRegionEditor(region, region);
        hideRegionEditor(panner_region_anomaly_point);
        updateHighlight();
        write_log_clear(
            logAnomaly,
            `✅ Đã lưu vùng "${region.name}" (ID ${region.id}, ngưỡng ${region.threshold}). ` +
            "Có thể vẽ thêm vùng khác hoặc dùng các nút bên dưới cho vùng đang chọn.",
        );
    });

    const btnClear = document.createElement("button");
    btnClear.className = "btn btn-clear";
    btnClear.textContent = "Hủy";
    btnClear.addEventListener("click", () => {
        obj_region_anomaly_point_canvas.reset();
        canvasManager.clearPreviewCanvas();
        boxContentAnomalyPoint.innerHTML = "";
        selectRegion(null);
    });

    actions.append(btnAccept, btnClear);
    wrapper.append(table, actions);
    boxContentAnomalyPoint.appendChild(wrapper);
}

// ==========================================
// CÁC NÚT TRONG CONTROLER-TOOL (theo khung đang chọn)
// ==========================================
function setBusy(busy) {
    if (panner_region_anomaly_point) panner_region_anomaly_point.style.pointerEvents = busy ? "none" : "";
    if (loadingPanel) loadingPanel.style.display = busy ? "flex" : "none";
}

function setProgress(percent, message) {
    if (loadingBar) loadingBar.style.width = `${percent}%`;
    if (loadingPercent) loadingPercent.textContent = `${percent}%`;
    if (loadingStatus && message) loadingStatus.textContent = message;
}

function baseQuery(region) {
    return {
        product_id: selected.product_id,
        frame_id: selected.frame_id,
        item_id: selected.items_id,
        roi_id: region.id,
    };
}

function cropRoiOf(region, withThreshold = false) {
    const roi = {
        xStart: region.xStart,
        yStart: region.yStart,
        xEnd: region.xEnd,
        yEnd: region.yEnd,
    };
    if (withThreshold) roi.threshold = region.threshold;
    return roi;
}

async function waitForTraining(region, context) {
    setBusy(true);
    setProgress(10, `Đang tạo model PatchCore cho "${region.name}"...`);
    let progress = 10;
    const timer = setInterval(() => {
        if (progress < 95) {
            progress += 1;
            setProgress(progress, "Đang train model...");
        }
    }, 300);
    try {
        for (let attempt = 0; attempt < 600; attempt++) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            const query = new URLSearchParams(context);
            const response = await fetch(`${API_BASE}/train_status?${query}`, {
                headers: { "Accept": "application/json" },
            });
            const text = await response.text();
            let status;
            try {
                status = JSON.parse(text);
            } catch (error) {
                throw new Error(`API trạng thái trả dữ liệu không hợp lệ (HTTP ${response.status})`);
            }
            if (!response.ok || !status?.ok) {
                throw new Error(
                    status?.message || status?.error_name ||
                    `Không đọc được trạng thái train (HTTP ${response.status})`,
                );
            }
            if (status.data?.completed) {
                setProgress(100, "Hoàn thành");
                return;
            }
        }
        throw new Error("Train model quá thời gian chờ");
    } finally {
        clearInterval(timer);
    }
}

btnCreateModel?.addEventListener("click", async () => {
    const region = requireActiveRegion();
    if (!region) return;
    const context = baseQuery(region);
    const version = viewVersion;
    const logAnomaly = capture_log(tool_log(EVENT_NAME), () => isCurrentContext(context, version));
    try {
        const response = await postData(`${API_BASE}/create_model`, {
            ...context, crop_roi: cropRoiOf(region), width_canvas: WIDTH_IMG_SHAPE, image_count: 16,
        });
        if (!response?.ok) throw new Error(response?.message || "Không thể bắt đầu tạo model.");
        write_log_append(logAnomaly, `✅ Đã đưa yêu cầu tạo model vùng "${region.name}" vào luồng train.`);
        await waitForTraining(region, context);
        if (isCurrentContext(context, version)) {
            updateRegionModelStatus(panner_region_anomaly_point, region.id, true);
        }
        write_log_append(logAnomaly, `✅ Tạo model vùng "${region.name}" hoàn tất.`);
    } catch (error) {
        write_log_append(logAnomaly, `❌ ${error.message}`);
    } finally {
        setBusy(false);
    }
});

btnRunModel?.addEventListener("click", async () => {
    const region = requireActiveRegion();
    if (!region) return;
    const context = baseQuery(region);
    const version = viewVersion;
    const logAnomaly = capture_log(tool_log(EVENT_NAME), () => isCurrentContext(context, version));
    write_log_append(logAnomaly, `⏳ Đang chạy model PatchCore vùng "${region.name}"...`);
    try {
        const response = await postData(`${API_BASE}/run_model`, {
            ...context,
            crop_roi: cropRoiOf(region, true),
            width_canvas: WIDTH_IMG_SHAPE,
        });
        if (!response?.ok) {
            write_log_append(logAnomaly, `❌ ${response?.message || "Chạy model thất bại (vùng này đã tạo model chưa?)."}`);
            return;
        }
        if (!isCurrentContext(context, version)) return;
        renderPatchCoreResult(response.data || {}, region);
        write_log_append(logAnomaly, `✅ Đã chạy model PatchCore vùng "${region.name}".`);
    } catch (error) {
        write_log_append(logAnomaly, `❌ ${error.message}`);
    }
});

function renderPatchCoreResult(data, region) {
    if (!resultPanel) return;
    activatePanel(resultPanel);
    resultPanel.innerHTML = "";

    const image = document.createElement("img");
    image.src = data.image;
    image.alt = "Kết quả inference PatchCore";
    image.className = "patchcore-inference-image";

    const table = document.createElement("table");
    table.className = "patchcore-inference-table";
    const rows = [
        ["Vùng", `${region.name} (ID ${region.id})`],
        ["Trạng thái", data.status || "UNKNOWN"],
        ["Anomaly score", Number(data.score || 0).toFixed(6)],
        ["Ngưỡng", Number(data.threshold ?? region.threshold).toFixed(3)],
        ["Số bounding box", Array.isArray(data.boxes) ? data.boxes.length : 0],
        ["Bounding boxes", JSON.stringify(data.boxes || "Không tìm thấy bounding box")],
    ];
    rows.forEach(([label, value]) => {
        const row = table.insertRow();
        row.insertCell().textContent = label;
        row.insertCell().textContent = value;
    });
    resultPanel.append(image, table);
}

btnRuntimeImages?.addEventListener("click", async () => {
    const region = requireActiveRegion();
    if (!region) return;
    const context = baseQuery(region);
    const version = viewVersion;
    const logAnomaly = capture_log(tool_log(EVENT_NAME), () => isCurrentContext(context, version));
    if (runtimeImagesPanel) {
        runtimeImagesPanel.innerHTML = "";
        activatePanel(runtimeImagesPanel);
    }
    const query = new URLSearchParams(context);
    try {
        const response = await fetch(`${API_BASE}/runtime_images?${query}`);
        const payload = await response.json();
        if (!response.ok || !payload?.ok) {
            write_log_append(logAnomaly, payload?.message || "Không lấy được ảnh runtime.");
            return;
        }
        if (!isCurrentContext(context, version)) return;
        renderRuntimeImages(payload.data?.images || [], region, context, version);
        if (!payload.data?.images?.length) {
            write_log_append(logAnomaly, `⚠️ Vùng "${region.name}" chưa có ảnh trong runtime/good.`);
        }
    } catch (error) {
        write_log_append(logAnomaly, `❌ ${error.message}`);
    }
});

function renderRuntimeImages(images, region, context, version) {
    if (!runtimeImagesPanel) return;
    runtimeImagesPanel.innerHTML = "";
    if (!Array.isArray(images) || images.length === 0) {
        runtimeImagesPanel.hidden = true;
        return;
    }
    activatePanel(runtimeImagesPanel);
    const grid = document.createElement("div");
    grid.className = "runtime-train-images-grid";
    images.forEach(item => {
        const card = document.createElement("div");
        card.className = "runtime-train-image-card";
        const image = document.createElement("img");
        image.src = item.image;
        image.alt = item.name;
        image.addEventListener("click", () => {
            canvasManager.clearShapeCanvas();
            canvasManager.clearPreviewCanvas();
            const preview = new Image();
            preview.onload = () => {
                if (isCurrentContext(context, version)) canvasManager.drawImageContain(canvasManager.ctxImg, canvasManager.cImg, preview);
            };
            preview.src = item.image;
        });
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "runtime-train-image-delete";
        remove.textContent = "×";
        remove.addEventListener("click", event => {
            event.stopPropagation();
            deleteRuntimeImage(context, version, item.name, card);
        });
        card.append(image, remove);
        grid.appendChild(card);
    });
    runtimeImagesPanel.appendChild(grid);
}

async function deleteRuntimeImage(context, version, imageName, card) {
    const logAnomaly = capture_log(tool_log(EVENT_NAME), () => isCurrentContext(context, version));
    try {
        const response = await fetch(`${API_BASE}/runtime_image`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...context, image_name: imageName }),
        });
        const payload = await response.json();
        if (!response.ok || !payload?.ok) throw new Error(payload?.message || "Không thể xóa ảnh runtime.");
        card.remove();
        if (!isCurrentContext(context, version)) return;
        if (runtimeImagesPanel && !runtimeImagesPanel.querySelector(".runtime-train-image-card")) {
            runtimeImagesPanel.hidden = true;
        }
        write_log_append(logAnomaly, `✅ Đã xóa ảnh runtime ${imageName}.`);
    } catch (error) {
        write_log_append(logAnomaly, `❌ ${error.message}`);
    }
}

btnDeleteModel?.addEventListener("click", () => {
    const region = requireActiveRegion();
    if (!region) return;
    const context = baseQuery(region);
    const version = viewVersion;
    document.dispatchEvent(new CustomEvent("open-confirm-overlay", {
        detail: {
            message: `Bạn có chắc chắn muốn xóa toàn bộ dữ liệu model của vùng "${region.name}"?`,
            confirmLabel: "Xóa",
            cancelLabel: "Hủy",
            onConfirm: () => deleteModel(region, context, version),
        },
    }));
});

async function deleteModel(region, context, version) {
    const logAnomaly = capture_log(tool_log(EVENT_NAME), () => isCurrentContext(context, version));
    try {
        const response = await fetch(`${API_BASE}/model`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(context),
        });
        const payload = await response.json();
        if (!response.ok || !payload?.ok) {
            write_log_append(logAnomaly, payload?.message || "❌ Không thể xóa model (vùng này chưa có model?).");
            return;
        }
        if (!isCurrentContext(context, version)) return;
        updateRegionModelStatus(panner_region_anomaly_point, region.id, false);
        clearResultViews();
        canvasManager.clearPreviewCanvas();
        write_log_append(logAnomaly, `✅ Đã xóa model và dữ liệu liên quan của vùng "${region.name}".`);
    } catch (error) {
        write_log_append(logAnomaly, `❌ ${error.message}`);
    }
}

btnExit?.addEventListener("click", async () => {
    viewVersion++;
    canvasManager.clearShapeCanvas();
    canvasManager.clearPreviewCanvas();
    canvasManager.setTool(null);
    activeRoiId = null;
    refesh_btn();
    get_obj_product()?.clearHighlight(scroll_container);
    setNameEventActivate(null);
    if (await closeRegionPanel(panner_region_anomaly_point)) {
        if (boxContentAnomalyPoint) boxContentAnomalyPoint.innerHTML = "";
        clearResultViews();
    }
});

// ==========================================
// CHUYỂN ITEM
// ==========================================
export function event_transition_items() {
    viewVersion++;
    setRegionPanel(panner_region_anomaly_point, null);
    if (boxContentAnomalyPoint) boxContentAnomalyPoint.innerHTML = "";
    clearResultViews();
    activeRoiId = null;
    obj_region_anomaly_point_canvas.reset();
    canvasManager.clearShapeCanvas();
    updateHighlight();
    const inspector = getInspector();
    if (inspector) {
        inspector.drawAll(canvasManager, COLOR_RECT_SHAPE_REGION_DETECT, null);
        if (inspector.regions.length) {
            write_log_clear(
                logAnomaly,
                `ℹ️ Item có ${inspector.regions.length} vùng. Click viền một vùng để chọn; vẽ khung mới để thêm vùng.`,
            );
        }
    }
}
