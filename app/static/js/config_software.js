/**
 * CONFIG SOFTWARE / PREFERENCES DIALOG CONTROLLER (UI ONLY)
 * Xử lý giao diện: Mở/đóng panel, chuyển tab Sidebar cây danh mục 2 cột,
 * tìm kiếm lọc danh mục, phím tắt Escape và giữ nguyên popup Thông tin phần mềm.
 */

// DOM Elements
const btn_config_software = document.getElementById("btn-open-software-config");
const btn_close_settings = document.getElementById("close-settings");
const btn_cancel_settings = document.getElementById("btn-pref-cancel");
const btn_ok_settings = document.getElementById("save-settings");
const btn_apply_settings = document.getElementById("btn-pref-apply");
const btn_defaults_settings = document.getElementById("btn-pref-defaults");
const overlay_config_software = document.getElementById("overlay_config_software");

// Header info elements
const pref_header_icon = document.getElementById("pref-header-icon");
const pref_header_title = document.getElementById("pref-header-title");
const pref_header_desc = document.getElementById("pref-header-desc");
const pref_search_input = document.getElementById("pref-search-input");
const pref_tree_menu = document.getElementById("pref-tree-menu");

// Category metadata for content header
const TAB_METADATA = {
    "tab-system-general": {
        icon: "🖥️",
        title: "System — General & View",
        desc: "Cấu hình các tham số vận hành chung, hiển thị và giao diện hệ thống",
    },
    "tab-system-logs": {
        icon: "📁",
        title: "System — Log & Retention",
        desc: "Cấu hình phân vùng ổ đĩa, chu kỳ lưu trữ và các kênh ghi dữ liệu nhật ký",
    },
    "tab-robot-network": {
        icon: "🌐",
        title: "Robot & Motion — Kết nối mạng Ethernet + TCP Socket",
        desc: "Cấu hình địa chỉ IP, cổng giao tiếp và thử nghiệm kết nối mạng trực tiếp tới PLC",
    },
    "tab-robot-safety": {
        icon: "🛡️",
        title: "Robot & Motion — Giới hạn an toàn không gian làm việc",
        desc: "Cài đặt hộp không gian Bounding Box, bán kính tầm với và góc xoay bảo vệ cáp Camera",
    },
    "tab-camera-imaging": {
        icon: "📷",
        title: "Imaging — Anti-Blur Service (Chống Rung Nhòe)",
        desc: "Cấu hình định thời dừng Stop-and-Shoot, bảo vệ phơi sáng và cổng kiểm soát độ nét ảnh",
    },
    "tab-ai-yolo-object": {
        icon: "📦",
        title: "AI & Judgment — Mô hình YOLO Object",
        desc: "Cấu hình nhận diện Có/Không tem (Stamp) và dị vật",
    },
    "tab-ai-patchcore": {
        icon: "🧠",
        title: "AI & Judgment — Mô hình PatchCore Anomaly",
        desc: "Cấu hình phát hiện dị vật lạ và điểm bất thường qua ngân hàng vector đặc trưng FAISS Memory Bank",
    },
};

// ==========================================
// MỞ VÀ ĐÓNG MODAL
// ==========================================
function openConfigSoftware() {
    if (overlay_config_software) {
        overlay_config_software.style.display = "flex";
        loadAntiBlurConfig();
        loadLogRetentionConfig();
        loadAIModelPaths();
        loadSoftwareInfo();
        loadRobotConfig();
    }
}

function closeConfigSoftware() {
    if (overlay_config_software) {
        overlay_config_software.style.display = "none";
    }
}

/**
 * Nạp đường dẫn chi tiết của các mô hình AI từ backend API /software/ai_model_paths
 */
async function loadAIModelPaths() {
    try {
        const response = await fetch("/software/ai_model_paths");
        if (!response.ok) return;
        const res = await response.json();
        if (res.status && res.paths) {
            const p = res.paths;
            // YOLO Object
            setInputValue("pref-path-yolo-obj-stamp", p.yolo_obj_stamp);
            setInputValue("pref-path-yolo-obj-foreign", p.yolo_obj_foreign);
            // PatchCore
            setInputValue("pref-path-patchcore-model", p.patchcore_model_folder);
            setInputValue("pref-path-patchcore-index", p.patchcore_index);
        }
    } catch (err) {
        console.warn("[AI-CONFIG] Lỗi khi nạp đường dẫn mô hình AI:", err);
    }
}

if (btn_config_software) {
    btn_config_software.addEventListener("click", openConfigSoftware);
}

if (btn_close_settings) {
    btn_close_settings.addEventListener("click", closeConfigSoftware);
}

if (btn_cancel_settings) {
    btn_cancel_settings.addEventListener("click", closeConfigSoftware);
}

if (btn_ok_settings) {
    btn_ok_settings.addEventListener("click", async () => {
        btn_ok_settings.disabled = true;
        setApplyStatus("loading", "Đang lưu cấu hình...");
        try {
            const [logOk, blurOk, robotOk] = await Promise.all([
                saveLogRetentionConfig(false),
                saveAntiBlurConfig(),
                saveRobotConfig(),
            ]);
            if (logOk && blurOk && robotOk) {
                closeConfigSoftware();
            } else {
                setApplyStatus("error", "Lưu cấu hình không thành công");
            }
        } finally {
            btn_ok_settings.disabled = false;
        }
    });
}

// Đóng modal khi nhấn phím Escape
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && overlay_config_software && overlay_config_software.style.display === "flex") {
        closeConfigSoftware();
    }
});

// ==========================================
// CHUYỂN TAB ĐIỀU HƯỚNG SIDEBAR
// ==========================================
function switchTab(tabId) {
    if (!tabId) return;

    // 1. Cập nhật active trong cây menu
    const allNodes = document.querySelectorAll(".pref-tree-node, .pref-tree-subitem");
    allNodes.forEach((node) => {
        if (node.getAttribute("data-tab") === tabId) {
            node.classList.add("active");
            // Mở nhóm cha nếu đang đóng
            const group = node.closest(".pref-tree-group");
            if (group) {
                const sublist = group.querySelector(".pref-tree-sublist");
                const arrow = group.querySelector(".pref-tree-arrow");
                if (sublist) sublist.classList.add("open");
                if (arrow) arrow.classList.add("expanded");
            }
        } else {
            node.classList.remove("active");
        }
    });

    // 2. Ẩn tất cả tab panels và hiển thị tab được chọn
    const allPanels = document.querySelectorAll(".pref-tab-panel");
    allPanels.forEach((panel) => {
        panel.style.display = "none";
    });

    const activePanel = document.getElementById(tabId);
    if (activePanel) {
        activePanel.style.display = "block";
    }

    // Nạp lại cấu hình nếu người dùng chuyển sang tab Imaging, Log hoặc các tab AI
    if (tabId === "tab-camera-imaging") {
        loadAntiBlurConfig();
    } else if (tabId === "tab-system-logs") {
        loadLogRetentionConfig();
    } else if (tabId.startsWith("tab-ai-")) {
        loadAIModelPaths();
    }

    // 3. Cập nhật header title & desc
    const meta = TAB_METADATA[tabId];
    if (meta) {
        if (pref_header_icon) pref_header_icon.textContent = meta.icon;
        if (pref_header_title) pref_header_title.textContent = meta.title;
        if (pref_header_desc) pref_header_desc.textContent = meta.desc;
    }
}

// Bắt sự kiện click vào các item cây menu
if (pref_tree_menu) {
    pref_tree_menu.addEventListener("click", (e) => {
        // Xử lý click vào mũi tên mở rộng / thu gọn
        const arrow = e.target.closest(".pref-tree-arrow");
        if (arrow) {
            e.stopPropagation();
            const group = arrow.closest(".pref-tree-group");
            const sublist = group ? group.querySelector(".pref-tree-sublist") : null;
            if (sublist) {
                const isOpen = sublist.classList.toggle("open");
                arrow.classList.toggle("expanded", isOpen);
            }
            return;
        }

        // Xử lý click vào node cha hoặc node con
        const item = e.target.closest(".pref-tree-node, .pref-tree-subitem");
        if (item) {
            const tabId = item.getAttribute("data-tab");
            if (tabId) {
                switchTab(tabId);
            } else {
                // Nếu click vào node cha không có tab riêng, mở sublist
                const group = item.closest(".pref-tree-group");
                const sublist = group ? group.querySelector(".pref-tree-sublist") : null;
                const nodeArrow = group ? group.querySelector(".pref-tree-arrow") : null;
                if (sublist) {
                    const isOpen = sublist.classList.toggle("open");
                    if (nodeArrow) nodeArrow.classList.toggle("expanded", isOpen);
                }
            }
        }
    });
}

// ==========================================
// TÌM KIẾM LỌC DANH MỤC TRONG SIDEBAR
// ==========================================
if (pref_search_input) {
    pref_search_input.addEventListener("input", (e) => {
        const query = e.target.value.trim().toLowerCase();
        const groups = document.querySelectorAll(".pref-tree-group");

        groups.forEach((group) => {
            let groupHasMatch = false;
            const parentNode = group.querySelector(".pref-tree-node");
            const subitems = group.querySelectorAll(".pref-tree-subitem");
            const sublist = group.querySelector(".pref-tree-sublist");
            const arrow = group.querySelector(".pref-tree-arrow");

            const parentText = parentNode ? parentNode.textContent.toLowerCase() : "";
            if (parentText.includes(query)) {
                groupHasMatch = true;
            }

            subitems.forEach((sub) => {
                const subText = sub.textContent.toLowerCase();
                if (subText.includes(query) || parentText.includes(query)) {
                    sub.style.display = "flex";
                    groupHasMatch = true;
                } else {
                    sub.style.display = query ? "none" : "flex";
                }
            });

            if (groupHasMatch || !query) {
                group.style.display = "block";
                if (query && sublist) {
                    sublist.classList.add("open");
                    if (arrow) arrow.classList.add("expanded");
                }
            } else {
                group.style.display = "none";
            }
        });
    });
}

// ==========================================
// CÁC NÚT TÁC VỤ GIAO DIỆN (UI FEEDBACK)
// ==========================================
const pref_apply_status = document.getElementById("pref-apply-status");

/** Hiển thị trạng thái Apply / Defaults ở footer Preferences */
function setApplyStatus(type, msg) {
    if (!pref_apply_status) return;
    const colors = { success: "#4ade80", error: "#f87171", loading: "#94a3b8", info: "#60a5fa" };
    const icons = { success: "✔", error: "❌", loading: "⏳", info: "ℹ️" };
    pref_apply_status.style.color = colors[type] || colors.info;
    pref_apply_status.textContent = `${icons[type] || ""} ${msg} (${new Date().toLocaleTimeString()})`;
}

if (btn_apply_settings) {
    btn_apply_settings.addEventListener("click", async () => {
        btn_apply_settings.disabled = true;
        setApplyStatus("loading", "Đang lưu cấu hình...");
        try {
            const [logOk, blurOk, robotOk] = await Promise.all([
                saveLogRetentionConfig(false),
                saveAntiBlurConfig(),
                saveRobotConfig(),
            ]);
            const failed = [];
            if (!logOk) failed.push("System/Log");
            if (!blurOk) failed.push("Camera/Imaging");
            if (!robotOk) failed.push("Robot/Motion");
            if (failed.length === 0) {
                setApplyStatus("success", "Đã lưu đồng bộ cấu hình thành công");
            } else {
                setApplyStatus("error", "Lưu thất bại: " + failed.join(", "));
            }
        } finally {
            btn_apply_settings.disabled = false;
        }
    });
}

if (btn_defaults_settings) {
    btn_defaults_settings.addEventListener("click", async () => {
        btn_defaults_settings.disabled = true;
        setApplyStatus("loading", "Đang nạp cấu hình mặc định từ backend...");
        try {
            const [logRes, blurRes, robotRes] = await Promise.all([
                fetch("/software/config_logs/defaults").then((r) => r.json()),
                fetch("/api/anti_blur/defaults").then((r) => r.json()),
                fetch("/api/robot/defaults").then((r) => r.json()),
            ]);
            if (!(logRes.status && logRes.data) || !(blurRes.status && blurRes.data) || !(robotRes.status && robotRes.data)) {
                throw new Error("Backend không trả về cấu hình mặc định hợp lệ");
            }

            // Robot & Motion
            applyRobotConfigToForm(robotRes.data);

            // Log & Retention
            applyLogConfigToForm(logRes.data, logRes.retrain_folder_path);

            // Anti-Blur / Imaging
            const d = blurRes.data;
            setInputValue("pref-antiblur-t-settle", d.t_settle_ms);
            setInputValue("pref-antiblur-t-hold", d.t_hold_safety_ms);
            setInputValue("pref-antiblur-t-exp", d.t_exp_ms);
            setSelectValue("pref-antiblur-trigger-mode", d.is_hardware_trigger ? "hardware" : "software");
            setInputValue("pref-antiblur-threshold", d.blur_threshold);
            setCheckboxValue("pref-antiblur-auto-retrigger", d.auto_retrigger_on_blur);
            setInputValue("pref-antiblur-max-retry", d.max_retrigger_count);
            setInputValue("pref-antiblur-extra-settle", d.extra_settle_ms);
            setInputValue("pref-antiblur-fov", d.fov_mm);
            setInputValue("pref-antiblur-sensor-px", d.sensor_px);
            setInputValue("pref-antiblur-b-max", d.b_max_px);
            setInputValue("pref-antiblur-a0", d.a0_um);
            setInputValue("pref-antiblur-fn", d.fn_hz);
            setInputValue("pref-antiblur-zeta", d.zeta);
            setTextContent("badge-t-exp-source", `(mặc định: ${d.t_exp_ms} ms)`);
            await calculateAntiBlurTimers();
            // calculateAntiBlurTimers ghi đè T_settle/T_hold theo URD; đặt lại đúng giá trị mặc định backend
            setInputValue("pref-antiblur-t-settle", d.t_settle_ms);
            setInputValue("pref-antiblur-t-hold", d.t_hold_safety_ms);

            // Các tab AI: đưa ô nhập (không readonly) về giá trị mặc định ban đầu của giao diện
            document.querySelectorAll(".pref-tab-panel[id^='tab-ai-'] input, .pref-tab-panel[id^='tab-ai-'] select").forEach((el) => {
                if (el.readOnly) return;
                if (el.type === "checkbox" || el.type === "radio") {
                    el.checked = el.defaultChecked;
                } else if (el.tagName === "SELECT") {
                    Array.from(el.options).forEach((o) => { o.selected = o.defaultSelected; });
                } else {
                    el.value = el.defaultValue;
                }
            });
            await loadAIModelPaths();
            setInputValue("pref-max-judger-workers", 5);

            setApplyStatus("info", "Đã đặt về mặc định (chưa lưu – nhấn Apply để lưu)");
        } catch (err) {
            console.error("[PREFERENCES] Lỗi đặt mặc định:", err);
            setApplyStatus("error", "Không thể nạp cấu hình mặc định từ backend");
        } finally {
            btn_defaults_settings.disabled = false;
        }
    });
}

// ==========================================
// LOG & RETENTION CONFIG CONTROLLER
// ==========================================
const btn_browse_log_dir = document.getElementById("btn-browse-log-dir");
const pref_toggle_retrain = document.getElementById("pref-toggle-retrain");
const retrain_inspectors_wrapper = document.getElementById("retrain-inspectors-wrapper");

/**
 * Cập nhật trạng thái hiển thị của khu vực 6 hạng mục retrain
 * Khi master switch tắt: làm mờ và vô hiệu hóa tương tác
 */
function updateRetrainSectionState(isOpen) {
    if (!retrain_inspectors_wrapper) return;
    if (isOpen) {
        retrain_inspectors_wrapper.classList.remove("retrain-disabled");
    } else {
        retrain_inspectors_wrapper.classList.add("retrain-disabled");
    }
    const toggles = document.querySelectorAll(".retrain-inspector-toggle");
    toggles.forEach((t) => {
        t.disabled = !isOpen;
    });
}

if (pref_toggle_retrain) {
    pref_toggle_retrain.addEventListener("change", (e) => {
        updateRetrainSectionState(e.target.checked);
    });
}

// Xử lý nút Browse mở hộp thoại chọn thư mục Windows
if (btn_browse_log_dir) {
    btn_browse_log_dir.addEventListener("click", async () => {
        const originText = btn_browse_log_dir.textContent;
        btn_browse_log_dir.textContent = "⏳ Đang mở...";
        try {
            const response = await fetch("/software/browse_log_dir", { method: "POST" });
            const res = await response.json();
            if (res.status && res.selected_path) {
                setInputValue("pref-log-dir", res.selected_path);
            }
        } catch (err) {
            console.error("[LOG-RETENTION] Lỗi khi mở hộp thoại chọn thư mục:", err);
        } finally {
            btn_browse_log_dir.textContent = originText;
        }
    });
}

const btn_browse_output_dir = document.getElementById("btn-browse-output-dir");
if (btn_browse_output_dir) {
    btn_browse_output_dir.addEventListener("click", async () => {
        const originText = btn_browse_output_dir.textContent;
        btn_browse_output_dir.textContent = "⏳ Đang mở...";
        try {
            const response = await fetch("/software/browse_output_dir", { method: "POST" });
            const res = await response.json();
            if (res.status && res.selected_path) {
                setInputValue("pref-output-dir", res.selected_path);
                setInputValue("pref-retrain-folder-path", `${res.selected_path}\\retrain`);
            }
        } catch (err) {
            console.error("[OUTPUT-DIR] Lỗi khi mở hộp thoại chọn thư mục output:", err);
        } finally {
            btn_browse_output_dir.textContent = originText;
        }
    });
}

/**
 * Nạp cấu hình Log & Retention từ backend API /software/config_logs
 */
async function loadLogRetentionConfig() {
    try {
        const response = await fetch("/software/config_logs");
        if (!response.ok) throw new Error("Network response was not ok");
        const res = await response.json();
        if (res.status && res.data) {
            applyLogConfigToForm(res.data, res.retrain_folder_path);
        }
    } catch (err) {
        console.error("[LOG-RETENTION] Lỗi nạp cấu hình log:", err);
    }
}

/**
 * Đổ dữ liệu cấu hình Log (từ GET config hoặc defaults) vào các ô input
 */
function applyLogConfigToForm(d, retrainFolderPath) {
    // 1. Đường dẫn thư mục log & output
    const logDirPath = d.log_dir || d.disk_select || "C:\\Log";
    setInputValue("pref-log-dir", logDirPath);

    if (d.output_dir) {
        setInputValue("pref-output-dir", d.output_dir);
    }

    // 2. Thời gian lưu log hợp nhất (ngày)
    const retentionDays = d.time_save_log ?? d.time_save_img ?? 30;
    setInputValue("set-time-save-log", retentionDays);

    // 3. Trạng thái các switch bật/tắt kênh log & hiển thị
    setCheckboxValue("pref-toggle-img", d.open_img ?? true);
    setCheckboxValue("pref-toggle-csv", d.open_csv ?? true);
    setCheckboxValue("pref-toggle-txt", d.open_txt ?? true);
    setCheckboxValue("set-cosole", d.open_log_cosole ?? true);
    setInputValue("pref-max-judger-workers", d.max_judger_workers ?? 5);

    // 4. Đường dẫn tuyệt đối thư mục retrain
    if (retrainFolderPath) {
        setInputValue("pref-retrain-folder-path", retrainFolderPath);
    }

    // 5. Cấu hình thu thập ảnh retrain
    const isRetrainOpen = Boolean(d.open_retrain);
    setCheckboxValue("pref-toggle-retrain", isRetrainOpen);

    // 6. Cập nhật 6 inspector switches
    const inspectorToggles = document.querySelectorAll(".retrain-inspector-toggle");
    inspectorToggles.forEach((toggle) => {
        const inspectorName = toggle.getAttribute("data-inspector");
        if (inspectorName && d.retrain_inspectors && d.retrain_inspectors[inspectorName] !== undefined) {
            toggle.checked = Boolean(d.retrain_inspectors[inspectorName]);
        } else {
            // Mặc định bật nếu chưa cấu hình
            toggle.checked = true;
        }
    });

    // Đồng bộ trạng thái giao diện khu vực inspector
    updateRetrainSectionState(isRetrainOpen);
}

/**
 * Thu thập dữ liệu từ giao diện và gửi POST /software/config_logs
 */
async function saveLogRetentionConfig(showBanner = false) {
    // Thu thập trạng thái 6 hạng mục inspector
    const retrainInspectors = {};
    const inspectorToggles = document.querySelectorAll(".retrain-inspector-toggle");
    inspectorToggles.forEach((toggle) => {
        const inspectorName = toggle.getAttribute("data-inspector");
        if (inspectorName) {
            retrainInspectors[inspectorName] = Boolean(toggle.checked);
        }
    });

    const payload = {
        log_dir: getInputValue("pref-log-dir", "C:\\Log"),
        output_dir: getInputValue("pref-output-dir", ""),
        time_save_log: parseInt(getInputValue("set-time-save-log", 30), 10) || 30,
        open_img: getCheckboxValue("pref-toggle-img", true),
        open_csv: getCheckboxValue("pref-toggle-csv", true),
        open_txt: getCheckboxValue("pref-toggle-txt", true),
        open_log_cosole: getCheckboxValue("set-cosole", true),
        max_judger_workers: Math.min(10, Math.max(1, parseInt(getInputValue("pref-max-judger-workers", 5), 10) || 5)),
        open_retrain: getCheckboxValue("pref-toggle-retrain", false),
        retrain_inspectors: retrainInspectors,
    };

    try {
        const response = await fetch("/software/config_logs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const res = await response.json();
        if (res.status) return true;
    } catch (err) {
        console.error("[LOG-RETENTION] Lỗi lưu cấu hình log:", err);
    }
    return false;
}


// ==========================================
// THÔNG TIN PHẦN MỀM (HIỂN THỊ TRONG TAB GENERAL & VIEW)
// ==========================================
async function loadSoftwareInfo() {
    try {
        const response = await fetch("/software/information");
        if (!response.ok) return;
        const data = await response.json();
        const s = data.software || {};
        setInputValue("pref-info-name", s.name);
        setInputValue("pref-info-version", s.version);
        setInputValue("pref-info-author", s.author);
        setInputValue("pref-info-company", s.company);
        setInputValue("pref-info-description", s.description);
        setInputValue("pref-info-build-date", s.build_date);
        setInputValue("pref-info-license", s.license);
    } catch (err) {
        console.warn("[SOFTWARE-INFO] Lỗi nạp thông tin phần mềm:", err);
    }
}

// ==========================================
// ANTI-BLUR / IMAGING CONFIG CONTROLLER
// ==========================================
async function loadAntiBlurConfig() {
    try {
        const response = await fetch("/api/anti_blur/config");
        if (!response.ok) return;
        const res = await response.json();
        if (!res.status || !res.data) return;

        const d = res.data;
        // Stop & Shoot timing
        setInputValue("pref-antiblur-t-settle", d.t_settle_ms);
        setInputValue("pref-antiblur-t-hold", d.t_hold_safety_ms);
        setInputValue("pref-antiblur-t-exp", d.t_exp_ms);
        setSelectValue("pref-antiblur-trigger-mode", d.is_hardware_trigger ? "hardware" : "software");

        // Sharpness Gate
        setInputValue("pref-antiblur-threshold", d.blur_threshold);
        setCheckboxValue("pref-antiblur-auto-retrigger", d.auto_retrigger_on_blur);
        setInputValue("pref-antiblur-max-retry", d.max_retrigger_count);
        setInputValue("pref-antiblur-extra-settle", d.extra_settle_ms);

        // Physics parameters
        setInputValue("pref-antiblur-fov", d.fov_mm);
        setInputValue("pref-antiblur-sensor-px", d.sensor_px);
        setInputValue("pref-antiblur-b-max", d.b_max_px);
        setInputValue("pref-antiblur-a0", d.a0_um);
        setInputValue("pref-antiblur-fn", d.fn_hz);
        setInputValue("pref-antiblur-zeta", d.zeta);

        if (d.t_exp_ms) {
            setTextContent("badge-t-exp-source", `(hiện tại: ${d.t_exp_ms} ms)`);
        }

        if (res.calculated) {
            updateCalcDisplay(res.calculated);
        }

        setBannerStatus("info", "Đã nạp 14 tham số cấu hình hiện tại từ storage.");
    } catch (err) {
        console.warn("[ANTI-BLUR] Không thể nạp cấu hình:", err);
    }
}

function updateCalcDisplay(c) {
    if (!c) return;
    setTextContent("calc-res-r", c.resolution_um_per_px ?? "20.00");
    setTextContent("calc-res-a-allow", c.allowed_vibration_um ?? "10.00");
    setTextContent("calc-res-t-settle", c.t_settle_ms ?? c.recommended_t_settle_ms ?? "64.05");
    setTextContent("calc-res-t-hold", c.t_hold_ms ?? c.recommended_t_hold_ms ?? "17.00");
    setTextContent("calc-res-total-stop", c.t_total_stop_ms ?? c.recommended_t_total_stop_ms ?? "81.05");
}

function setBannerStatus(type, msg) {
    const iconElem = document.getElementById("antiblur-banner-icon");
    const msgElem = document.getElementById("antiblur-banner-msg");
    const timeElem = document.getElementById("antiblur-banner-timestamp");
    const now = new Date();
    const timeStr = now.toLocaleTimeString();

    if (msgElem) msgElem.textContent = msg;
    if (timeElem) timeElem.textContent = `Lúc: ${timeStr}`;

    if (iconElem) {
        if (type === "success") iconElem.textContent = "✔";
        else if (type === "warning") iconElem.textContent = "⚠️";
        else if (type === "error") iconElem.textContent = "❌";
        else if (type === "loading") iconElem.textContent = "⏳";
        else iconElem.textContent = "ℹ️";
    }
}

function getAntiBlurPayload() {
    return {
        t_settle_ms: parseFloat(getInputValue("pref-antiblur-t-settle", 40.0)),
        t_hold_safety_ms: parseFloat(getInputValue("pref-antiblur-t-hold", 15.0)),
        t_exp_ms: parseFloat(getInputValue("pref-antiblur-t-exp", 2.0)),
        is_hardware_trigger: getSelectValue("pref-antiblur-trigger-mode") === "hardware",
        blur_threshold: parseFloat(getInputValue("pref-antiblur-threshold", 100.0)),
        auto_retrigger_on_blur: getCheckboxValue("pref-antiblur-auto-retrigger", true),
        max_retrigger_count: parseInt(getInputValue("pref-antiblur-max-retry", 1), 10),
        extra_settle_ms: parseFloat(getInputValue("pref-antiblur-extra-settle", 20.0)),
        fov_mm: parseFloat(getInputValue("pref-antiblur-fov", 40.0)),
        sensor_px: parseInt(getInputValue("pref-antiblur-sensor-px", 2000), 10),
        b_max_px: parseFloat(getInputValue("pref-antiblur-b-max", 0.5)),
        a0_um: parseFloat(getInputValue("pref-antiblur-a0", 50.0)),
        fn_hz: parseFloat(getInputValue("pref-antiblur-fn", 50.0)),
        zeta: parseFloat(getInputValue("pref-antiblur-zeta", 0.08)),
        t_safety_ms: getSelectValue("pref-antiblur-trigger-mode") === "hardware" ? 2.0 : 5.0,
    };
}

async function saveAntiBlurConfig() {
    const payload = getAntiBlurPayload();
    setBannerStatus("loading", "Đang lưu cấu hình vào app/storage/anti_blur.json...");
    try {
        const response = await fetch("/api/anti_blur/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const res = await response.json();
        if (res.status) {
            setBannerStatus("success", "Đã lưu cấu hình Anti-Blur thành công vào app/storage/anti_blur.json và đồng bộ IAI runtime!");
            return true;
        }
        setBannerStatus("error", "Lưu thất bại: " + (res.message || "Không xác định"));
    } catch (err) {
        setBannerStatus("error", "Lỗi kết nối khi lưu cấu hình Anti-Blur!");
    }
    return false;
}

async function calculateAntiBlurTimers() {
    const payload = getAntiBlurPayload();
    setBannerStatus("loading", "Đang tính toán các thông số dao động URD...");
    try {
        const response = await fetch("/api/anti_blur/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const res = await response.json();
        if (res.status && res.data) {
            updateCalcDisplay(res.data);
            setInputValue("pref-antiblur-t-settle", Math.round(res.data.t_settle_ms));
            setInputValue("pref-antiblur-t-hold", Math.round(res.data.t_hold_ms));
            setBannerStatus("success", `Tính toán URD thành công! Đã điền T_settle: ${Math.round(res.data.t_settle_ms)}ms, T_hold: ${Math.round(res.data.t_hold_ms)}ms.`);
        }
    } catch (err) {
        console.error("[ANTI-BLUR] Lỗi tính toán:", err);
        setBannerStatus("error", "Lỗi tính toán mô hình URD!");
    }
}

/**
 * [BƯỚC 1]: NẠP CẤU HÌNH TỪ features.cfg
 * Tự động đồng bộ phần cứng, trích xuất ExposureTime và chuỗi tính toán lại URD ngay lập tức.
 */
async function reloadFeaturesCfg() {
    setBannerStatus("loading", "Đang nạp file features.cfg và kết nối Camera...");
    try {
        const response = await fetch("/api/anti_blur/reload_features", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });
        const res = await response.json();
        if (res.status && res.hardware_info) {
            const expMs = res.hardware_info.exposure_time_ms;
            setInputValue("pref-antiblur-t-exp", expMs);
            setTextContent("badge-t-exp-source", `(đồng bộ features.cfg: ${expMs} ms)`);

            // Tự động kích hoạt tính toán lại URD với ExposureTime mới
            await calculateAntiBlurTimers();

            const statusType = res.camera_applied ? "success" : "warning";
            setBannerStatus(statusType, `${res.message} → T_exp: ${expMs}ms đã được cập nhật vào URD!`);
        } else {
            setBannerStatus("error", res.message || "Không thể đọc file features.cfg");
        }
    } catch (err) {
        console.error("[ANTI-BLUR] Lỗi nạp features.cfg:", err);
        setBannerStatus("error", "Lỗi kết nối khi nạp file features.cfg!");
    }
}

/**
 * [KHÔI PHỤC MẶC ĐỊNH]: CƠ CHẾ DỰ PHÒNG THAM SỐ CHUẨN AN TOÀN
 */
async function restoreAntiBlurDefaults() {
    setBannerStatus("loading", "Đang khôi phục các tham số mặc định an toàn...");
    try {
        const response = await fetch("/api/anti_blur/defaults");
        const res = await response.json();
        const d = res.status && res.data ? res.data : {
            fov_mm: 40.0, sensor_px: 2000, b_max_px: 0.5, a0_um: 50.0, fn_hz: 50.0, zeta: 0.08,
            t_exp_ms: 2.0, is_hardware_trigger: false, t_safety_ms: 5.0, t_settle_ms: 40.0,
            t_hold_safety_ms: 15.0, blur_threshold: 100.0, auto_retrigger_on_blur: true,
            max_retrigger_count: 1, extra_settle_ms: 20.0,
        };

        // Gán lại toàn bộ 14 tham số về mặc định
        setInputValue("pref-antiblur-t-settle", d.t_settle_ms);
        setInputValue("pref-antiblur-t-hold", d.t_hold_safety_ms);
        setInputValue("pref-antiblur-t-exp", d.t_exp_ms);
        setSelectValue("pref-antiblur-trigger-mode", d.is_hardware_trigger ? "hardware" : "software");
        setInputValue("pref-antiblur-threshold", d.blur_threshold);
        setCheckboxValue("pref-antiblur-auto-retrigger", d.auto_retrigger_on_blur);
        setInputValue("pref-antiblur-max-retry", d.max_retrigger_count);
        setInputValue("pref-antiblur-extra-settle", d.extra_settle_ms);
        setInputValue("pref-antiblur-fov", d.fov_mm);
        setInputValue("pref-antiblur-sensor-px", d.sensor_px);
        setInputValue("pref-antiblur-b-max", d.b_max_px);
        setInputValue("pref-antiblur-a0", d.a0_um);
        setInputValue("pref-antiblur-fn", d.fn_hz);
        setInputValue("pref-antiblur-zeta", d.zeta);

        setTextContent("badge-t-exp-source", `(mặc định: ${d.t_exp_ms} ms)`);

        // Tự động tính toán lại bảng URD theo tham số mặc định
        await calculateAntiBlurTimers();
        setBannerStatus("success", "✔ Đã khôi phục toàn bộ tham số mặc định chuẩn công nghiệp thành công!");
    } catch (err) {
        console.error("[ANTI-BLUR] Lỗi khôi phục mặc định:", err);
        setBannerStatus("error", "Lỗi khi khôi phục tham số mặc định!");
    }
}

// Helper getter / setter functions
function getInputValue(id, fallback) {
    const el = document.getElementById(id);
    return el && el.value !== "" ? el.value : fallback;
}
function setInputValue(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) el.value = val;
}
function getSelectValue(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
}
function setSelectValue(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.value = val;
}
function getCheckboxValue(id, fallback) {
    const el = document.getElementById(id);
    return el ? el.checked : fallback;
}
function setCheckboxValue(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.checked = Boolean(val);
}
function setTextContent(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = String(text);
}

// Hook các nút chức năng trong tab Anti-Blur
const btn_antiblur_reload_features = document.getElementById("btn-antiblur-reload-features");
if (btn_antiblur_reload_features) {
    btn_antiblur_reload_features.addEventListener("click", reloadFeaturesCfg);
}

const btn_antiblur_auto_calc = document.getElementById("btn-antiblur-auto-calc");
if (btn_antiblur_auto_calc) {
    btn_antiblur_auto_calc.addEventListener("click", calculateAntiBlurTimers);
}

const btn_antiblur_reset_defaults = document.getElementById("btn-antiblur-reset-defaults");
if (btn_antiblur_reset_defaults) {
    btn_antiblur_reset_defaults.addEventListener("click", restoreAntiBlurDefaults);
}


// ==========================================
// ROBOT & MOTION CONFIG CONTROLLER
// ==========================================
function applyRobotConfigToForm(d) {
    if (!d) return;
    const conn = d.connection || {};
    const lim = d.safety_limits || {};

    // Connection
    setInputValue("pref-robot-plc-ip", conn.plc_ip ?? "192.168.1.10");
    setInputValue("pref-robot-plc-port", conn.plc_port ?? 2000);
    setInputValue("pref-robot-pc-ip", conn.pc_ip ?? "192.168.1.100");
    setInputValue("pref-robot-subnet-mask", conn.subnet_mask ?? "255.255.255.0");
    setInputValue("pref-robot-timeout-ms", conn.timeout_ms ?? 1500);

    // Safety limits
    setInputValue("pref-robot-x-min", lim.x_min ?? 100);
    setInputValue("pref-robot-x-max", lim.x_max ?? 800);
    setInputValue("pref-robot-y-min", lim.y_min ?? -500);
    setInputValue("pref-robot-y-max", lim.y_max ?? 500);
    setInputValue("pref-robot-z-min", lim.z_min ?? 50);
    setInputValue("pref-robot-z-max", lim.z_max ?? 450);
    setInputValue("pref-robot-max-reach", lim.max_reach ?? 800);
    setInputValue("pref-robot-min-deadzone", lim.min_deadzone ?? 150);
    setInputValue("pref-robot-z-safe", lim.z_safe ?? 250);
    setInputValue("pref-robot-rx-min", lim.rx_min ?? 170.0);
    setInputValue("pref-robot-rx-max", lim.rx_max ?? 190.0);
    setInputValue("pref-robot-ry-min", lim.ry_min ?? -10.0);
    setInputValue("pref-robot-ry-max", lim.ry_max ?? 10.0);
    setInputValue("pref-robot-rz-min", lim.rz_min ?? -180.0);
    setInputValue("pref-robot-rz-max", lim.rz_max ?? 180.0);
}

async function loadRobotConfig() {
    try {
        const response = await fetch("/api/robot/config");
        if (!response.ok) return;
        const res = await response.json();
        if (res.status && res.data) {
            applyRobotConfigToForm(res.data);
        }
    } catch (err) {
        console.warn("[ROBOT-CONFIG] Lỗi khi nạp cấu hình robot:", err);
    }
}

async function saveRobotConfig() {
    try {
        const payload = {
            connection: {
                protocol: "TCP_SOCKET",
                plc_ip: getInputValue("pref-robot-plc-ip", "192.168.1.10"),
                plc_port: parseInt(getInputValue("pref-robot-plc-port", "2000"), 10),
                pc_ip: getInputValue("pref-robot-pc-ip", "192.168.1.100"),
                subnet_mask: getInputValue("pref-robot-subnet-mask", "255.255.255.0"),
                timeout_ms: parseInt(getInputValue("pref-robot-timeout-ms", "1500"), 10),
            },
            safety_limits: {
                x_min: parseFloat(getInputValue("pref-robot-x-min", "100")),
                x_max: parseFloat(getInputValue("pref-robot-x-max", "800")),
                y_min: parseFloat(getInputValue("pref-robot-y-min", "-500")),
                y_max: parseFloat(getInputValue("pref-robot-y-max", "500")),
                z_min: parseFloat(getInputValue("pref-robot-z-min", "50")),
                z_max: parseFloat(getInputValue("pref-robot-z-max", "450")),
                max_reach: parseFloat(getInputValue("pref-robot-max-reach", "800")),
                min_deadzone: parseFloat(getInputValue("pref-robot-min-deadzone", "150")),
                z_safe: parseFloat(getInputValue("pref-robot-z-safe", "250")),
                rx_min: parseFloat(getInputValue("pref-robot-rx-min", "170")),
                rx_max: parseFloat(getInputValue("pref-robot-rx-max", "190")),
                ry_min: parseFloat(getInputValue("pref-robot-ry-min", "-10")),
                ry_max: parseFloat(getInputValue("pref-robot-ry-max", "10")),
                rz_min: parseFloat(getInputValue("pref-robot-rz-min", "-180")),
                rz_max: parseFloat(getInputValue("pref-robot-rz-max", "180")),
            }
        };

        const response = await fetch("/api/robot/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const res = await response.json();
        return res.status === true;
    } catch (err) {
        console.error("[ROBOT-CONFIG] Lỗi khi lưu cấu hình robot:", err);
        return false;
    }
}

// Hook nút Kiểm tra kết nối PLC
const btn_test_robot_connection = document.getElementById("btn-test-robot-connection");
const robot_test_result_box = document.getElementById("robot-test-result-box");

if (btn_test_robot_connection) {
    btn_test_robot_connection.addEventListener("click", async () => {
        const plc_ip = getInputValue("pref-robot-plc-ip", "192.168.1.10");
        const plc_port = parseInt(getInputValue("pref-robot-plc-port", "2000"), 10);
        const timeout_ms = parseInt(getInputValue("pref-robot-timeout-ms", "1500"), 10);

        btn_test_robot_connection.disabled = true;
        btn_test_robot_connection.innerHTML = "<span>⏳</span><span>Đang kết nối...</span>";
        if (robot_test_result_box) {
            robot_test_result_box.style.display = "block";
            robot_test_result_box.style.background = "rgba(59, 130, 246, 0.15)";
            robot_test_result_box.style.border = "1px solid #3b82f6";
            robot_test_result_box.style.color = "#93c5fd";
            robot_test_result_box.textContent = `Đang thử kết nối TCP tới ${plc_ip}:${plc_port}...`;
        }

        try {
            const response = await fetch("/api/robot/test_connection", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ plc_ip, plc_port, timeout_ms }),
            });
            const res = await response.json();
            if (robot_test_result_box) {
                if (res.status) {
                    robot_test_result_box.style.background = "rgba(34, 197, 94, 0.15)";
                    robot_test_result_box.style.border = "1px solid #22c55e";
                    robot_test_result_box.style.color = "#86efac";
                    robot_test_result_box.textContent = `✔ ${res.message}`;
                } else {
                    robot_test_result_box.style.background = "rgba(239, 68, 68, 0.15)";
                    robot_test_result_box.style.border = "1px solid #ef4444";
                    robot_test_result_box.style.color = "#fca5a5";
                    robot_test_result_box.textContent = `✖ ${res.error || "Không thể kết nối"}`;
                }
            }
        } catch (err) {
            if (robot_test_result_box) {
                robot_test_result_box.style.background = "rgba(239, 68, 68, 0.15)";
                robot_test_result_box.style.border = "1px solid #ef4444";
                robot_test_result_box.style.color = "#fca5a5";
                robot_test_result_box.textContent = `✖ Lỗi mạng: ${err.message}`;
            }
        } finally {
            btn_test_robot_connection.disabled = false;
            btn_test_robot_connection.innerHTML = "<span>🔌</span><span>Kiểm tra kết nối PLC</span>";
        }
    });
}
