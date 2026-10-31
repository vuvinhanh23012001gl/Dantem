const closingPanels = new WeakMap();

function cancelClose(panel) {
    closingPanels.get(panel)?.(false);
    panel.classList.remove("region-leave");
}

export function setRegionPanel(panel, selection, accepted = false) {
    if (!panel) return;
    cancelClose(panel);
    const opening = selection !== null && !panel.classList.contains("active");
    panel.classList.toggle("active", selection !== null);
    if (opening) {
        panel.classList.remove("region-enter");
        void panel.offsetWidth;
        panel.classList.add("region-enter");
    }
    if (selection === null) panel.classList.remove("region-enter");
    const content = panel.querySelector(".cof-and-inf-tool-content");
    if (content) {
        content.dataset.selection = selection === null ? "" : String(selection);
        content.hidden = selection === null;
    }
    panel.querySelectorAll(".controler-tool button").forEach(button => {
        if (!button.id.startsWith("btn-exit-")) button.disabled = !accepted;
    });
}

export function hideRegionEditor(panel) {
    panel.querySelectorAll(".region-editor").forEach(editor => { editor.hidden = true; });
}

export function closeRegionPanel(panel) {
    cancelClose(panel);
    if (!panel.classList.contains("active")) return Promise.resolve(true);
    panel.classList.remove("region-enter");
    panel.classList.add("region-leave");
    return new Promise(resolve => {
        const finish = completed => {
            clearTimeout(timer);
            panel.removeEventListener("animationend", onEnd);
            closingPanels.delete(panel);
            panel.classList.remove("region-leave");
            if (completed) setRegionPanel(panel, null);
            resolve(completed);
        };
        const onEnd = event => {
            if (event.target === panel && event.animationName === "slideLeftToRight") finish(true);
        };
        const timer = setTimeout(() => finish(true), 300);
        closingPanels.set(panel, finish);
        panel.addEventListener("animationend", onEnd);
    });
}

function setModelBadge(badge, completed) {
    badge.dataset.state = completed ? "ready" : "missing";
    badge.textContent = completed ? "Đã có model" : "Chưa tạo";
    badge.classList.toggle("ready", completed);
    badge.classList.remove("error");
}

export function updateRegionModelStatus(panel, regionId, completed) {
    panel.querySelectorAll(".foreign-object-region").forEach(row => {
        if (row.dataset.roiId === String(regionId)) {
            setModelBadge(row.querySelector(".foreign-object-model-badge"), completed);
        }
    });
}

export function createRegionList(regions, activeId, {select, remove, statusUrl, isCurrent, onError}) {
    const list = document.createElement("div");
    list.className = "foreign-object-regions";
    list.setAttribute("aria-label", "Danh sách vùng kiểm tra");
    for (const region of regions) {
        const row = document.createElement("div");
        row.className = `foreign-object-region${region.id === activeId ? " active" : ""}`;
        row.dataset.roiId = String(region.id);
        const button = document.createElement("button");
        button.type = "button";
        button.className = "region-select";
        button.textContent = region.name;
        button.title = region.name;
        button.setAttribute("aria-pressed", String(region.id === activeId));
        button.addEventListener("click", () => select(region));
        const badge = document.createElement("span");
        badge.className = "foreign-object-model-badge";
        badge.textContent = "Đang kiểm tra";
        badge.dataset.state = "checking";
        fetch(statusUrl(region)).then(async response => {
            const payload = await response.json();
            if (!response.ok || !payload.ok) throw new Error(payload.message || "Không đọc được trạng thái model.");
            if (!list.isConnected || !isCurrent() || badge.dataset.state !== "checking") return;
            setModelBadge(badge, Boolean(payload.data.completed));
        }).catch(error => {
            if (!list.isConnected || !isCurrent() || badge.dataset.state !== "checking") return;
            badge.textContent = "Lỗi trạng thái";
            badge.classList.add("error");
            onError(region, error);
        });
        const erase = document.createElement("button");
        erase.type = "button";
        erase.className = "region-remove";
        erase.textContent = "\u00d7";
        erase.title = `Gỡ vùng ${region.name}; model chỉ được dọn khi Lưu master`;
        erase.setAttribute("aria-label", `Gỡ vùng ${region.name}`);
        erase.addEventListener("click", () => remove(region));
        row.append(button, badge, erase);
        list.appendChild(row);
    }
    return list;
}
