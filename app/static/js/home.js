// import {scroll_content,,SocketData,SocketLog,WIDTH_IMG_SHAPE,HEIGH_IMG_SHAPE,set_camera_connection} from "./common_value.js"
import {canvasManager,SocketData,SocketLog,scroll_container,set_camera_connection,set_tcp_connection, get_tcp_connection} from "./common_value.js"
import {postData}from "./utills/api.js";

const status_judment = document.querySelector(".paner-main-status-product");
const log_judment = document.getElementById("log_judment");
const btn_left = document.querySelector(".scroll-up");   
const btn_right = document.querySelector(".scroll-down");
const div_show_point_detect = document.getElementById("table-show-point-detect");
const toggle_judgment_images = document.getElementById("toggleBtn");
const judgment_results = new Map();
let judgment_session = null;
let judgment_complete = false;
let judgment_image_mode = false;

const circle_status_connect_camera =  document.getElementById("element-circle-status-camera");
const label_status_connect_camera = document.getElementById("status-connect-cam");
const label_status_connect_tcp = document.getElementById("header-show-status-tcp");
const circle_status_connect_tcp = document.getElementById("element-circle-status-tcp");
const element_product_count = document.getElementById("product-count");
const btn_reset_count_total = document.getElementById("btn_reset_count_total");
const element_time_display = document.getElementById("time-display");
let divCreateList_Home = [];

// ==========================================
// 1. QUẢN LÝ SỐ ĐẾM SẢN PHẨM (OK / NG / TỔNG)
// ==========================================
function renderProductCount(counts) {
  if (!element_product_count) return;
  const ok = counts?.ok ?? 0;
  const ng = counts?.ng ?? 0;
  const total = counts?.total ?? (ok + ng);
  element_product_count.textContent = `OK: ${ok} | NG: ${ng} | Tổng: ${total}`;
}

async function fetchProductCount() {
  try {
    const response = await fetch("/api/product_count");
    if (response.ok) {
      const counts = await response.json();
      renderProductCount(counts);
    }
  } catch (error) {
    console.error("Lỗi khi tải số đếm sản phẩm:", error);
  }
}

btn_reset_count_total?.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/product_count/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    if (response.ok) {
      const counts = await response.json();
      renderProductCount(counts);
    }
  } catch (error) {
    console.error("Lỗi khi reset số lượng sản phẩm:", error);
  }
});

// ==========================================
// 2. BỘ ĐẾM THỜI GIAN CHU KỲ CHẠY (RUNTIME)
// ==========================================
let cycleTimerInterval = null;
let cycleStartTime = null;
let cycleTotalItems = 0;
let cycleTimerRunning = false;

function updateCycleTimeDisplay(seconds) {
  if (!element_time_display) return;
  element_time_display.textContent = `Thời gian chạy: ${Number(seconds).toFixed(1)} s`;
}

function startCycleTimer(totalItems) {
  stopCycleTimer();
  cycleStartTime = performance.now();
  cycleTotalItems = Number(totalItems) || 0;
  cycleTimerRunning = true;
  updateCycleTimeDisplay(0);
  cycleTimerInterval = setInterval(() => {
    if (!cycleTimerRunning || !cycleStartTime) return;
    const elapsed = (performance.now() - cycleStartTime) / 1000;
    updateCycleTimeDisplay(elapsed);
  }, 100);
}

function stopCycleTimer() {
  if (cycleTimerInterval) {
    clearInterval(cycleTimerInterval);
    cycleTimerInterval = null;
  }
  if (cycleTimerRunning && cycleStartTime) {
    const elapsed = (performance.now() - cycleStartTime) / 1000;
    updateCycleTimeDisplay(elapsed);
  }
  cycleTimerRunning = false;
}

async function fetchInitialHardwareStatus() {
  try {
    const response = await fetch("/api/hardware_status");
    if (response.ok) {
      const status = await response.json();
      set_camera_connection(status.camera);
      set_tcp_connection(status.tcp);
      isConect(status.camera, circle_status_connect_camera, label_status_connect_camera, "Camera");
      isConect(status.tcp, circle_status_connect_tcp, label_status_connect_tcp, "Ethernet TCP");
    }
  } catch (error) {
    console.error("Lỗi khi tải trạng thái phần cứng ban đầu:", error);
  }
}

// Tải dữ liệu ban đầu
fetchProductCount();
fetchInitialHardwareStatus();


SocketData.on("data_output_judment", data =>{
  console.log("data judment :",data);
  handle_judment_realtime(data?.msg?.data_output_judment);
});

SocketData.on("judgment_reset", data => {
  const payload = data?.data || {};
  canvasManager.hideImagePreview();
  log_judment?.replaceChildren();
  judgment_results.clear();
  judgment_session = payload;
  judgment_complete = false;
  judgment_image_mode = true;
  if (toggle_judgment_images) toggle_judgment_images.textContent = "Ảnh master";
  setProductJudgmentStatus("--");
  if (div_show_point_detect) div_show_point_detect.innerHTML = "";
  clearJudgmentBorders();
  // Bắt đầu đếm thời gian chu kỳ từ tín hiệu bắt đầu
  startCycleTimer(payload.number_step);
});

SocketData.on("judgment_item_result", data => {
  const result = data?.data;
  if (!result) return;

  // Phòng vệ chống rò rỉ: Tự động dọn dẹp nếu sang session mới mà bị lỡ mất sự kiện judgment_reset
  if (result.session_id && judgment_session?.session_id && result.session_id !== judgment_session.session_id) {
    judgment_results.clear();
    judgment_session = { session_id: result.session_id, product_id: result.product_id };
  }

  const key = `${result.frame_id}:${result.item_id}`;
  judgment_results.set(key, result);
  markJudgmentItem(result);
  renderInspectorTable(result);
  showJudgmentImage(result);
  // Dừng đếm thời gian khi phán định xong item cuối cùng
  if (cycleTotalItems > 0 && judgment_results.size >= cycleTotalItems) {
    stopCycleTimer();
  }
});

SocketData.on("judgment_product_result", data => {
  const result = data?.data;
  if (!result) return;
  judgment_complete = true;
  setProductJudgmentStatus(result.overall ? "OK" : "NG");
  // Dừng đếm thời gian chu kỳ
  stopCycleTimer();
  // Cập nhật số đếm sản phẩm mới nhất
  if (result.counts) {
    renderProductCount(result.counts);
  } else {
    fetchProductCount();
  }
});


SocketData.on("status_camera", data =>{
  let status_connect  = Boolean(data?.status);
  set_camera_connection(status_connect);
  isConect(status_connect, circle_status_connect_camera, label_status_connect_camera, "Camera");
});

SocketData.on("status_tcp", data =>{
  let status_connect  = Boolean(data?.status);
  set_tcp_connection(status_connect);
  isConect(status_connect, circle_status_connect_tcp, label_status_connect_tcp, "Ethernet TCP");
});


SocketLog.on("log_Home", (data) => {
  if (!log_judment) return;
  const log_entry = document.createElement("p");
  log_entry.textContent = String(data?.msg ?? "");
  log_judment.append(log_entry);
  // Giới hạn tối đa 200 dòng để tránh phình to DOM tree gây chậm browser
  while (log_judment.childNodes.length > 200) {
    log_judment.removeChild(log_judment.firstChild);
  }
  log_judment.scrollTop = log_judment.scrollHeight;
});

function clearJudgmentBorders() {
  scroll_container?.querySelectorAll(".img-item").forEach(item => {
    item.style.borderColor = "";
  });
}

function markJudgmentItem(result) {
  const frame = scroll_container?.querySelector(
    `.box-frame[data-frame-id="${result.frame_id}"]`
  );
  const item = frame?.querySelector(`.img-item[data-id="${result.item_id}"]`);
  if (!item) return;
  item.style.border = "3px solid";
  item.style.borderColor = ["NO_DATA", "ERROR"].includes(result.status)
    ? "#f59e0b"
    : result.overall === true ? "#16a34a" : "#dc2626";
}

function renderInspectorTable(result) {
  if (!div_show_point_detect) return;
  div_show_point_detect.innerHTML = "";
  const table = document.createElement("table");
  table.className = "master-table";
  const header = document.createElement("tr");
  ["STT", "Tên hạng mục", "Kết quả", "Message"].forEach(text => {
    const cell = document.createElement("th");
    cell.textContent = text;
    header.appendChild(cell);
  });
  table.appendChild(header);
  Object.entries(result.inspectors || {}).forEach(([name, inspector], index) => {
    const row = document.createElement("tr");
    const values = [
      index + 1,
      inspector.display_name || name,
      inspector.status || (inspector.ok ? "OK" : "NG"),
      inspector.message || "",
    ];
    values.forEach((value, valueIndex) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      if (valueIndex === 2) {
        cell.classList.add("judgment-status-cell");
        cell.classList.add(String(value).toUpperCase() === "OK" ? "is-ok" : "is-ng");
      }
      row.appendChild(cell);
    });
    table.appendChild(row);
  });
  div_show_point_detect.appendChild(table);
}

function showJudgmentImage(result) {
  if (!result.judgment_path) return;
  canvasManager.showImagePreview(result.judgment_path);
}

function getActiveItemView() {
  const item = scroll_container?.querySelector(".img-item.active");
  const frame = item?.closest(".box-frame");
  if (!item || !frame) return null;
  return {item, frameId: frame.dataset.frameId, itemId: item.dataset.id};
}

function showActiveMasterImage() {
  const active = getActiveItemView();
  const image = active?.item.querySelector(".img_show_point");
  if (image) canvasManager.showImagePreview(image);
}

function showActiveJudgmentImage() {
  const active = getActiveItemView();
  if (!active) return;
  const result = judgment_results.get(`${active.frameId}:${active.itemId}`);
  if (!result) {
    showActiveMasterImage();
    div_show_point_detect.innerHTML = "";
    return;
  }
  renderInspectorTable(result);
  showJudgmentImage(result);
}

function selectJudgmentItem(frameId, itemId) {
  const frame = scroll_container?.querySelector(
    `.box-frame[data-frame-id="${frameId}"]`
  );
  const item = frame?.querySelector(`.img-item[data-id="${itemId}"]`);
  if (!item) return;
  scroll_container.querySelectorAll(".img-item.active").forEach(activeItem => {
    activeItem.classList.remove("active");
  });
  item.classList.add("active");
  const result = judgment_results.get(`${frameId}:${itemId}`);
  if (judgment_image_mode && result) {
    renderInspectorTable(result);
    showJudgmentImage(result);
  } else if (!judgment_image_mode) {
    div_show_point_detect.innerHTML = "";
    showActiveMasterImage();
  }
}

scroll_container?.addEventListener("click", event => {
  if (!document.getElementById("paner-main")?.classList.contains("active")) return;
  const item = event.target.closest(".img-item");
  const frame = item?.closest(".box-frame");
  if (!item || !frame) return;
  selectJudgmentItem(frame.dataset.frameId, item.dataset.id);
});

window.addEventListener("iai-point-selected", event => {
  if (!document.getElementById("paner-main")?.classList.contains("active")) return;
  const detail = event.detail || {};
  selectJudgmentItem(detail.frameId, detail.pointId);
  if (!judgment_image_mode) {
    showActiveMasterImage();
    div_show_point_detect.innerHTML = "";
    return;
  }
  const result = judgment_results.get(`${detail.frameId}:${detail.pointId}`);
  if (result) {
    renderInspectorTable(result);
    showJudgmentImage(result);
  }
});

window.addEventListener("image-view-mode", () => {
  judgment_image_mode = false;
  if (toggle_judgment_images) toggle_judgment_images.textContent = "Ảnh phán định";
  canvasManager.hideImagePreview();
  canvasManager.setWrapCanvasVisible(false);
});

toggle_judgment_images?.addEventListener("click", () => {
  if (!judgment_complete) {
    log_judment.innerHTML += "<p>Chưa có dữ liệu phán định.</p>";
    return;
  }
  judgment_image_mode = !judgment_image_mode;
  toggle_judgment_images.textContent = judgment_image_mode
    ? "Ảnh master"
    : "Ảnh phán định";
  if (!judgment_image_mode) {
    div_show_point_detect.innerHTML = "";
    showActiveMasterImage();
    return;
  }
  showActiveJudgmentImage();
});


function handle_judment_realtime(data)
{
  let arr_line = data?.arr_line;
  let img_package = data?.img;
  let index = data?.index;
  let status_judment_frame = data?.judment_frame;
  if (arr_line && img_package && index != undefined && status_judment_frame != undefined){
    console.log(`Dữ liệu phán định tại index:${index} hợp lệ.`);
    const table = create_show_table(arr_line);
    div_show_point_detect.innerHTML = "";
    div_show_point_detect.appendChild(table);
        Run_div(index,status_judment_frame,divCreateList_Home);
     
        // CSS inline để ảnh không quá to làm vỡ bảng
   
        canvasManager.setWrapCanvasVisible(false);
   
        let status_judment = data?.judment;
        if (status_judment == undefined){
             setStatusDefault();
            
        }
        else if (status_judment){
            setStatusOK();
            clearn_div_img(divCreateList_Home);
        }
        else{
             setStatusNG();
            clearn_div_img(divCreateList_Home);
        }
        
  }
}


function Run_div(index, status_frame, div_card) {
  if (!div_card || !div_card[index]) return; // tránh lỗi nếu index sai

  // Xóa class cũ (nếu có)
  div_card[index].classList.remove('ok', 'erro');

  // Thêm class tương ứng
  if (status_frame) {
    div_card[index].classList.add('ok');
  } else {
    div_card[index].classList.add('erro');
  }
}


function create_show_table(data) {
  const headers = ["STT", "Tên line", "Chiều dài", "Level", "Trạng thái"];
  const table = document.createElement("table");
  table.className = "master-table";

  // 1. Tạo phần đầu (thead)
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  headerRow.className = "master-header";
  
  headers.forEach(text => {
    const th = document.createElement("th");
    th.textContent = text;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // 2. Tạo phần thân (tbody)
  const tbody = document.createElement("tbody");
  
  data?.forEach((item, index) => {
    const tr = document.createElement("tr");
    tr.className = "point-table";

    // --- XỬ LÝ LOGIC TẠI ĐÂY ---
    
    // Làm tròn chiều dài (width) - dùng Math.round()
    const displayWidth = (item?.width != null) ? Number(item.width).toFixed(3) : "";
    // Chuyển đổi trạng thái (status)
    const displayStatus = item?.status === true ? "OK" : (item?.status === false ? "NG" : "");
   
    const fields = [
      index + 1,          // STT
      item?.name_line, 
      displayWidth,       // Đã làm tròn
      item?.level, 
      displayStatus       // Hiển thị OK nếu true
    ];
    
    fields.forEach(text => {
      const td = document.createElement("td");
      td.textContent = text ?? ""; 
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });
  
  table.appendChild(tbody);
  return table;
}


function RenderDataHome(data){
    // scroll_content.innerHTML = "";

    canvasManager.setWrapCanvasVisible(false);
    let status = data?.status;
    if (status == "erro"){
        console.log("Lỗi chọn sản phẩm ");
    }
    else{   
            const imgList = data?.path_arr_img;

            // console.log("Danh sách ảnh:", imgList);
        //     imgList.forEach((imgPath, index) => {
        //         const div_create = document.createElement("div");
        //         div_create.className = "div-index-img-mater";
        //         const h_create = document.createElement("p");
        //         h_create.innerText = `Ảnh master ${index}`;
        //         h_create.className = "p-index-img-master";
        //         const img = document.createElement("img");
        //         img.src = `${imgPath}?t=${Date.now()}`;  // dam bao  goi moi nhat
        //         img.alt = "Ảnh sản phẩm";
        //         img.style.width = "200px";
        //         img.style.margin = "10px";
        //         div_create.appendChild(img);
        //         div_create.appendChild(h_create);
        //         scroll_content.appendChild(div_create);
        //         divCreateList_Home.push(div_create);
        //         div_create.addEventListener("click", function () {
        //             clearn_div(divCreateList_Home);
        //             console.log("Ảnh master đang chỉ tới là", index);
        //             div_create.classList.add("div_click");
        //        
        //         });
        // });
    }
}
function clearn_div_img(div_card) {
  if (!div_card) return;
  for (let i = 0; i < div_card.length; i++) {
    div_card[i].classList.remove('ok', 'erro');
  }
}
function resetStatusDisplay() {
      status_judment.innerHTML ="--";
      status_judment.classList.remove("WARNING");
      status_judment.classList.remove("NG");
      status_judment.classList.remove("OK");
}
function setStatusOK() {
    resetStatusDisplay();
    status_judment.classList.add("OK");
    status_judment.innerHTML = "OK";
}

function setStatusWarning() {
    resetStatusDisplay();
    status_judment.classList.add("WARNING");
    status_judment.innerHTML = "⚠️ CẢNH BÁO";
}
function setStatusDefault() {
    resetStatusDisplay();
    status_judment.innerHTML = "--";
}
function setStatusNG() {
    resetStatusDisplay();
    status_judment.classList.add("NG");
    status_judment.innerHTML = "NG";
}

function isConect(isconect,element_circle,element_lable,str_lable){
    if (isconect) {
        element_circle.classList.remove("off");
        element_circle.classList.add("on");
        element_lable.innerText = `${str_lable} đã kết nối`;
        } else {
        element_circle.classList.add("off");
        element_circle.classList.remove("on");
        element_lable.innerText = `${str_lable} mất kết nối`;
    }  
}

function setProductJudgmentStatus(status) {
  if (!status_judment) return;
  status_judment.textContent = status;
  status_judment.classList.remove("OK", "NG", "WARNING", "ERRO", "PENDING");
  status_judment.classList.add(status === "OK" || status === "NG" ? status : "PENDING");
}