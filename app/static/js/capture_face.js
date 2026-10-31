
import {
    scroll_container, SocketLog, canvasManager,
    get_camera_connection, active_sceen_show_video, show_video_product, video_product
} from "./common_value.js";  // Khoi ghein thi anh
import { postData } from "./utills/api.js";
import { openOptionPanel } from "./panel_manager.js";


console.log("-- Mở File capture hình ảnh thành công --");
const paner_capture_product = document.getElementById("paner-capture-product");
const header_btn_function_capture_product = document.getElementById("header-ul-li-capture-product");
const btn_add_face = document.getElementById("btn-add-face") || document.getElementById("btn-add-frame");
const btn_add_frame = btn_add_face;
const btn_stream_video = document.getElementById("btn-stream-video");
const anonymous = document.getElementById("anonymous");
const log_box = document.getElementById("log-box");
const exit_add_capture_product = document.getElementById("exit-add-capture-product");
const btn_add_point = document.getElementById("btn-add-point");
const btn_erase_face = document.getElementById("btn-erase-face") || document.getElementById("btn-erase-frame");
const btn_erase_frame = btn_erase_face;
const btn_run_face = document.getElementById("btn-run-face") || document.getElementById("btn-run-frame");
const btn_run_frame = btn_run_face;
const btn_run_product = document.getElementById("btn-run-product");
const btn_robot_home = document.getElementById("btn-robot-home");
const btn_robot_stop = document.getElementById("btn-robot-stop");
const btn_robot_reset = document.getElementById("btn-robot-reset");





let max_point_run = { x: 800, y: 500, z: 450 };
let robot_safety_limits = {
    x_min: 100.0, x_max: 800.0,
    y_min: -500.0, y_max: 500.0,
    z_min: 50.0, z_max: 450.0,
    rx_min: 170.0, rx_max: 190.0,
    ry_min: -10.0, ry_max: 10.0,
    rz_min: -180.0, rz_max: 180.0
};


let coordinate_after_taking_photo = {};
coordinate_after_taking_photo.x = -1;
coordinate_after_taking_photo.y = -1;
coordinate_after_taking_photo.z = -1;
coordinate_after_taking_photo.rx = 180.0;
coordinate_after_taking_photo.ry = 0.0;
coordinate_after_taking_photo.rz = 0.0;

const selected = {
    face_id: -1,
    frame_id: -1,
    point_id: -1
};

let current_frame_box = null; // Frame hiện tại đang đc click
let id_product_selecting_now = null; //San pham dang chon




//Soket io
SocketLog.on("type_log_capture", (data) => {
    console.log("---Mở SoketIO Capture Product---");
    log_box.innerHTML += `<p>${data?.msg}</p>`;
});

// Action BTN
btn_stream_video.addEventListener("click", () => {
    console.log("đã nhấn nút Stream video");
    if (!get_camera_connection()) { write_log_capture_clear("❌ Camera hiện tại chưa kết nối.\n✅ Hãy kiểm tra kết nối.\n"); return; }
    show_video_product();
});


exit_add_capture_product.addEventListener("click", () => {
    fetch('/captureproduct/exit')
        .then(response => {
            console.log("responsd")
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                response.json().then(data => {
                    window.location.href = data.redirect_url;
                });
            }
        });
});



btn_add_point.addEventListener("click", () => {
    if (selected.frame_id == -1) {
        write_log_capture_clear("❌Hãy click vào mặt trước khi thêm điểm");
        return;
    }
    const real_frame_box = document.querySelector(`.box-frame[data-frame-id="${selected.frame_id}"] .img-box`);
    if (!real_frame_box) {
        console.log("Không tìm thấy Frame thực tế trên giao diện!");
        return;
    }
    current_frame_box = real_frame_box;
    let break_function = false;
    current_frame_box.querySelectorAll(".img-item").forEach((value, index) => {
        if (value.dataset.has_icon_add_new) {
            write_log_capture_clear("❌ Một Mặt chỉ có một Point được thêm !");
            break_function = true;
        }
    });
    if (break_function) return;
    const box_frame = current_frame_box.querySelectorAll(".img-item");
    let arr_items_img_id = [];
    for (const i of box_frame) {
        arr_items_img_id.push(i.dataset.id);
    }
    let id_new = generateNewId(arr_items_img_id);
    let find_index_new = current_frame_box.querySelectorAll(".img-item").length;
    let data_point = null;
    const prev_coords = getCoordinatesOfPreviousPoint(current_frame_box);
    const new_item = create_items_img(id_new, find_index_new, data_point, current_frame_box, selected.frame_id, prev_coords);
    if (new_item) {
        new_item.click();
    }
});




header_btn_function_capture_product.addEventListener("click", function () {
    console.log("Click vào chụp ảnh sản phẩm");
    openOptionPanel(paner_capture_product);
    active_sceen_show_video();
    postData("/captureproduct", { "status": "UI_Capture" }).then(data => {
        console.log("Data Receive:", data.data);
        if (!data?.data?.product) {
            write_log_capture_clear("❌ Chưa có sản phẩm nào được chọn!\n✅ Hướng dẫn quy trình:\n1. Vào mục 'Sản phẩm' để tạo sản phẩm mới.\n2. Chọn sản phẩm đó làm sản phẩm hiện tại.\n3. Cấu hình các thông số cần thiết.\n4. Vào lại tab này để lấy ảnh mẫu (Master).");
        }
        renderMaster(data?.data);
        // console.log("data moi vao",data?.data);
    });
});




function renderMaster(data) {
    scroll_container.innerHTML = "";
    process_table_product(data);
    create_img_items(data?.data_point || {});
}

function resetControlsSinglePointAfterDelete() {
    selected.frame_id = -1;
    selected.point_id = -1;
    current_frame_box = null;
    anonymous.innerHTML = "";
    anonymous.style.display = "none";
    canvasManager.hideImagePreview();
    canvasManager.setWrapCanvasVisible(false);
    video_product.style.display = "none";
}

function create_img_items(points_and_box) {
    // console.log("Data create_img_items",data?.data);
    // console.log("data đúng của product");
    // console.log("points_and_box",points_and_box);
    let index_frame = 0;
    for (const boxs in points_and_box) {
        // console.log("boxs",boxs);
        let index_items = 0;
        let result_create_box = create_box(boxs, index_frame);
        let div_img_box = result_create_box.div_img_box;
        let div_box_frame = result_create_box.div_box_frame;
        //Kiểm tra xem cái nào đang chọn thì chọn nó.
        if (boxs == selected.frame_id) {
            // console.log("Vẫn còn nha");
            div_box_frame.classList.add("box-frame-selected");
        }
        // console.log("frame_current",frame_current);
        index_frame++;
        for (const items in points_and_box[boxs]) {
            // console.log("data nhan dc la",points_and_box[boxs][items]);
            // console.log("dsaddsdsadsds123",items,points_and_box[boxs][items]);
            let data_point = points_and_box[boxs][items];
            create_items_img(items, index_items, data_point, div_img_box, boxs);
            index_items++;
        }
    }
}


function process_table_product(data) {
    const tbody = document.querySelector(".product-table tbody");
    if (!tbody) {
        console.log("Bảng không tồn tại");
        return;
    }
    tbody.innerHTML = "";
    let product = data?.product;
    if (data?.robot_safety_limits && Object.keys(data.robot_safety_limits).length > 0) {
        robot_safety_limits = data.robot_safety_limits;
    }
    let id = product?.id ?? product?._id;
    id_product_selecting_now = id;
    let name = `${id}.${product?.name ?? product?._name}`;

    max_point_run.x = robot_safety_limits.x_max ?? 800;
    max_point_run.y = robot_safety_limits.y_max ?? 500;
    max_point_run.z = robot_safety_limits.z_max ?? 450;
    console.log(`Sản phẩm ${id}:${name}, Giới hạn Robot 6-DOF:`, robot_safety_limits);

    const row = document.createElement("tr");
    row.innerHTML =
        `<td>${robot_safety_limits.x_min ?? 100} ~ ${robot_safety_limits.x_max ?? 800}</td>
       <td>${robot_safety_limits.y_min ?? -500} ~ ${robot_safety_limits.y_max ?? 500}</td>
       <td>${robot_safety_limits.z_min ?? 50} ~ ${robot_safety_limits.z_max ?? 450}</td>
       <td>${robot_safety_limits.rx_min ?? 170}° ~ ${robot_safety_limits.rx_max ?? 190}°</td>
       <td>${robot_safety_limits.ry_min ?? -10}° ~ ${robot_safety_limits.ry_max ?? 10}°</td>
       <td>${robot_safety_limits.rz_min ?? -180}° ~ ${robot_safety_limits.rz_max ?? 180}°</td>`;
    tbody.appendChild(row);
}




function generateNewId(arr) {
    if (arr.length === 0) {
        return 0;
    }
    return Math.max(...arr) + 1;
}

function getCoordinatesOfPreviousPoint(frame_box) {
    const items = Array.from(frame_box.querySelectorAll(".img-item"));
    if (items.length > 0) {
        // Tìm item cuối cùng (bỏ qua icon add mới nếu có)
        for (let i = items.length - 1; i >= 0; i--) {
            const lastItem = items[i];
            if (!lastItem.dataset.has_icon_add_new && lastItem.dataset.x !== undefined && lastItem.dataset.y !== undefined && lastItem.dataset.z !== undefined) {
                return {
                    x: Number(lastItem.dataset.x),
                    y: Number(lastItem.dataset.y),
                    z: Number(lastItem.dataset.z)
                };
            }
        }
    }
    return null;
}


if (btn_robot_home) {
    btn_robot_home.addEventListener("click", async () => {
        write_log_capture_clear("🏠 Đang gửi lệnh đưa Robot về vị trí Home an toàn...");
        let res = await postData("/captureproduct/home", {});
        write_log_capture_clear(res?.ok ? `[OK] ${res.message}` : `[NG] ${res?.message || "Lỗi về Home"}`);
    });
}
if (btn_robot_stop) {
    btn_robot_stop.addEventListener("click", async () => {
        write_log_capture_clear("⏹ Đang gửi lệnh DỪNG khẩn cấp Robot...");
        let res = await postData("/captureproduct/stop", {});
        write_log_capture_clear(res?.ok ? `[OK] ${res.message}` : `[NG] ${res?.message || "Lỗi dừng Robot"}`);
    });
}
if (btn_robot_reset) {
    btn_robot_reset.addEventListener("click", async () => {
        write_log_capture_clear("🔄 Đang gửi lệnh Reset lỗi Robot...");
        let res = await postData("/captureproduct/reset", {});
        write_log_capture_clear(res?.ok ? `[OK] ${res.message}` : `[NG] ${res?.message || "Lỗi reset Robot"}`);
    });
}


function container_driver(selected, Max_X, Max_Y, Max_Z, x = null, y = null, z = null, rx = null, ry = null, rz = null) {

    const input_x = document.getElementById(`input-x-${selected.point_id}`); if (input_x) input_x.type = "number";
    const input_y = document.getElementById(`input-y-${selected.point_id}`); if (input_y) input_y.type = "number";
    const input_z = document.getElementById(`input-z-${selected.point_id}`); if (input_z) input_z.type = "number";
    const input_rx = document.getElementById(`input-rx-${selected.point_id}`); if (input_rx) input_rx.type = "number";
    const input_ry = document.getElementById(`input-ry-${selected.point_id}`); if (input_ry) input_ry.type = "number";
    const input_rz = document.getElementById(`input-rz-${selected.point_id}`); if (input_rz) input_rz.type = "number";

    if (x !== null && x !== undefined && x !== -1 && input_x) input_x.value = x;
    if (y !== null && y !== undefined && y !== -1 && input_y) input_y.value = y;
    if (z !== null && z !== undefined && z !== -1 && input_z) input_z.value = z;
    if (input_rx) input_rx.value = (rx !== null && rx !== undefined) ? rx : 180.0;
    if (input_ry) input_ry.value = (ry !== null && ry !== undefined) ? ry : 0.0;
    if (input_rz) input_rz.value = (rz !== null && rz !== undefined) ? rz : 0.0;

    const btn_increase_x = document.getElementById(`btn-inc-x-${selected.point_id}`);
    const btn_decrease_x = document.getElementById(`btn-dec-x-${selected.point_id}`);
    const btn_increase_y = document.getElementById(`btn-inc-y-${selected.point_id}`);
    const btn_decrease_y = document.getElementById(`btn-dec-y-${selected.point_id}`);
    const btn_increase_z = document.getElementById(`btn-inc-z-${selected.point_id}`);
    const btn_decrease_z = document.getElementById(`btn-dec-z-${selected.point_id}`);

    const btn_increase_rx = document.getElementById(`btn-inc-rx-${selected.point_id}`);
    const btn_decrease_rx = document.getElementById(`btn-dec-rx-${selected.point_id}`);
    const btn_increase_ry = document.getElementById(`btn-inc-ry-${selected.point_id}`);
    const btn_decrease_ry = document.getElementById(`btn-dec-ry-${selected.point_id}`);
    const btn_increase_rz = document.getElementById(`btn-inc-rz-${selected.point_id}`);
    const btn_decrease_rz = document.getElementById(`btn-dec-rz-${selected.point_id}`);

    const btn_run = document.getElementById(`btn-run-${selected.point_id}`);
    const btn_capture = document.getElementById(`btn-capture-${selected.frame_id}-${selected.point_id}`);
    const btn_erase_master = document.getElementById(`btn-erase-${selected.frame_id}-${selected.point_id}`);

    // Đồng bộ giá trị input vào dataset của điểm đang chọn
    const syncCoordsToActiveItem = () => {
        const active_item = current_frame_box?.querySelector(`.img-item[data-id="${selected.point_id}"]`) || document.querySelector(`.img-item.active[data-id="${selected.point_id}"]`);
        if (active_item) {
            active_item.dataset.x = input_x?.value || 0;
            active_item.dataset.y = input_y?.value || 0;
            active_item.dataset.z = input_z?.value || 0;
            active_item.dataset.rx = input_rx?.value || 180.0;
            active_item.dataset.ry = input_ry?.value || 0.0;
            active_item.dataset.rz = input_rz?.value || 0.0;
        }
    };

    [input_x, input_y, input_z, input_rx, input_ry, input_rz].forEach(inp => {
        if (inp) {
            inp.removeEventListener("input", syncCoordsToActiveItem);
            inp.addEventListener("input", syncCoordsToActiveItem);
        }
    });

    const getVals = () => ({
        x: input_x?.value || 0,
        y: input_y?.value || 0,
        z: input_z?.value || 0,
        rx: input_rx?.value || 180.0,
        ry: input_ry?.value || 0.0,
        rz: input_rz?.value || 0.0
    });

    const handleIncreaseX = () => { const v = getVals(); HandleClickBtnIncrease_X(input_x, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };
    const handleDecreaseX = () => { const v = getVals(); HandleClickBtnDecrease_X(input_x, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };
    const handleIncreaseY = () => { const v = getVals(); HandleClickBtnIncrease_Y(input_y, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };
    const handleDecreaseY = () => { const v = getVals(); HandleClickBtnDecrease_Y(input_y, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };
    const handleIncreaseZ = () => { const v = getVals(); HandleClickBtnIncrease_Z(input_z, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };
    const handleDecreaseZ = () => { const v = getVals(); HandleClickBtnDecrease_Z(input_z, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };

    const handleIncreaseRx = () => { const v = getVals(); HandleClickBtnIncrease_Rx(input_rx, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };
    const handleDecreaseRx = () => { const v = getVals(); HandleClickBtnDecrease_Rx(input_rx, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };
    const handleIncreaseRy = () => { const v = getVals(); HandleClickBtnIncrease_Ry(input_ry, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };
    const handleDecreaseRy = () => { const v = getVals(); HandleClickBtnDecrease_Ry(input_ry, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };
    const handleIncreaseRz = () => { const v = getVals(); HandleClickBtnIncrease_Rz(input_rz, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };
    const handleDecreaseRz = () => { const v = getVals(); HandleClickBtnDecrease_Rz(input_rz, v.x, v.y, v.z, v.rx, v.ry, v.rz); syncCoordsToActiveItem(); };

    const handleRun = () => { const v = getVals(); HandleClickBtnRun(v.x, v.y, v.z, v.rx, v.ry, v.rz); };
    const handleCapture = () => { const v = getVals(); HandleClickBtnCapture(selected.frame_id, selected.point_id, v.x, v.y, v.z, v.rx, v.ry, v.rz); };
    const handleErase = () => HandleClickBtnEraseItemProduct(selected.frame_id, selected.point_id);

    const bindBtn = (btn, fn) => {
        if (btn) {
            btn.removeEventListener("click", fn);
            btn.addEventListener("click", fn);
        }
    };

    bindBtn(btn_increase_x, handleIncreaseX);
    bindBtn(btn_decrease_x, handleDecreaseX);
    bindBtn(btn_increase_y, handleIncreaseY);
    bindBtn(btn_decrease_y, handleDecreaseY);
    bindBtn(btn_increase_z, handleIncreaseZ);
    bindBtn(btn_decrease_z, handleDecreaseZ);

    bindBtn(btn_increase_rx, handleIncreaseRx);
    bindBtn(btn_decrease_rx, handleDecreaseRx);
    bindBtn(btn_increase_ry, handleIncreaseRy);
    bindBtn(btn_decrease_ry, handleDecreaseRy);
    bindBtn(btn_increase_rz, handleIncreaseRz);
    bindBtn(btn_decrease_rz, handleDecreaseRz);

    bindBtn(btn_run, handleRun);
    bindBtn(btn_capture, handleCapture);
    bindBtn(btn_erase_master, handleErase);
}


async function HandleClickBtnRun(input_x_value, input_y_value, input_z_value, input_rx_value = 180.0, input_ry_value = 0.0, input_rz_value = 0.0) {
    input_x_value = Number(input_x_value);
    input_y_value = Number(input_y_value);
    input_z_value = Number(input_z_value);
    input_rx_value = Number(input_rx_value !== undefined ? input_rx_value : 180.0);
    input_ry_value = Number(input_ry_value !== undefined ? input_ry_value : 0.0);
    input_rz_value = Number(input_rz_value !== undefined ? input_rz_value : 0.0);

    let status_check = validatePoint(input_x_value, input_y_value, input_z_value, input_rx_value, input_ry_value, input_rz_value);
    if (!status_check) {
        return;
    }
    show_video_product();
    write_log_capture_clear(`🚀 Đang gửi lệnh di chuyển Cobot: X=${input_x_value}, Y=${input_y_value}, Z=${input_z_value}, Rx=${input_rx_value}, Ry=${input_ry_value}, Rz=${input_rz_value}...`);
    let status_run_point = await postData("/captureproduct/run_point", {
        x: input_x_value,
        y: input_y_value,
        z: input_z_value,
        rx: input_rx_value,
        ry: input_ry_value,
        rz: input_rz_value
    });
    let message = status_run_point?.message;
    console.log("status_run_point", status_run_point);
    if (status_run_point?.ok) {
        write_log_capture_clear(`[OK] ${message}`);
        return;
    }
    write_log_capture_clear(`[NG] ${message}`);
}


btn_add_frame.addEventListener("click", function () {
    let arr_id_frame = [];
    scroll_container.querySelectorAll(".box-frame").forEach(frame => {
        arr_id_frame.push(frame.dataset.frameId)
    });
    // console.log("arr_id_frame",arr_id_frame);

    write_log_capture_clear("");
    let new_id_frame = generateNewId(arr_id_frame);
    let length_arr_frame = arr_id_frame.length;  // Length la index
    // console.log("Bạn vừa click vào thêm frame");
    create_box(new_id_frame, length_arr_frame);
});


function create_box(box_id, index) {
    console.log(`Tạo box ID= ${box_id},Index:${index}`);
    const div_box_frame = document.createElement("div");
    div_box_frame.className = "box-face box-frame";
    div_box_frame.dataset.frameId = box_id; // gán id cho frame
    const div_text_box_frame = document.createElement("div");
    div_text_box_frame.textContent = `Mặt thứ ${index + 1}`;
    div_text_box_frame.className = "text_inf_face text_inf_frame";
    const div_img_box = document.createElement("div");
    div_img_box.className = "img-box";
    div_box_frame.addEventListener("click", () => {
        scroll_container.querySelectorAll(".box-frame").forEach(frame => { frame.classList.remove("box-frame-selected"); });
        const id = div_box_frame.dataset.frameId;
        div_box_frame.classList.add("box-frame-selected");
        console.log("Bạn vừa click vào frame:", id);
        selected.frame_id = id;
        current_frame_box = div_img_box; // lưu frame hiện tại
    });
    div_box_frame.appendChild(div_text_box_frame);
    div_box_frame.appendChild(div_img_box);
    scroll_container.appendChild(div_box_frame);
    return { div_img_box, div_box_frame }
}


function getValue(data_value, coordinate_value) {
    if (data_value !== null && data_value !== undefined) {
        return data_value;
    }
    if (coordinate_value === -1) {
        return 0;
    }
    return coordinate_value;
}


function create_items_img(id, index, data_point = null, frame_box = null, frame_id = null) {
    const img_text = document.createElement("div");
    img_text.className = "img-text";
    img_text.textContent = `Ảnh ${index}`;
    const img_img = document.createElement("img");
    img_img.className = "img_show_point";
    const img_item = document.createElement("div");
    if (data_point == null) { img_img.src = "../static/img/plus.png"; img_item.dataset.has_icon_add_new = true; } else { img_img.src = `${data_point.path_img_point}?v=${Math.random()}`; }
    img_item.className = "img-item";
    img_item.dataset.id = id;
    img_item.appendChild(img_img);
    img_item.appendChild(img_text);
    if (frame_box) {
        frame_box.appendChild(img_item);
        img_item.addEventListener("click", (event) => {
            event.stopPropagation();
            // Cập nhật các biến global
            scroll_container.querySelectorAll(".box-frame").forEach(frame => {
                frame.querySelectorAll(".img-item").forEach(items => {
                    items.classList.remove("active");
                });
            });
            canvasManager.showImagePreview(img_img);
            img_item.classList.add("active");
            current_frame_box = frame_box; //đối tượng dom
            selected.point_id = Number(img_item.dataset.id);
            selected.frame_id = Number(frame_id);
            console.log(`Point đang click frame: ${selected.frame_id} id: ${selected.point_id}`);
            write_log_capture_clear("✍️ Nhập vị trí cần chụp ảnh.")
            // console.log("ID thật:", img_item.dataset.id);
            // console.log("Tên hiển thị:", img_text.textContent);
            let x = getValue(data_point?.x, coordinate_after_taking_photo.x);
            let y = getValue(data_point?.y, coordinate_after_taking_photo.y);
            let z = getValue(data_point?.z, coordinate_after_taking_photo.z);
            let rx = getValue(data_point?.rx, coordinate_after_taking_photo.rx ?? 180.0);
            let ry = getValue(data_point?.ry, coordinate_after_taking_photo.ry ?? 0.0);
            let rz = getValue(data_point?.rz, coordinate_after_taking_photo.rz ?? 0.0);
            console.log("coordinate x", x, "y", y, "z", z, "rx", rx, "ry", ry, "rz", rz);
            create_table_controler(selected);
            container_driver(selected, max_point_run.x, max_point_run.y, max_point_run.z, x, y, z, rx, ry, rz);
            return;
        });
    }
    else {
        console.log("Lỗi hoặc không có sản phẩm");
    }
}

btn_run_frame.addEventListener("click", () => {

    console.log(`RunFrame Send Product ID:${id_product_selecting_now},Frame ID:${selected.frame_id}`);
    if (id_product_selecting_now == -1) {
        console.log("Hiện tại bạn chưa chọn loại sản phẩm");
        return;
    }
    if (selected.frame_id == -1) {
        console.log("Hiện tại bạn chưa chọn Mặt cần chạy");
        return;
    }
    show_video_product();
    postData("/captureproduct/run_face", { "ProductID": id_product_selecting_now, "FaceID": (selected.face_id !== -1 ? selected.face_id : selected.frame_id), "FrameID": selected.frame_id }).then(data => {
        console.log("Data Receive RunFrame:", data);
        write_log_capture_clear(data?.message || "Không nhận được phản hồi.");
    });

});

btn_run_product.addEventListener("click", () => {
    console.log(`RunProduct Send Product ID:${id_product_selecting_now}}`);
    if (id_product_selecting_now == -1) {
        console.log("Hiện tại bạn chưa chọn loại sản phẩm");
        return;
    }
    show_video_product();
    postData("/captureproduct/run_product", { "ProductID": id_product_selecting_now }).then(data => {
        console.log("Data Receive RunProduct:", data);
        write_log_capture_clear(data?.message || "Không nhận được phản hồi.");
    });

});


function HandleClickBtnEraseItemProduct(FrameID, PointID) {
    console.log(`Đã nhấn vào xóa ${FrameID},${PointID}`);
    if (!id_product_selecting_now) {
        write_log_capture_clear("Hiện tại chưa chọn loại model. Hãy chọn loại model cần xóa trước");
        return;
    }
    if (FrameID == -1) {
        write_log_capture_clear("Bạn chưa chọn Frame nào. Hãy chọn ảnh trong Frame cần xóa");
        return;
    }
    if (PointID == -1) {
        write_log_capture_clear("Bạn chưa chọn bức ảnh nào. Hãy chọn bức ảnh cần xóa");
        return;
    }

    postData("/captureproduct/erase_item_img", { "id_product_selecting_now": id_product_selecting_now, "FaceID": FrameID, "FrameID": FrameID, "PointID": PointID }).then(data => {
        const is_ok = Boolean(data?.ok);
        const technical_report = data?.data?.technical_report || [];
        console.log("[DeleteItem][Summary]", {
            ok: is_ok,
            message: data?.message,
            product_id: id_product_selecting_now,
            frame_id: FrameID,
            point_id: PointID
        });
        console.log("[DeleteItem][TechnicalReport]", technical_report);
        resetControlsSinglePointAfterDelete();
        if (data?.data) {
            renderMaster(data?.data);
        }
        write_log_capture_clear(is_ok ? "Đã xóa ảnh thành công." : `Xóa ảnh thất bại: ${data?.message || "Lỗi không xác định"}`);
    });
}


function HandleClickBtnCapture(frame_id, point_id, x, y, z, rx = 180.0, ry = 0.0, rz = 0.0) {

    coordinate_after_taking_photo.x = x;
    coordinate_after_taking_photo.y = y;
    coordinate_after_taking_photo.z = z;
    coordinate_after_taking_photo.rx = rx;
    coordinate_after_taking_photo.ry = ry;
    coordinate_after_taking_photo.rz = rz;
    console.log("----📸 Đã nhấn vào chụp Cobot 6-DOF-----");

    if (current_frame_box) {
        current_frame_box.querySelectorAll(".img-item").forEach((value) => {
            if (value.dataset.has_icon_add_new) {
                delete value.dataset.has_icon_add_new;
            }
        });
    }

    let status_check = validatePoint(x, y, z, rx, ry, rz);
    if (status_check) {
        console.log(`Data gửi chụp ảnh Product:${id_product_selecting_now} Frame ID:${frame_id} Point ID${point_id} X:${x}, Y:${y}, Z:${z}, Rx:${rx}, Ry:${ry}, Rz:${rz}`);
        postData("/captureproduct/capture", {
            "product_selecting": id_product_selecting_now,
            "id_face": frame_id,
            "id_frame": frame_id,
            "id_point": point_id,
            "x": x,
            "y": y,
            "z": z,
            "rx": rx,
            "ry": ry,
            "rz": rz
        }).then(data => {
            renderMaster(data?.data);
        });
    }
}

function clampWithSafety(val, key) {
    if (!robot_safety_limits) return val;
    let min = robot_safety_limits[`${key}_min`];
    let max = robot_safety_limits[`${key}_max`];
    if (min !== undefined && val < min) {
        write_log_capture_clear(`⚠️ Trục ${key.toUpperCase()}=${val} chạm giới hạn an toàn Min (${min})!`);
        return min;
    }
    if (max !== undefined && val > max) {
        write_log_capture_clear(`⚠️ Trục ${key.toUpperCase()}=${val} chạm giới hạn an toàn Max (${max})!`);
        return max;
    }
    return val;
}

function createInputRow(label_text, placeholder, id_input) {
    const div = document.createElement("div");
    div.className = "Alight-items";

    const label = document.createElement("label");
    label.textContent = label_text;

    const input = document.createElement("input");
    input.type = "number";
    input.placeholder = placeholder;
    input.id = id_input;

    div.appendChild(label);
    div.appendChild(input);

    return div;
}

function createButtonRow(buttons) {
    const div = document.createElement("div");
    div.className = "btn-driver-capture-point";

    buttons.forEach(btn => {
        const button = document.createElement("button");
        button.id = btn.id;

        const img = document.createElement("img");
        img.src = btn.imgSrc;
        button.appendChild(img);

        const span = document.createElement("span");
        span.textContent = btn.text;
        button.appendChild(span);

        div.appendChild(button);
    });

    return div;
}

function create_table_controler(selected) {
    anonymous.innerHTML = "";

    // 6 hàng nhập tọa độ
    anonymous.appendChild(createInputRow("Nhập x:", "Tọa độ X (mm)", `input-x-${selected.point_id}`));
    anonymous.appendChild(createInputRow("Nhập y:", "Tọa độ Y (mm)", `input-y-${selected.point_id}`));
    anonymous.appendChild(createInputRow("Nhập z:", "Tọa độ Z (mm)", `input-z-${selected.point_id}`));
    anonymous.appendChild(createInputRow("Nhập rx:", "Góc Rx (°)", `input-rx-${selected.point_id}`));
    anonymous.appendChild(createInputRow("Nhập ry:", "Góc Ry (°)", `input-ry-${selected.point_id}`));
    anonymous.appendChild(createInputRow("Nhập rz:", "Góc Rz (°)", `input-rz-${selected.point_id}`));

    // 6 cặp nút tăng giảm trục
    anonymous.appendChild(createButtonRow([
        { id: `btn-inc-x-${selected.point_id}`, text: " Tăng X", imgSrc: "../static/img/add1.png" },
        { id: `btn-dec-x-${selected.point_id}`, text: " Giảm X", imgSrc: "../static/img/minus.png" }
    ]));
    anonymous.appendChild(createButtonRow([
        { id: `btn-inc-y-${selected.point_id}`, text: " Tăng Y", imgSrc: "../static/img/add1.png" },
        { id: `btn-dec-y-${selected.point_id}`, text: " Giảm Y", imgSrc: "../static/img/minus.png" }
    ]));
    anonymous.appendChild(createButtonRow([
        { id: `btn-inc-z-${selected.point_id}`, text: " Tăng Z", imgSrc: "../static/img/add1.png" },
        { id: `btn-dec-z-${selected.point_id}`, text: " Giảm Z", imgSrc: "../static/img/minus.png" }
    ]));
    anonymous.appendChild(createButtonRow([
        { id: `btn-inc-rx-${selected.point_id}`, text: " Tăng Rx", imgSrc: "../static/img/add1.png" },
        { id: `btn-dec-rx-${selected.point_id}`, text: " Giảm Rx", imgSrc: "../static/img/minus.png" }
    ]));
    anonymous.appendChild(createButtonRow([
        { id: `btn-inc-ry-${selected.point_id}`, text: " Tăng Ry", imgSrc: "../static/img/add1.png" },
        { id: `btn-dec-ry-${selected.point_id}`, text: " Giảm Ry", imgSrc: "../static/img/minus.png" }
    ]));
    anonymous.appendChild(createButtonRow([
        { id: `btn-inc-rz-${selected.point_id}`, text: " Tăng Rz", imgSrc: "../static/img/add1.png" },
        { id: `btn-dec-rz-${selected.point_id}`, text: " Giảm Rz", imgSrc: "../static/img/minus.png" }
    ]));

    // Hàng 3 nút thao tác (Chạy điểm, Chụp, Xóa ảnh)
    const actionDiv = document.createElement("div");
    actionDiv.className = "btn-driver-capture-point Alight-items-x";

    const btnRun = document.createElement("button");
    btnRun.id = `btn-run-${selected.point_id}`;
    btnRun.className = "btn";
    btnRun.innerHTML = `<img src="../static/img/run_point_location.png" alt="Chạy"><span> Chạy điểm</span>`;

    const btnCapture = document.createElement("button");
    btnCapture.id = `btn-capture-${selected.frame_id}-${selected.point_id}`;
    btnCapture.className = "btn";
    btnCapture.innerHTML = `<img src="../static/img/camera.png" alt="Chụp"><span> Chụp</span>`;

    const btnErase = document.createElement("button");
    btnErase.id = `btn-erase-${selected.frame_id}-${selected.point_id}`;
    btnErase.className = "btn";
    btnErase.innerHTML = `<img src="../static/img/eraser (5).png" alt="Xóa"><span> Xóa ảnh</span>`;

    actionDiv.appendChild(btnRun);
    actionDiv.appendChild(btnCapture);
    actionDiv.appendChild(btnErase);
    anonymous.appendChild(actionDiv);

    anonymous.style.display = "flex";
}

function HandleClickBtnIncrease_X(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(x) + 1, "x");
    element.value = new_val;
    HandleClickBtnRun(new_val, y, z, rx, ry, rz);
}
function HandleClickBtnDecrease_X(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(x) - 1, "x");
    element.value = new_val;
    HandleClickBtnRun(new_val, y, z, rx, ry, rz);
}

function HandleClickBtnIncrease_Y(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(y) + 1, "y");
    element.value = new_val;
    HandleClickBtnRun(x, new_val, z, rx, ry, rz);
}
function HandleClickBtnDecrease_Y(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(y) - 1, "y");
    element.value = new_val;
    HandleClickBtnRun(x, new_val, z, rx, ry, rz);
}

function HandleClickBtnIncrease_Z(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(z) + 1, "z");
    element.value = new_val;
    HandleClickBtnRun(x, y, new_val, rx, ry, rz);
}
function HandleClickBtnDecrease_Z(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(z) - 1, "z");
    element.value = new_val;
    HandleClickBtnRun(x, y, new_val, rx, ry, rz);
}

function HandleClickBtnIncrease_Rx(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(rx) + 1, "rx");
    element.value = new_val;
    HandleClickBtnRun(x, y, z, new_val, ry, rz);
}
function HandleClickBtnDecrease_Rx(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(rx) - 1, "rx");
    element.value = new_val;
    HandleClickBtnRun(x, y, z, new_val, ry, rz);
}

function HandleClickBtnIncrease_Ry(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(ry) + 1, "ry");
    element.value = new_val;
    HandleClickBtnRun(x, y, z, rx, new_val, rz);
}
function HandleClickBtnDecrease_Ry(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(ry) - 1, "ry");
    element.value = new_val;
    HandleClickBtnRun(x, y, z, rx, new_val, rz);
}

function HandleClickBtnIncrease_Rz(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(rz) + 1, "rz");
    element.value = new_val;
    HandleClickBtnRun(x, y, z, rx, ry, new_val);
}
function HandleClickBtnDecrease_Rz(element, x, y, z, rx, ry, rz) {
    let new_val = clampWithSafety(Number(rz) - 1, "rz");
    element.value = new_val;
    HandleClickBtnRun(x, y, z, rx, ry, new_val);
}

function write_log_capture_clear(text) {
    log_box.textContent = text;
}

function write_log_capture_append(text) {
    log_box.textContent += text;
}

//validate
function validate_render_data(data) {
    if (data?.error_code == 5002) {
        const tbody = document.querySelector(".product-table tbody");
        if (!tbody) {
            console.log("Bảng không tồn tại");
            return;
        }
        tbody.innerHTML = "";
        const row = document.createElement("tr");
        row.innerHTML = `<td>?</td><td>?</td><td>?</td><td>?</td><td>?</td><td>?</td>`;
        tbody.appendChild(row);
        write_log_capture_clear("❌ Hiện tại chưa chọn sản phẩm.\n✅ Hãy chọn lại sản phẩm.");
        return;
    }
}

// Hàm validate toàn bộ điểm theo giới hạn an toàn Robot 6-DOF
function validatePoint(x, y, z, rx = 180.0, ry = 0.0, rz = 0.0) {
    let nx = Number(x), ny = Number(y), nz = Number(z);
    let nrx = Number(rx), nry = Number(ry), nrz = Number(rz);

    if (isNaN(nx) || isNaN(ny) || isNaN(nz) || isNaN(nrx) || isNaN(nry) || isNaN(nrz)) {
        write_log_capture_clear("❌ Các thông số X, Y, Z, Rx, Ry, Rz phải là số hợp lệ và không được để trống.");
        console.log("❌ Các thông số X, Y, Z, Rx, Ry, Rz phải là số hợp lệ và không được để trống.");
        return false;
    }

    if (robot_safety_limits) {
        const checks = [
            { key: "x", name: "Trục X", val: nx },
            { key: "y", name: "Trục Y", val: ny },
            { key: "z", name: "Trục Z", val: nz },
            { key: "rx", name: "Góc Rx", val: nrx },
            { key: "ry", name: "Góc Ry", val: nry },
            { key: "rz", name: "Góc Rz", val: nrz },
        ];
        for (const item of checks) {
            let min = robot_safety_limits[`${item.key}_min`];
            let max = robot_safety_limits[`${item.key}_max`];
            if (min !== undefined && item.val < min) {
                write_log_capture_clear(`❌ ${item.name}=${item.val} nhỏ hơn giới hạn an toàn Min (${min})!`);
                return false;
            }
            if (max !== undefined && item.val > max) {
                write_log_capture_clear(`❌ ${item.name}=${item.val} vượt quá giới hạn an toàn Max (${max})!`);
                return false;
            }
        }
    }
    return true;
}
