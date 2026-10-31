import { openOptionPanel } from "./panel_manager.js";
import { active_sceen_show_video, show_video_product, scroll_container, get_camera_connection } from "./common_value.js";

const cameraConfigButton = document.getElementById("btn-open-camera-config");
const cameraConfigPanel = document.getElementById("paner-camera-config");
const cameraConfigLog = document.getElementById("camera-config-log");

const cameraConfigFields = [
    "acquisition_frame_rate", "exposure_time", "gain", "gamma",
    "black_level", "exposure_auto", "trigger_mode", "trigger_selector"
];

function renderCameraConfig(config) {
    if (!config) return;
    cameraConfigFields.forEach((field) => {
        const input = document.querySelector(`#paner-camera-config [name="${field}"]`);
        if (input && config[field] !== undefined) input.value = config[field];
    });

    const info = config.device_info;
    if (info) {
        const statusInput = document.getElementById("camera-info-status");
        const modelInput = document.getElementById("camera-info-model");
        const serialInput = document.getElementById("camera-info-serial");
        const resInput = document.getElementById("camera-info-resolution");
        const interfaceInput = document.getElementById("camera-info-interface");
        const payloadInput = document.getElementById("camera-info-payload");

        if (statusInput) {
            statusInput.value = info.status || (info.connected ? "Đang kết nối (Online)" : "Mất kết nối (Offline)");
            statusInput.classList.toggle("camera-status-online", !!info.connected);
            statusInput.classList.toggle("camera-status-offline", !info.connected);
        }
        if (modelInput) modelInput.value = info.device_model || info.device_name || "OMRON Sentech";
        if (serialInput) serialInput.value = info.serial_number || "--";
        if (resInput) resInput.value = info.resolution || `${info.width} x ${info.height} px`;
        if (interfaceInput) interfaceInput.value = info.interface || "USB3 Vision (U3V)";
        if (payloadInput) payloadInput.value = info.payload_size || "--";
    }
}

async function requestCameraConfig(url, method = "GET") {
    console.log(`[CameraConfig] Gửi request ${method} ${url}`);
    const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" }
    });
    console.log(`[CameraConfig] Backend response ${response.status} ${response.statusText}`);
    const result = await response.json();
    console.log("[CameraConfig] Dữ liệu backend trả về:", result);
    if (!response.ok) throw new Error(result.detail || "Không thể lấy thông tin camera");
    return result;
}

function openCameraConfigPanel() {
    if (!cameraConfigPanel) return;
    console.log("[CameraConfig] Đã mở panel Thông tin camera");
    openOptionPanel(cameraConfigPanel);

    // Đồng bộ giao diện với Lấy ảnh mẫu & Hiệu chuẩn kích thước
    if (scroll_container) scroll_container.innerHTML = "";
    active_sceen_show_video();
    if (get_camera_connection()) {
        show_video_product();
    }

    if (cameraConfigLog) cameraConfigLog.textContent = "Đang nạp thông tin camera...";
    requestCameraConfig("/camera/config")
        .then((result) => {
            console.log("[CameraConfig] Thông tin camera nhận được khi mở panel:", result);
            renderCameraConfig(result);
            if (cameraConfigLog) {
                const isConn = result?.device_info?.connected ?? get_camera_connection();
                cameraConfigLog.textContent = isConn
                    ? "Camera đã kết nối - Chế độ chỉ đọc (Read-only)"
                    : "⚠️ Camera đang mất kết nối (Offline)";
            }
        })
        .catch((error) => {
            console.error("[CameraConfig] Lỗi nhận thông tin camera từ backend:", error);
            if (cameraConfigLog) cameraConfigLog.textContent = error.message;
        });
}

if (cameraConfigButton && cameraConfigPanel) {
    document.getElementById("camera-config-stream")?.addEventListener("click", () => {
        active_sceen_show_video();
        show_video_product();
        if (cameraConfigLog) cameraConfigLog.textContent = "Đang phát Stream video camera";
    });

    document.getElementById("camera-config-cancel")?.addEventListener("click", async () => {
        if (cameraConfigLog) cameraConfigLog.textContent = "Đang gửi yêu cầu thoát...";
        try {
            const result = await requestCameraConfig("/camera/exit");
            console.log("[CameraConfig] Backend xác nhận thoát:", result);
            if (result.redirect_url) window.location.href = result.redirect_url;
        } catch (error) {
            console.error("[CameraConfig] Lỗi thoát cấu hình camera:", error);
            if (cameraConfigLog) cameraConfigLog.textContent = `Thoát thất bại: ${error.message}`;
        }
    });
}

document.addEventListener("click", (event) => {
    if (event.target.closest("#btn-open-camera-config")) openCameraConfigPanel();
});
