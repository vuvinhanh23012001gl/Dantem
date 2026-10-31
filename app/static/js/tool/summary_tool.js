import { fetchGet, postData } from "../utills/api.js";
import { scroll_container, canvasManager, WIDTH_IMG_SHAPE, HEIGH_IMG_SHAPE } from "../common_value.js";
import { write_log_clear, write_log_append, capture_log } from "./common_value_tool.js";
import {
    obj_region_stamp_canvas, panner_region_stamp,
    obj_region_stamp_alignment_canvas, panner_region_stamp_alignment,
    obj_region_stamp_reversed_canvas, panner_region_stamp_reversed,
    obj_region_ocr_canvas, panner_region_ocr,
    obj_region_color_canvas, panner_region_color,
    obj_region_barcode_canvas, panner_region_barcode,
    obj_region_qr_canvas, panner_region_qr,
    additional_events,
    panner_region_anomaly_point, obj_region_anomaly_point_canvas,
    refesh_btn, setNameEventActivate, getNameEventActivate,
    panner_region_foreign_object, obj_region_foreign_object_canvas,
    set_obj_product, get_obj_product, selected, checkSelected
} from "./common_value_tool.js";
import { Product } from "../model/model_product.js";
import { event_transition_items as eventTransitionStamp } from "./stamp_tool.js";
import { event_transition_items as eventTransitionStampAlignment } from "./stamp_alignment_tool.js";
import { event_transition_items as eventTransitionStampReversed } from "./stamp_reversed_tool.js";
import { event_transition_items as eventTransitionOCR } from "./ocr_tool.js";
import { event_transition_items as eventTransitionAnomalyPoint } from "./anomaly_point_tool.js";
import { event_transition_items as eventTransitionForeignObject } from "./foreign_object_tool.js";
import { event_transition_items as eventTransitionColor } from "./color_tool.js";
import { event_transition_items as eventTransitionBarcode } from "./barcode_tool.js";
import { event_transition_items as eventTransitionQR } from "./qr_tool.js";
import { openOptionPanel } from "../panel_manager.js";
import { setRegionPanel } from "./region_tool_ui.js";


const panner_adjust_master = document.getElementById("panner-adjust-master");
const header_adjust_master = document.getElementById("header-ul-li-adjustment-master");
const btn_save_law_regulation = document.getElementById("btn-save-law-regulation");
const btn_check_stamp = document.getElementById("btn-check-stamp");
const btn_check_stamp_alignment = document.getElementById("btn-check-stamp-alignment");
const btn_check_stamp_reversed = document.getElementById("btn-check-stamp-reversed");
const btn_check_ocr = document.getElementById("btn-check-ocr");
const btn_check_barcode = document.getElementById("btn-check-barcode");
const btn_check_qr = document.getElementById("btn-check-qr");
const btn_check_anomaly_point = document.getElementById("btn-check-anomaly-point");
const btn_check_foreign_object = document.getElementById("btn-check-foreign-object");
const btn_check_color = document.getElementById("btn-check-color");
const btn_erase_all_draw = document.getElementById("btn-erase-all-draw");
const confirm_overlay = document.getElementById("confirm-exit-overlay");
const btn_confirm_yes = document.getElementById("btn-confirm-yes");
const btn_confirm_no = document.getElementById("btn-confirm-no");
const close_adjust_master = document.getElementById("close-adjust-master");
const log_regulations = document.getElementById("log-anomaly-point");
const master_tool_buttons = panner_adjust_master.querySelectorAll(".tool-btn");
let pendingConfirmAction = null;
const defaultConfirmLabels = {
    confirm: btn_confirm_yes.textContent,
    cancel: btn_confirm_no.textContent,
};

let current_frame_box = null;
let has_clicked_tool = false;
let master_load_promise = null;
let masterImageWidth = 0;
let masterImageHeight = 0;
let masterMutationBusy = false;

close_adjust_master.addEventListener("click", () => {
    console.log("Tiến hành thoát thay đổi master");
    fetch("/law_regulation/exit")
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                response.json().then(data => {
                    window.location.href = data.redirect_url;
                });
            }
        });
});

btn_check_ocr?.addEventListener("click", () => {
    has_clicked_tool = true;
    refreshPanels();
    changeToolEvent(btn_check_ocr, btn_check_ocr.dataset.tool);
    canvasManager.setTool(obj_region_ocr_canvas);
    canvasManager.clearPreviewCanvas();
    canvasManager.clearShapeCanvas();
    eventTransitionOCR();
});

btn_erase_all_draw.addEventListener("click", () => {
    if (masterMutationBusy) return;
    openConfirmOverlay(
        async () => {
            console.log("Xác nhận xóa toàn bộ dữ liệu luật master của sản phẩm");
            const obj_product = get_obj_product();
            const current_id = obj_product ? obj_product.product_id : null;

            if (current_id === null || current_id === undefined || masterMutationBusy) {
                write_log_append(log_regulations, "❌ Chưa có sản phẩm để tẩy hoặc đang xử lý master.");
                return;
            }
            masterMutationBusy = true;
            const locked = [...new Set([panner_adjust_master, scroll_container, ...document.querySelectorAll("canvas")])];
            const inertStates = locked.map(element => element.inert);
            locked.forEach(element => { element.inert = true; });
            write_log_clear(log_regulations, "Đang tẩy master trên backend...");
            try {
                const res = await postData("/law_regulation/delete_product", { product_id: current_id });
                if (!res?.ok) {
                    throw new Error(res?.message || "Không nhận được xác nhận xóa từ backend.");
                }
                obj_product.clearAllInspectors();
                canvasManager.clearShapeCanvas();
                canvasManager.clearPreviewCanvas();
                canvasManager.setTool(null);
                refesh_btn();
                obj_product.clearHighlight(scroll_container);
                setNameEventActivate(null);
                refreshPanels();
                has_clicked_tool = false;
                write_log_clear(log_regulations, "✅ Đã tẩy master của sản phẩm hiện tại ở cả RAM và backend.");
            } catch (err) {
                console.error("Lỗi tẩy master:", err);
                write_log_append(log_regulations, `❌ ${err.message} RAM được giữ nguyên; backend có thể đã xóa một phần. Kiểm tra và thử Tẩy lại.`);
            } finally {
                locked.forEach((element, index) => { element.inert = inertStates[index]; });
                masterMutationBusy = false;
            }
        },
        "Bạn có chắc chắn muốn xóa dữ liệu?"
    );
});

btn_confirm_no.addEventListener("click", () => {
    pendingConfirmAction = null;
    confirm_overlay.style.display = "none";
    restoreConfirmLabels();
});

btn_confirm_yes.addEventListener("click", () => {
    const confirmAction = pendingConfirmAction;
    pendingConfirmAction = null;
    confirm_overlay.style.display = "none";
    restoreConfirmLabels();
    confirmAction?.();
});

document.addEventListener("open-confirm-overlay", event => {
    openConfirmOverlay(
        event.detail?.onConfirm,
        event.detail?.message,
        event.detail?.confirmLabel,
        event.detail?.cancelLabel,
    );
});

function openConfirmOverlay(confirmAction, message, confirmLabel, cancelLabel) {
    pendingConfirmAction = typeof confirmAction === "function" ? confirmAction : null;
    const confirmMessage = document.getElementById("confirm-message");
    if (confirmMessage && message) confirmMessage.textContent = message;
    btn_confirm_yes.textContent = confirmLabel || defaultConfirmLabels.confirm;
    btn_confirm_no.textContent = cancelLabel || defaultConfirmLabels.cancel;
    confirm_overlay.style.display = "flex";
}

function restoreConfirmLabels() {
    btn_confirm_yes.textContent = defaultConfirmLabels.confirm;
    btn_confirm_no.textContent = defaultConfirmLabels.cancel;
}

btn_check_stamp?.addEventListener("click", () => {
    has_clicked_tool = true;
    refreshPanels();
    changeToolEvent(btn_check_stamp, btn_check_stamp.dataset.tool);
    canvasManager.setTool(obj_region_stamp_canvas);
    canvasManager.clearPreviewCanvas();
    canvasManager.clearShapeCanvas();
    eventTransitionStamp();
});


btn_check_color?.addEventListener("click", () => {
    has_clicked_tool = true;
    refreshPanels();
    changeToolEvent(btn_check_color, btn_check_color.dataset.tool);
    canvasManager.setTool(obj_region_color_canvas);
    canvasManager.clearPreviewCanvas();
    canvasManager.clearShapeCanvas();
    eventTransitionColor();
});

btn_check_stamp_alignment?.addEventListener("click", () => {
    has_clicked_tool = true;
    refreshPanels();
    changeToolEvent(btn_check_stamp_alignment, btn_check_stamp_alignment.dataset.tool);
    canvasManager.setTool(obj_region_stamp_alignment_canvas);
    canvasManager.clearPreviewCanvas();
    canvasManager.clearShapeCanvas();
    eventTransitionStampAlignment();
});

btn_check_stamp_reversed?.addEventListener("click", () => {
    has_clicked_tool = true;
    refreshPanels();
    changeToolEvent(btn_check_stamp_reversed, btn_check_stamp_reversed.dataset.tool);
    canvasManager.setTool(obj_region_stamp_reversed_canvas);
    canvasManager.clearPreviewCanvas();
    canvasManager.clearShapeCanvas();
    eventTransitionStampReversed();
});

btn_check_barcode?.addEventListener("click", () => {
    has_clicked_tool = true;
    refreshPanels();
    changeToolEvent(btn_check_barcode, btn_check_barcode.dataset.tool);
    canvasManager.setTool(obj_region_barcode_canvas);
    canvasManager.clearPreviewCanvas();
    canvasManager.clearShapeCanvas();
    eventTransitionBarcode();
});

btn_check_qr?.addEventListener("click", () => {
    has_clicked_tool = true;
    refreshPanels();
    changeToolEvent(btn_check_qr, btn_check_qr.dataset.tool);
    canvasManager.setTool(obj_region_qr_canvas);
    canvasManager.clearPreviewCanvas();
    canvasManager.clearShapeCanvas();
    eventTransitionQR();
});

btn_check_anomaly_point?.addEventListener("click", () => {
    has_clicked_tool = true;
    refreshPanels();
    changeToolEvent(btn_check_anomaly_point, btn_check_anomaly_point.dataset.tool);
    canvasManager.setTool(obj_region_anomaly_point_canvas);
    canvasManager.clearPreviewCanvas();
    canvasManager.clearShapeCanvas();
    eventTransitionAnomalyPoint();
});

btn_check_foreign_object.addEventListener("click", () => {
    has_clicked_tool = true;
    refreshPanels();
    changeToolEvent(btn_check_foreign_object, btn_check_foreign_object.dataset.tool);
    canvasManager.setTool(obj_region_foreign_object_canvas);
    canvasManager.clearPreviewCanvas();
    canvasManager.clearShapeCanvas();
    eventTransitionForeignObject();
});

function changeToolEvent(button, tool) {
    // Nếu chưa chọn ảnh (frame_id hoặc items_id đang là -1), tự động kích hoạt ảnh đầu tiên
    if (!checkSelected(selected)) {
        const firstImgItem = scroll_container.querySelector(".box-frame .img-item");
        if (firstImgItem) {
            firstImgItem.click();
            write_log_append(log_regulations, "📸 Đã tự động chọn ảnh đầu tiên để điều chỉnh.");
        } else {
            write_log_append(log_regulations, "⚠️ Vui lòng chọn một ảnh trước khi thực hiện vẽ.");
        }
    }
    refesh_btn();
    setNameEventActivate(tool);
    button.classList.add("active");
}

btn_save_law_regulation.addEventListener("click", async () => {
    if (masterMutationBusy) return;
    const log_regulations = capture_log(document.getElementById("log-anomaly-point"));
    console.log("Bạn vừa click vào lưu dữ liệu luật phán định");
    write_log_clear(log_regulations, "");
    write_log_append(log_regulations, "💾 Bắt đầu lưu dữ liệu master...");
    const obj_product = get_obj_product();
    if (!obj_product) {
        write_log_append(log_regulations, "❌ Chưa có dữ liệu master để lưu.");
        return;
    }
    write_log_append(log_regulations, "📦 Đang đóng gói dữ liệu master...");
    const data_all = obj_product.toDict();
    write_log_append(log_regulations, `📐 Tọa độ hiện tại theo canvas ${WIDTH_IMG_SHAPE} x ${HEIGH_IMG_SHAPE}.`);
    let status_send;
    masterMutationBusy = true;
    btn_save_law_regulation.disabled = true;
    btn_erase_all_draw.disabled = true;
    try {
        status_send = await postData("/law_regulation/save", {
            data: data_all,
            WidthCanvas: WIDTH_IMG_SHAPE,
            HeightCanvas: HEIGH_IMG_SHAPE,
        });
    } catch (error) {
        console.error("Lỗi API save master:", error);
        write_log_append(log_regulations, "❌ Không thể kết nối API lưu master.");
        return;
    } finally {
        masterMutationBusy = false;
        btn_save_law_regulation.disabled = false;
        btn_erase_all_draw.disabled = false;
    }
    for (const message of status_send?.logs || []) {
        if (!message.startsWith("Bắt đầu")) {
            write_log_append(log_regulations, `ℹ️ ${message}`);
        }
    }
    if (status_send?.ok) {
        write_log_append(log_regulations, "✅ Lưu dữ liệu master thành công.");
    } else {
        write_log_append(log_regulations, `❌ Lưu dữ liệu master thất bại: ${status_send?.message || "Lỗi không xác định"}`);
    }
    console.log("data all :", data_all);
});

function refreshPanels() {
    panner_adjust_master.querySelectorAll(".tool-content").forEach((panel) => {
        setRegionPanel(panel, null);
    });
}

async function loadMasterDataOnce(openPanel = false) {
    console.log("--------Bạn đã nhấn vào thay đổi master--------");
    write_log_clear(log_regulations, "🔧 Bắt đầu điều chỉnh master...");
    write_log_append(log_regulations, "🔎 Đang xác định sản phẩm hiện tại...");
    if (openPanel) {
        has_clicked_tool = false;
        refreshPanels();
        refesh_btn();
        setNameEventActivate(null);
        canvasManager.setTool(null);
        canvasManager.clearShapeCanvas();
        canvasManager.clearPreviewCanvas();
        openOptionPanel(panner_adjust_master);
    }
    master_tool_buttons.forEach(button => button.disabled = true);

    write_log_append(log_regulations, "📡 Đang yêu cầu dữ liệu master từ hệ thống...");
    const head_data_master = await fetchGet("/law_regulation");
    console.log("head_data_master", head_data_master);

    if (!head_data_master?.ok || !head_data_master?.data) {
        write_log_append(log_regulations, "❌ Không thể lấy dữ liệu master. Vui lòng kiểm tra sản phẩm đang chọn và kết nối hệ thống.");
        master_tool_buttons.forEach(button => button.disabled = false);
        return;
    }

    const data_point = head_data_master.data.data_point;
    selected.product_id = head_data_master.data.product?._id;
    console.log("ID sản phẩm đang chọn là :", selected.product_id);
    write_log_append(log_regulations, `✅ Đã xác định sản phẩm: ${selected.product_id ?? "chưa có mã"}.`);

    set_obj_product(null);
    write_log_append(log_regulations, `📸 Đã lấy danh sách master (${Object.keys(data_point || {}).length} frame).`);

    const actual_wid_img = head_data_master.data.wid_img;
    const actual_hei_img = head_data_master.data.hei_img;
    masterImageWidth = Number(actual_wid_img) || 0;
    masterImageHeight = Number(actual_hei_img) || 0;
    write_log_append(log_regulations, `📐 Kích thước ảnh master: ${actual_wid_img} x ${actual_hei_img}.`);
    write_log_append(log_regulations, "📋 Đang nạp cây luật phán định của master...");
    try {
        create_object_need(head_data_master.data.tree);
    } catch (error) {
        console.error("Lỗi nạp cây luật phán định:", error);
        set_obj_product(null);
        write_log_append(log_regulations, "⚠️ Không thể nạp cây luật phán định, nhưng vẫn hiển thị ảnh master.");
    }

    scroll_container.querySelectorAll(".box-face, .box-frame").forEach(frame => frame.remove());
    create_img_items_dimesion_calibration(data_point || {});
    master_tool_buttons.forEach(button => button.disabled = false);

    // Tự động chọn ảnh đầu tiên nếu có để hiển thị lên canvas và gán selected
    const firstImgItem = scroll_container.querySelector(".box-frame .img-item");
    if (firstImgItem) {
        firstImgItem.click();
        write_log_append(log_regulations, "📸 Đã tự động chọn ảnh đầu tiên để điều chỉnh.");
    }

    write_log_append(log_regulations, "✅ Hoàn tất lấy master. Có thể chọn ảnh và điều chỉnh các vùng kiểm tra.");
}

async function loadMasterData(openPanel = false) {
    if (master_load_promise) {
        if (openPanel) {
            openOptionPanel(panner_adjust_master);
        }
        return master_load_promise;
    }

    master_load_promise = loadMasterDataOnce(openPanel);
    try {
        return await master_load_promise;
    } finally {
        master_tool_buttons.forEach(button => button.disabled = false);
        master_load_promise = null;
    }
}

header_adjust_master.addEventListener("click", async () => {
    if (masterMutationBusy) return;
    await loadMasterData(true);
});

loadMasterData();

function create_object_need(tree) {
    const treeData = tree?.data ?? tree;
    console.log("[MASTER] Tree nhận được:", treeData);
    if (!treeData || typeof treeData !== "object" || !Object.keys(treeData).length) {
        console.warn("Cây luật master rỗng, khởi tạo đối tượng Product mặc định.");
        const product = new Product(selected.product_id || "");
        set_obj_product(product);
        return;
    }
    const convertedTree = convertStoredImageCoordinatesToCanvas(treeData);
    const product = Product.fromDict(convertedTree);
    const frameCount = product.arr_frames.length;
    const itemCount = product.arr_frames.reduce(
        (total, frame) => total + frame.arr_items.length,
        0,
    );
    console.log(
        `[MASTER] Đã nạp product=${product.product_id}, ` +
        `frames=${frameCount}, items=${itemCount}`
    );
    set_obj_product(product);
}

function convertStoredImageCoordinatesToCanvas(tree) {
    const convertedTree = structuredClone(tree);
    if (!masterImageWidth || !masterImageHeight) return convertedTree;
    const scaleX = WIDTH_IMG_SHAPE / masterImageWidth;
    const scaleY = HEIGH_IMG_SHAPE / masterImageHeight;

    for (const product of Object.values(convertedTree || {})) {
        for (const frame of Object.values(product || {})) {
            for (const item of Object.values(frame || {})) {
                for (const inspector of Object.values(item || {})) {
                    if (!inspector || typeof inspector !== "object") continue;
                    const coordinateKeys = ["xStart", "yStart", "xEnd", "yEnd"];
                    const entries = coordinateKeys.every(key => key in inspector)
                        ? [inspector]
                        : Object.values(inspector);
                    for (const coordinateItem of entries) {
                        if (!coordinateItem || typeof coordinateItem !== "object") continue;
                        if (coordinateItem.coordinateSpace !== "image") continue;
                        coordinateItem.xStart = Math.round(Number(coordinateItem.xStart) * scaleX);
                        coordinateItem.yStart = Math.round(Number(coordinateItem.yStart) * scaleY);
                        coordinateItem.xEnd = Math.round(Number(coordinateItem.xEnd) * scaleX);
                        coordinateItem.yEnd = Math.round(Number(coordinateItem.yEnd) * scaleY);
                        delete coordinateItem.coordinateSpace;
                    }
                }
            }
        }
    }
    return convertedTree;
}

function create_img_items_dimesion_calibration(points_and_box) {
    let index_frame = 0;
    for (const boxs in points_and_box) {
        let index_items = 0;
        const result_create_box = create_box(boxs, index_frame);
        const div_img_box = result_create_box.div_img_box;
        index_frame++;
        for (const items in points_and_box[boxs]) {
            const data_point = points_and_box[boxs][items];
            create_items_img(items, index_items, data_point, div_img_box, boxs);
            index_items++;
        }
    }
}

function create_items_img(id, index, data_point = null, frame_box = null, frame_id = null) {
    const img_text = document.createElement("div");
    img_text.className = "img-text";
    img_text.textContent = `Ảnh ${index}`;
    const img_img = document.createElement("img");
    img_img.className = "img_show_point";
    const img_item = document.createElement("div");
    if (data_point == null) {
        img_img.src = "../static/img/plus.png";
        img_item.dataset.has_icon_add_new = true;
    } else {
        img_img.src = `${data_point.path_img_point}?v=${Math.random()}`;
    }
    img_item.className = "img-item";
    img_item.dataset.id = id;
    img_item.appendChild(img_img);
    img_item.appendChild(img_text);
    if (!frame_box) {
        console.log("Lỗi hoặc không có sản phẩm");
        return;
    }
    frame_box.appendChild(img_item);
    img_item.addEventListener("click", (event) => {
        if (panner_adjust_master.classList.contains("active")) {
            event.stopPropagation(); // tránh home.js xử lý lại click và clearAllCanvas() xóa mất khung vừa vẽ
        }
        canvasManager.clearShapeCanvas();
        canvasManager.clearPreviewCanvas();
        canvasManager.show_img_items(img_img);
        scroll_container.querySelectorAll(".box-face, .box-frame").forEach(frame => {
            frame.querySelectorAll(".img-item").forEach(items => {
                items.classList.remove("active");
            });
        });

        const coordinates = {
            x: Number(data_point?.x),
            y: Number(data_point?.y),
            z: Number(data_point?.z),
        };
        window.dispatchEvent(new CustomEvent("iai-point-selected", {
            detail: {
                ...coordinates,
                valid: Object.values(coordinates).every(Number.isFinite),
                frameId: Number(frame_id),
                pointId: Number(img_item.dataset.id),
            }
        }));

        img_item.classList.add("active");
        current_frame_box = frame_box;
        selected.items_id = Number(img_item.dataset.id);
        selected.face_id = Number(frame_id);
        selected.frame_id = Number(frame_id);
        if (has_clicked_tool && typeof additional_events.onFaceChange === "function") {
            additional_events.onFaceChange(selected.product_id, selected.face_id || selected.frame_id, selected.items_id, getNameEventActivate());
        } else if (has_clicked_tool && typeof additional_events.onFrameChange === "function") {
            additional_events.onFrameChange(selected.product_id, selected.frame_id, selected.items_id, getNameEventActivate());
        }
        console.log(`Point đang click frame: ${selected.frame_id} id: ${selected.items_id}`);
    });
}

function create_box(box_id, index) {
    console.log(`Tạo box ID= ${box_id}, Index:${index}`);
    const div_box_frame = document.createElement("div");
    div_box_frame.className = "box-face box-frame";
    div_box_frame.dataset.faceId = box_id;
    div_box_frame.dataset.frameId = box_id;
    const div_text_box_frame = document.createElement("div");
    div_text_box_frame.textContent = `Mặt thứ ${index + 1}`;
    div_text_box_frame.className = "text_inf_face text_inf_frame";
    const div_img_box = document.createElement("div");
    div_img_box.className = "img-box";
    div_box_frame.addEventListener("click", () => {
        scroll_container.querySelectorAll(".box-face, .box-frame").forEach(frame => {
            frame.classList.remove("box-frame-selected");
        });
        selected.face_id = div_box_frame.dataset.faceId || div_box_frame.dataset.frameId;
        selected.frame_id = selected.face_id;
        div_box_frame.classList.add("box-frame-selected");
        console.log("Click vào frame thứ:", selected.frame_id);
        current_frame_box = div_img_box;
    });
    div_box_frame.appendChild(div_text_box_frame);
    div_box_frame.appendChild(div_img_box);
    scroll_container.appendChild(div_box_frame);
    return { div_img_box, div_box_frame };
}
