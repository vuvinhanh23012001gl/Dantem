/**
 * Quản lý sự kiện tải và hiển thị file PDF hướng dẫn sử dụng phần mềm dành cho kỹ sư EE.
 */
const btn_instruct_staff_ee = document.getElementById("btn_instruct_staff_ee");

btn_instruct_staff_ee?.addEventListener("click", () => {
    console.log("[Tài liệu] Mở tài liệu Hướng dẫn sử dụng EE...");
    window.open("/api/instruct/staff_ee.pdf", "_blank");
});
