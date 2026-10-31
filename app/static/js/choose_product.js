import {fetchGet,fetchGetSendData} from "./utills/api.js";

const choose_product = document.getElementById("choose-product"); 
const overlay_choose_product = document.getElementById("overlay-choose-product");
const close_choose_product = document.getElementById("close-choose-product");
const container = document.getElementById("container-chose-product");

choose_product.addEventListener("click",async function(){

    console.log("Bạn vừa nhấn chọn sản phẩm");
    overlay_choose_product.style.display = "flex";
    container.innerHTML = "";
    let data =  await fetchGet("/product/get_inf_product");
    let arr_product = data?.data;
    let select_product = data?.current_option;
    console.log("arr",arr_product,"select",select_product);

    if (!Array.isArray(arr_product)){
        alert("Lỗi định dạng gửi dữ liệu lên");
        return;
    } 
    else if (arr_product.length === 0){
        // alert("Hiện tại chưa có sản phẩm nào");
        return;
    }
        for (let key of arr_product) {
          const new_div = document.createElement("div");
          new_div.className = "div-product";
          const img = document.createElement("img");
          img.src = key?.image_src ? `${key.image_src}?t=${Date.now()}` : "";
          img.alt = `Ảnh sản phẩm ${key?.image_src}`;
          img.style.width = "100%";
          img.style.height = "250px";
          img.style.objectFit = "cover";
          img.style.borderRadius = "8px";
        
          const product_name = document.createElement("h3");
          product_name.innerText = `${key?.id}: ${key?.name}`;

          const description = document.createElement("h4");
          description.innerText = key?.description || "Không có mô tả";

          new_div.appendChild(img);
          new_div.appendChild(product_name);
          new_div.appendChild(description);
          container.appendChild(new_div);
          // console.log("select_product",select_product,"key?.id",key?.id);
          if (select_product == key?.id){ new_div.classList.add("active");console.log("Tìm thấy sản phẩm đã chọn");}
          new_div.addEventListener("click",async()=>{
              let data = await fetchGetSendData("/product/select_product_new",{"ID_Choose":key?.id});
              if (data?.success == true){
                   container.querySelectorAll("*").forEach(el => {
                        el.classList.remove("active");
                    });
                    new_div.classList.add("active"); 
                    overlay_choose_product.style.display = "None";
                    location.reload();
              }
              else{
                    console.log("Lỗi chọn sản phẩm");
              }
          });

        }









});
close_choose_product.addEventListener("click",function(){
    overlay_choose_product.style.display = "None";
});