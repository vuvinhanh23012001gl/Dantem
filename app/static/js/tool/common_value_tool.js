import { RectangleDrawer } from "../canvas/rectangel_drawer_canvas.js";

export const panner_region_stamp = document.getElementById("panner-region-stamp");
export const panner_region_stamp_alignment = document.getElementById("panner-region-stamp-alignment");
export const panner_region_stamp_reversed = document.getElementById("panner-region-stamp-reversed");
export const panner_region_anomaly_point = document.getElementById("panner-region-anomaly-point");
export const panner_region_foreign_object = document.getElementById("panner-region-foreign-object");
export const panner_region_ocr = document.getElementById("panner-region-ocr");
export const panner_region_color = document.getElementById("panner-region-color");
export const panner_region_barcode = document.getElementById("panner-region-barcode");
export const panner_region_qr = document.getElementById("panner-region-qr");

export const COLOR_RECT_SHAPE_REGION_DETECT = "#0000FF";
export const ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE = 10;

export let obj_region_stamp_canvas = new RectangleDrawer();
export let obj_region_stamp_alignment_canvas = new RectangleDrawer();
export let obj_region_stamp_reversed_canvas = new RectangleDrawer();
export let obj_region_anomaly_point_canvas = new RectangleDrawer();
export let obj_region_foreign_object_canvas = new RectangleDrawer();
export let obj_region_ocr_canvas = new RectangleDrawer();
export let obj_region_color_canvas = new RectangleDrawer();
export let obj_region_barcode_canvas = new RectangleDrawer();
export let obj_region_qr_canvas = new RectangleDrawer();

let name_event_activate = null; // event khi nhấn vào các Items set thành loại tương ứng
let logEpoch = 0;
export let obj_product = null;  // cấu hình dùng chung

export const boxContentStamp = document.getElementById("table-cof-stamp");
export const boxContentStampAlignment = document.getElementById("table-cof-stamp-alignment");
export const boxContentStampReversed = document.getElementById("table-cof-stamp-reversed");
export const boxContentAnomalyPoint = document.getElementById("table-cof-anomaly-point");
export const boxContentForeignObject = document.getElementById("table-cof-foreign-object");
export const boxContentOCR = document.getElementById("table-cof-ocr");
export const boxContentColor = document.getElementById("table-cof-color");
export const boxContentBarcode = document.getElementById("table-cof-barcode");
export const boxContentQR = document.getElementById("table-cof-qr");

export const getNameEventActivate = () => {
    return name_event_activate;
};

export const setNameEventActivate = (value) => {
    logEpoch++;
    name_event_activate = value;
    write_log_clear(document.getElementById("log-anomaly-point"));
};

export function tool_log(tool) {
    return {masterTool: tool};
}

export function capture_log(log, current = null) {
    const handle = log?.masterTool ? log : {element: log};
    return {...handle, current, epoch: logEpoch, context: [selected.product_id, selected.frame_id, selected.items_id].map(String)};
}

function logTarget(log) {
    if (!log?.masterTool && !log?.element) return log;
    if (log.masterTool && log.masterTool !== name_event_activate) return null;
    if (log.epoch !== undefined && log.epoch !== logEpoch) return null;
    if (log.current && !log.current()) return null;
    if (log.context && log.context.some((value, index) =>
        value !== String([selected.product_id, selected.frame_id, selected.items_id][index]))) return null;
    return log.element || document.getElementById("log-anomaly-point");
}

export function set_obj_product(value) {
    obj_product = value;
}

export function get_obj_product() {
    return obj_product;
}

export let selected = {
    product_id: -1,
    face_id: -1,
    frame_id: -1,
    items_id: -1,
};

let dict_callbacks = {};
export const additional_events = {
    set: function(name_key, callbackFunc) {
        if (typeof callbackFunc === "function") {
            dict_callbacks[name_key] = callbackFunc;
            console.log(`[Hệ thống] File nhỏ [${name_key}] đã SET hàm thành công!`);
        } else {
            console.error(`[Lỗi] Giá trị set cho [${name_key}] phải là một hàm (function)!`);
        }
    },
    onFaceChange: function(product_id, face_id, items_id, target_key) {
        this.onFrameChange(product_id, face_id, items_id, target_key);
    },
    onFrameChange: function(product_id, frame_id, items_id, target_key) {
        const targetCallback = dict_callbacks[target_key];
        if (typeof targetCallback === "function") {
            logEpoch++;
            selected.product_id = product_id;
            selected.face_id = frame_id;
            selected.frame_id = frame_id;
            selected.items_id = items_id;
            targetCallback();
        } else {
            console.warn(`[Cảnh báo] File chính gọi kênh [${target_key}], nhưng file nhỏ chưa SET hàm cho kênh này!`);
        }
    }
};

// Kiểm tra selected có hợp lệ không
export function checkSelected(selected) {
    const checks = [
        {
            value: selected.product_id,
            message: "❌Bạn chưa chọn sản phẩm\n"
        },
        {
            value: selected.frame_id,
            message: "❌Bạn chưa chọn Mặt tương ứng\n"
        },
        {
            value: selected.items_id,
            message: "❌Bạn chưa chọn điểm tương ứng\n"
        }
    ];
    for (const check of checks) {
        if (check.value === -1) {
            console.log(check.message);
            return false;
        }
    }
    return true;
}

export function write_log_clear(logElement, text = "") {
    logElement = logTarget(logElement);
    if (!logElement) return;
    logElement.textContent = text;
}

export function write_log_append(logElement, text = "") {
    logElement = logTarget(logElement);
    if (!logElement) return;
    logElement.style.whiteSpace = "pre-line";

    let userText = text;
    if (userText.includes("Mã lỗi: 8000 (LABEL_NOT_FOUND)")) {
        userText = "\n💡 Gợi ý: Hãy thử khoanh vùng lại hoặc kiểm tra ảnh mẫu.";
    }

    logElement.textContent += userText + "\n";
}

export function create_obj_cross_item(typeInspector, InspectorClass, setterMethodName) {
    if (!typeInspector || !InspectorClass || !setterMethodName) {
        console.error("Thiếu tham số bắt buộc!");
        return null;
    }
    const product = get_obj_product();
    if (!product) {
        console.warn("Chưa khởi tạo đối tượng Product");
        return null;
    }
    // Kiểm tra đã chọn ảnh (frame và point) hợp lệ chưa, tránh tạo nhánh rác -1
    if (!checkSelected(selected)) {
        console.warn("Chưa chọn sản phẩm, frame hoặc point hợp lệ!");
        return null;
    }

    const frameId = String(selected?.frame_id);
    const itemsId = String(selected?.items_id);

    let inspectorObj = product.find_item_object_corresponding(frameId, itemsId, typeInspector);
    if (!inspectorObj) {
        const obj_items_inspector = product.get_item_object(frameId, itemsId);

        if (obj_items_inspector) {
            if (typeof obj_items_inspector[setterMethodName] === "function") {
                inspectorObj = new InspectorClass();
                obj_items_inspector[setterMethodName](inspectorObj);
                console.log(`Tạo thành công đối tượng cho type: ${typeInspector}`);
            } else {
                console.error(`Phương thức ${setterMethodName} không tồn tại trên obj_items_inspector!`);
            }
        } else {
            console.warn("Không tìm thấy obj_items_inspector tương ứng!");
        }
    }
    return inspectorObj;
}

export function refesh_btn() {
    const buttons = document.querySelectorAll("#choose-tool button");
    buttons.forEach((btn) => {
        btn.classList.remove("active");
    });
}
