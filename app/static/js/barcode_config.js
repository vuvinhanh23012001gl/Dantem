// ==========================================
// BARCODE CONFIGURATION CONTROLLER
// Quản lý hiển thị và tương tác cấu hình Barcode
// ==========================================

const btnOpenBarcode = document.getElementById("btn-open-barcode-config");
const overlayBarcode = document.getElementById("overlay-barcode-config");
const btnCloseBarcode = document.getElementById("close-barcode-config");

const formAddBarcode = document.getElementById("form-add-barcode");
const btnCreateBarcode = document.getElementById("btn-create-barcode");
const barcodeStatusMsg = document.getElementById("barcode-status-msg");
const barcodeListBody = document.getElementById("barcode-list-body");

const inputOperator = document.getElementById("barcode-operator");
const inputFactory = document.getElementById("barcode-factory");
const inputLine = document.getElementById("barcode-line");
const selectRole = document.getElementById("barcode-role");
const inputCode = document.getElementById("barcode-code");

/**
 * Kiểm tra tính hợp lệ của mã Barcode:
 * - Chỉ gồm chữ và số (a-z, A-Z, 0-9)
 * - Không tiếng Việt có dấu
 * - Không khoảng trắng
 */
function validateBarcodeCode(code) {
    if (!code || typeof code !== "string") {
        return { valid: false, message: "Mã barcode không được để trống." };
    }

    if (/\s/.test(code)) {
        return { valid: false, message: "Mã barcode không được chứa khoảng trắng." };
    }

    const trimmed = code.trim();
    if (!trimmed) {
        return { valid: false, message: "Mã barcode không được để trống." };
    }

    // Regex kiểm tra chỉ chứa ký tự chữ và số ASCII
    const regex = /^[a-zA-Z0-9]+$/;
    if (!regex.test(trimmed)) {
        return {
            valid: false,
            message: "Mã barcode chỉ được chứa chữ và số, không dấu tiếng Việt và không ký tự đặc biệt."
        };
    }

    return { valid: true, message: "" };
}

/**
 * Tải danh sách tài khoản Barcode từ server và hiển thị lên bảng:
 * - Server đã sắp xếp: Nhóm Manager trước, User sau.
 * - Admin không hiển thị trong danh sách này.
 */
async function loadBarcodeAccounts() {
    if (!barcodeListBody) return;

    try {
        const response = await fetch("/barcode/accounts", {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });

        if (!response.ok) {
            throw new Error(`Lỗi tải dữ liệu: ${response.status}`);
        }

        const resData = await response.json();
        const accounts = resData.data || [];

        barcodeListBody.innerHTML = "";

        if (accounts.length === 0) {
            const emptyTr = document.createElement("tr");
            emptyTr.innerHTML = `
                <td colspan="6" style="text-align: center; color: #9ca3af; padding: 18px;">
                    Chưa có tài khoản barcode nào được tạo
                </td>
            `;
            barcodeListBody.appendChild(emptyTr);
            return;
        }

        accounts.forEach((acc) => {
            const tr = document.createElement("tr");
            const isManager = (acc.role || "").toLowerCase() === "manager";
            const roleBadgeStyle = isManager
                ? "background: #854d0e; color: #fef08a;"
                : "background: #1e3a8a; color: #bfdbfe;";

            tr.innerHTML = `
                <td>${escapeHtml(acc.operator || "")}</td>
                <td>${escapeHtml(acc.factory || "")}</td>
                <td>${escapeHtml(acc.line || "")}</td>
                <td><span style="padding: 2px 8px; border-radius: 4px; font-weight: bold; ${roleBadgeStyle}">${escapeHtml(acc.role || "User")}</span></td>
                <td><code style="background: #1e293b; padding: 2px 6px; border-radius: 4px; color: #38bdf8;">${escapeHtml(acc.barcode || "")}</code></td>
                <td><button type="button" class="btn_erase btn-delete-barcode" data-barcode="${escapeHtml(acc.barcode || "")}">🗑️ Xóa</button></td>
            `;

            // Bắt sự kiện xóa tài khoản
            const deleteBtn = tr.querySelector(".btn-delete-barcode");
            if (deleteBtn) {
                deleteBtn.addEventListener("click", () => {
                    handleDeleteBarcode(acc.barcode, acc.operator);
                });
            }

            barcodeListBody.appendChild(tr);
        });
    } catch (err) {
        console.error("Lỗi khi tải danh sách Barcode:", err);
        barcodeListBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; color: #f87171; padding: 18px;">
                    ⚠️ Không thể tải danh sách tài khoản: ${escapeHtml(err.message)}
                </td>
            </tr>
        `;
    }
}

/**
 * Xử lý xóa tài khoản barcode
 */
async function handleDeleteBarcode(barcode, operator) {
    if (!barcode) return;

    const confirmMsg = `Bạn có chắc chắn muốn xóa tài khoản barcode "${barcode}" (${operator || ""})?`;
    if (!confirm(confirmMsg)) {
        return;
    }

    try {
        const response = await fetch(`/barcode/account/${encodeURIComponent(barcode)}`, {
            method: "DELETE"
        });

        const result = await response.json();

        if (response.ok) {
            if (barcodeStatusMsg) {
                barcodeStatusMsg.innerText = `✅ Đã xóa tài khoản barcode "${barcode}"`;
                barcodeStatusMsg.style.color = "#22c55e";
            }
            await loadBarcodeAccounts();
        } else {
            if (barcodeStatusMsg) {
                barcodeStatusMsg.innerText = `⚠️ ${result.detail || result.message || "Xóa thất bại"}`;
                barcodeStatusMsg.style.color = "#f87171";
            }
        }
    } catch (err) {
        console.error("Lỗi khi xóa barcode:", err);
        if (barcodeStatusMsg) {
            barcodeStatusMsg.innerText = `⚠️ Lỗi kết nối khi xóa: ${err.message}`;
            barcodeStatusMsg.style.color = "#f87171";
        }
    }
}

// Mở panel Cấu hình Barcode
if (btnOpenBarcode && overlayBarcode) {
    btnOpenBarcode.addEventListener("click", () => {
        console.log("Mở bảng Cấu hình Barcode");
        overlayBarcode.style.display = "flex";
        if (barcodeStatusMsg) {
            barcodeStatusMsg.innerText = "";
        }
        if (inputOperator) {
            inputOperator.focus();
        }
        // Tải danh sách barcode từ server
        loadBarcodeAccounts();
    });
}

// Đóng panel khi bấm nút X
if (btnCloseBarcode && overlayBarcode) {
    btnCloseBarcode.addEventListener("click", () => {
        console.log("Đóng bảng Cấu hình Barcode");
        overlayBarcode.style.display = "none";
    });
}

// Đóng panel khi click ra ngoài vùng backdrop
if (overlayBarcode) {
    overlayBarcode.addEventListener("click", (event) => {
        if (event.target === overlayBarcode) {
            overlayBarcode.style.display = "none";
        }
    });
}

// Kiểm tra realtime khi gõ mã barcode
if (inputCode) {
    inputCode.addEventListener("input", () => {
        const val = inputCode.value;
        if (!val) {
            inputCode.style.borderColor = "#253046";
            return;
        }

        const check = validateBarcodeCode(val);
        if (!check.valid) {
            inputCode.style.borderColor = "#f87171";
            if (barcodeStatusMsg) {
                barcodeStatusMsg.innerText = `⚠️ ${check.message}`;
                barcodeStatusMsg.style.color = "#f87171";
            }
        } else {
            inputCode.style.borderColor = "#22c55e";
            if (barcodeStatusMsg && barcodeStatusMsg.innerText.startsWith("⚠️")) {
                barcodeStatusMsg.innerText = "";
            }
        }
    });
}

// Xử lý tạo tài khoản Barcode trên giao diện và lưu vào file
if (formAddBarcode) {
    formAddBarcode.addEventListener("submit", async (event) => {
        event.preventDefault();

        const operator = inputOperator ? inputOperator.value.trim() : "";
        const factory = inputFactory ? inputFactory.value.trim() : "";
        const line = inputLine ? inputLine.value.trim() : "";
        const role = selectRole ? selectRole.value : "Manager";
        const code = inputCode ? inputCode.value.trim() : "";

        // Kiểm tra điền đầy đủ thông tin
        if (!operator || !factory || !line || !code) {
            if (barcodeStatusMsg) {
                barcodeStatusMsg.innerText = "⚠️ Vui lòng điền đầy đủ tất cả các trường.";
                barcodeStatusMsg.style.color = "#f87171";
            }
            return;
        }

        // Kiểm tra hợp lệ mã barcode
        const check = validateBarcodeCode(code);
        if (!check.valid) {
            if (barcodeStatusMsg) {
                barcodeStatusMsg.innerText = `⚠️ ${check.message}`;
                barcodeStatusMsg.style.color = "#f87171";
            }
            if (inputCode) {
                inputCode.focus();
                inputCode.style.borderColor = "#f87171";
            }
            return;
        }

        // Disable nút tạo để tránh spam click
        if (btnCreateBarcode) {
            btnCreateBarcode.disabled = true;
            btnCreateBarcode.innerText = "Đang tạo...";
        }

        try {
            const response = await fetch("/barcode/account", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    operator: operator,
                    factory: factory,
                    line: line,
                    role: role,
                    barcode: code
                })
            });

            const result = await response.json();

            if (response.ok && result.status) {
                if (barcodeStatusMsg) {
                    barcodeStatusMsg.innerText = `✅ ${result.message || "Tạo tài khoản thành công!"}`;
                    barcodeStatusMsg.style.color = "#22c55e";
                }

                // Cập nhật lại giao diện bảng danh sách
                await loadBarcodeAccounts();

                // Xóa trắng input mã barcode và tên để nhập tiếp
                if (inputOperator) inputOperator.value = "";
                if (inputCode) {
                    inputCode.value = "";
                    inputCode.style.borderColor = "#253046";
                }
                if (inputOperator) inputOperator.focus();
            } else {
                if (barcodeStatusMsg) {
                    barcodeStatusMsg.innerText = `⚠️ ${result.detail || result.message || "Tạo tài khoản thất bại"}`;
                    barcodeStatusMsg.style.color = "#f87171";
                }
            }
        } catch (err) {
            console.error("Lỗi khi gửi yêu cầu tạo tài khoản:", err);
            if (barcodeStatusMsg) {
                barcodeStatusMsg.innerText = `⚠️ Lỗi kết nối: ${err.message}`;
                barcodeStatusMsg.style.color = "#f87171";
            }
        } finally {
            if (btnCreateBarcode) {
                btnCreateBarcode.disabled = false;
                btnCreateBarcode.innerText = "Tạo tài khoản";
            }
        }
    });
}

// Hàm chống XSS cho dữ liệu hiển thị trên bảng
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
