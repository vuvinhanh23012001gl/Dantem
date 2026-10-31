import {fetchGet,fetchGetSendData} from "./utills/api.js";

const add_product = document.getElementById("add-product");
const overlay_new_product =  document.getElementById("overlay-new-product");
const overlay_accpet_delete_product = document.getElementById("overlay-delete-product");

const close_add_product = document.getElementById("close-add-product");
const close_right_panel = document.getElementById("close-right-panel");
const form_add_new_product = document.getElementById("form-add-new-product");
const previewImg = document.getElementById("previewImg");
const imageInput = document.getElementById("imageInput");
const preview_box = document.querySelector(".preview-box");
const table_product_list = document.getElementById("table-product-list");

const btn_cancel_delete = document.getElementById("btn-cancel-delete");
const btn_confirm_delete = document.getElementById("btn-confirm-delete");

let selected_delete_id_current = null; //ID khi nhan xoa tren giao dien gia tri nay se dc gan



close_add_product.addEventListener("click", function() {
    overlay_new_product.style.display = "none";
    console.log("Close add new product");
});

if (close_right_panel) {
    close_right_panel.addEventListener("click", function() {
        overlay_new_product.style.display = "none";
        console.log("Close add new product from right panel");
    });
}


add_product.addEventListener("click",function() {
    console.log("Add new product clicked");
    UpDateTable();
});

async function UpDateTable(){
    overlay_new_product.style.display = "flex";
    let get_data_product = await fetchGet("/product");
    console.log(get_data_product);
    
    // Clear only rows that are not in the header
    while (table_product_list.rows.length > 1) {
        table_product_list.deleteRow(1);
    }
    
    createDataShowTable(get_data_product);
}

function show_box_warning_accept(id,name) {
    overlay_new_product.style.display = "flex";
    overlay_accpet_delete_product.style.display = "flex";
    document.getElementById(
        "warning-title"
    ).textContent = "⚠️ Xác nhận xóa";
    document.getElementById(
        "warning-message"
    ).innerText = `Đang tải dữ liệu liên quan của sản phẩm ${id}...`;
    fetchGetSendData("/product/delete_preview", {ID_Erase: id})
        .then(result => {
            const items = result?.data?.items || [];
            const details = items.length
                ? items.map(item => `- ${item.label}`).join("\n")
                : "- Không tìm thấy dữ liệu đã lưu";
            document.getElementById("warning-message").innerText =
                `Xóa sản phẩm có ID:${id} Tên:${name}?\n\nDữ liệu sẽ xóa:\n${details}`;
        })
        .catch(() => {
            document.getElementById("warning-message").innerText =
                `Xóa sản phẩm có ID:${id} Tên:${name}?\nKhông lấy được danh sách dữ liệu.`;
        });
    //dang ki su kien xoa
}

form_add_new_product.addEventListener("submit", function(e) {
    e.preventDefault();
    console.log("Form submitted");
    let formData = new FormData(form_add_new_product);
    console.log(formData);
    let id = formData.get("id");
    // let name = formData.get("name");
    // let descripttion = formData.get("description");
    //console.log("id"+id,"name", name,"descripttion",descripttion);
    if (!isValidId(id)) {
        alert("ID không hợp lệ. Vui lòng nhập số nguyên dương.");
        return;
    }
    

    fetch(form_add_new_product.action, {
      method: "POST",
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data?.success == true) {
        UpDateTable();
        alert("Lưu thành công sản phẩm mới!");
      }   
      else{
            alert(data?.message)
      }
    })
    .catch(err => {
      console.error(err);
      alert("Lỗi kết nối server!");
    });
});


function isValidId(id) {
    return /^[0-9]+$/.test(String(id));
}

imageInput.addEventListener("change", function(e) {
    const file = this.files[0];
    if (!file){
        return;
    }
    if (!file.type.startsWith("image/")) {
        alert("Vui lòng chọn file ảnh!");
        this.value = "";
        previewImg.style.display = "none";
        preview_box.style.display = "none";
        return;
    }
    const reader = new FileReader();
       reader.onload = function (e) {
        previewImg.src = e.target.result;
        previewImg.style.display = "block";
        preview_box.style.display = "block";
    };
    reader.readAsDataURL(file);
});


btn_cancel_delete.addEventListener("click",function(){
    overlay_accpet_delete_product.style.display = "none";

});


btn_confirm_delete.addEventListener("click", async function () {
    if (selected_delete_id_current === null) return;
    try {
        let status_erase = await fetchGetSendData(
            "/product/erase_product",
            { ID_Erase: selected_delete_id_current }
        );
        if (status_erase?.success) {
            console.log(
                "Xóa thành công:",
                selected_delete_id_current
            );
            overlay_accpet_delete_product.style.display = "none";
            location.reload();
            return;
        } else if (status_erase?.partial) {
            alert(status_erase.message);
            overlay_accpet_delete_product.style.display = "none";
            location.reload();
            return;
        } else {
            console.log(
                "Xóa thất bại:",
                status_erase?.message
            );
            alert(status_erase?.message || "Xóa sản phẩm thất bại");
        }
    } catch (err) {
        console.error(err);
    }
    overlay_accpet_delete_product.style.display = "none";
    selected_delete_id_current = null;
});



function createDataShowTable(data) {
    data?.data.forEach((item, index) => {
        // console.log("index", index, "item", item);
        let row = document.createElement("tr");
        // ID
        let cellId = document.createElement("td");
        cellId.textContent = item.id; // phải là item.id chứ không phải data.id

        // Name
        let cellName = document.createElement("td");
        cellName.textContent = item.name;

        // Description
        let cellDesc = document.createElement("td");
        cellDesc.textContent = item.description || "";

        // Image
        let cellImg = document.createElement("td");
        // console.log("item",item);
        if(item.image_src){ // nếu có trường image
            let img = document.createElement("img");
            img.src = `${item.image_src}?t=${Date.now()}`; // đường dẫn ảnh chống cache
            // console.log("item.image_src;",item.image_src);
            img.alt = item.name || "Ảnh sản phẩm";
            img.style.width = "100px"; // chỉnh kích thước nhỏ vừa
            img.style.height = "auto";
            cellImg.appendChild(img);
        } else {
            cellImg.textContent = "Chưa có ảnh";
        }
        // Action buttons
        let cellAction = document.createElement("td");
        let btn  = document.createElement("button");
        btn.textContent = "Xóa sản phẩm"; // an toàn hơn innerHTML
        btn.classList.add("btn_erase");
        cellAction.appendChild(btn);
        btn.addEventListener("click",async ()=>{
            console.log("data o day",data);
            show_box_warning_accept(cellId.textContent,cellName.textContent);
            selected_delete_id_current = item.id;            
        });
        
        // Append cells to row
        row.appendChild(cellId);
        row.appendChild(cellName);
        row.appendChild(cellDesc);
        row.appendChild(cellImg);
        row.appendChild(cellAction);
        // Append row to table
        table_product_list.appendChild(row);
    });

}
