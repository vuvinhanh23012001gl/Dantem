/**
 * Quản lý sự kiện nút "Thoát" (#out-app).
 * Ngắt các luồng, giải phóng COM, Camera, đóng tab hoặc hiển thị giao diện 404 giải phóng bộ nhớ.
 */

const btn_out_app = document.getElementById("out-app");

/**
 * Hiển thị giao diện 404 và giải phóng toàn bộ DOM / sự kiện để giải phóng bộ nhớ RAM của trình duyệt.
 */
function renderShutdown404Page() {
    // Ngắt kết nối socket nếu có
    try {
        if (window.sio && typeof window.sio.disconnect === "function") {
            window.sio.disconnect();
        }
    } catch (e) {
        console.warn("[Shutdown] Lỗi ngắt socket:", e);
    }

    // Xóa toàn bộ nội dung DOM của ứng dụng để giải phóng bộ nhớ
    document.body.innerHTML = `
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background-color: #121418;
            color: #e0e0e0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            text-align: center;
            padding: 20px;
            box-sizing: border-box;
            user-select: none;
        ">
            <div style="
                font-size: 80px;
                font-weight: 800;
                color: #ff5252;
                line-height: 1;
                margin-bottom: 12px;
                text-shadow: 0 4px 16px rgba(255, 82, 82, 0.4);
            ">404</div>

            <h1 style="
                font-size: 24px;
                font-weight: 600;
                margin: 0 0 16px 0;
                color: #ffffff;
            ">ỨNG DỤNG ĐÃ ĐƯỢC TẮT VÀ GIẢI PHÓNG TOÀN BỘ</h1>

            <p style="
                font-size: 15px;
                color: #9e9e9e;
                max-width: 540px;
                line-height: 1.6;
                margin: 0 0 28px 0;
            ">
                Tất cả các luồng xử lý nền, kết nối Camera, kết nối mạng Robot/Cobot và tài nguyên bộ nhớ đã được giải phóng an toàn.<br>
                Do chính sách bảo mật, trình duyệt có thể không cho phép tự động đóng tab. Bạn có thể đóng tab này thủ công.
            </p>

            <button id="btn-force-close-tab" style="
                padding: 10px 26px;
                font-size: 14px;
                font-weight: 600;
                color: #ffffff;
                background-color: #d32f2f;
                border: 1px solid #ff5252;
                border-radius: 6px;
                cursor: pointer;
                box-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);
                transition: background-color 0.2s, transform 0.1s;
            ">
                Đóng tab ngay
            </button>
        </div>
    `;

    const btnClose = document.getElementById("btn-force-close-tab");
    btnClose?.addEventListener("click", () => {
        window.close();
        window.location.href = "about:blank";
    });
}

btn_out_app?.addEventListener("click", async () => {
    const isConfirm = confirm("Bạn có chắc chắn muốn thoát ứng dụng?\nToàn bộ kết nối Camera, mạng Robot/Cobot và các luồng tiến trình sẽ được tắt để giải phóng bộ nhớ.");
    if (!isConfirm) {
        return;
    }

    console.log("🛑 [Shutdown] Đang gửi yêu cầu dừng hệ thống tới backend...");

    try {
        // Gửi yêu cầu shutdown tới backend
        const response = await fetch("/api/system/shutdown", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });

        if (response.ok) {
            console.log("✅ [Shutdown] Backend đã tiếp nhận và giải phóng tài nguyên.");
        } else {
            console.warn("⚠️ [Shutdown] Phản hồi backend không thành công:", response.status);
        }
    } catch (error) {
        console.error("❌ [Shutdown] Lỗi khi gọi API shutdown:", error);
    }

    // Thử đóng tab
    window.close();

    // Nếu sau 250ms tab vẫn chưa đóng (do cơ chế bảo mật của trình duyệt), hiển thị giao diện 404 giải phóng RAM
    setTimeout(() => {
        renderShutdown404Page();
    }, 250);
});
