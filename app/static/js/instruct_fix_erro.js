/**
 * Quản lý sự kiện tải và hiển thị file PDF hướng dẫn đối ứng và khắc phục lỗi phần mềm/hệ thống.
 */
const btn_instruct_fix_erro = document.getElementById("btn_instruct_fix_erro");

btn_instruct_fix_erro?.addEventListener("click", () => {
    console.log("[Tài liệu] Mở tài liệu Hướng dẫn đối ứng lỗi...");
    window.open("/api/instruct/fix_erro.pdf", "_blank");
});
