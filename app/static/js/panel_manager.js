export function openOptionPanel(panel) {
    // Mở một panel cấp cao và đóng panel đang mở trong vùng show-option.
    document.querySelectorAll(".show-option > .paner").forEach((item) => {
        item.classList.remove("active");
    });
    panel.classList.add("active");
    if (["paner-capture-product", "panner-adjust-master", "paner-camera-config"].includes(panel.id)) {
        window.dispatchEvent(new CustomEvent("image-view-mode"));
    }
}