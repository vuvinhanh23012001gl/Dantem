/**
 * Quản lý sự kiện tải và hiển thị file PDF hướng dẫn sử dụng phần mềm cho người thao tác.
 */
const btn_instruct_worker = document.getElementById("btn_instruct_worker");

btn_instruct_worker?.addEventListener("click", () => {
    console.log("[Tài liệu] Mở tài liệu Hướng dẫn sử dụng phần mềm cho người thao tác...");
    window.open("/api/instruct/worker.pdf", "_blank");
});
