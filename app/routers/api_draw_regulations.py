from fastapi import APIRouter,Body,Depends
from app.container import ServiceContainer
from app.core.dependencies import get_services
from app.config import TypeSend

router = APIRouter(
    prefix="/draw-regulations",
    tags=["Draw-Regulations"]
)


@router.post("/")
def draw_regulations(services: ServiceContainer = Depends(get_services),bayload:dict =  Body(...)):
    print("---- Vào draw regulation --- ")
    status = bayload.get("status")
    print("Satus regulations: ",status)
    result_choose_product_current = services.obj_choose_product.get_choose_product()
    choose_product_current =  result_choose_product_current.data
    print("Sản phẩm đang chọn là :",choose_product_current)
    if choose_product_current == -1:
        msg = " Hiện tại chưa chọn sản phẩm. Vui lòng chọn sản phẩm trước khi chụp!"
        services.queue_log_send_client.put({"type": TypeSend.type_capture, "message": msg})  
        print("--------------Hết UI capture----------------")
        return {"status": "error", "message": msg}
    else:
        status,arr_path_img = services.obj_products_service.get_arr_path_img_roi_product_by_id(choose_product_current)
        arr_run_point = services.obj_products_service.get_arr_data_run_point_product_by_id(choose_product_current)
        infor = services.obj_products_service.get_infor_product(choose_product_current)
        status,data_regualtion,_,_ = services.obj_products_service.get_data_regulation_by_product_id(choose_product_current)
        print("data_regualtion",data_regualtion)
        print("arr_path_img",arr_path_img,"\n arr_run_point",arr_run_point,"\ninfor",infor)
        return {"status": "ok","path_arr_img":arr_path_img,"data_regualtion":data_regualtion}


@router.post("/accept_data")
def accept_data(services: ServiceContainer = Depends(get_services),bayload:dict =  Body(...)):
    print("----Nhấn Accept dữ liệu mới--- ")
    data_regulation = bayload.get("data_regulation")
    print("data_regulation",data_regulation)
    status,message = services.obj_logic.validate_full_regulation(data_regulation)
    print("data nhan duoc:",status,message)
    if status:
        choose_product_current = services.obj_choose_product.get_choose_product_pick()
        status_add_set,message =  services.obj_products_service.set_data_regulation_by_product_id(choose_product_current,data_regulation)
        if status_add_set:
            return {"status":True,"message":"ok"}
        else:
           return {"status":False,"message":message}
    else:
        return {"status":False,"message":message}
    
   

@router.get("/exit")
async def exit():
    return {
        "status": "200ok",
        "redirect_url": "/"
}



