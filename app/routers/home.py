import json
from fastapi import APIRouter, Request,Body,Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.dependencies import get_services
from app.container import ServiceContainer
from app.config.path_config import PATH_FOLDER_TEMPLATES, PATH_FILE_DATA_CONFIG_IAI

router = APIRouter()
templates = Jinja2Templates(directory=str(PATH_FOLDER_TEMPLATES))

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Hiển thị màn hình chính cùng tên sản phẩm đang được chọn.

    Input: request FastAPI và service container.
    Output: HTML response có tên sản phẩm hiện tại hoặc trạng thái chưa chọn.
    Errors: không phát sinh; sản phẩm không tồn tại được hiển thị là chưa chọn.
    """
    selected_product_name = "Chưa chọn sản phẩm"
    try:
        services = request.app.state.services
        selected_product_id = services.obj_choose_product.get_choose_product().data
        if selected_product_id != -1:
            product_result = services.obj_products_service.get_product_by_id(selected_product_id)
            if product_result.ok:
                selected_product_name = product_result.data.name
    except (AttributeError, KeyError, RuntimeError):
        pass
        
    iai_default_config = {}
    try:
        with open(PATH_FILE_DATA_CONFIG_IAI, 'r', encoding='utf-8') as f:
            iai_default_config = json.load(f)
    except Exception:
        pass

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "msg": "Xin chào Ánh 👋",
            "selected_product_name": selected_product_name,
            "iai_default_config": iai_default_config,
            "iai_config": iai_default_config,
        }
    )




@router.post("/data_home")
def data_home(services: ServiceContainer = Depends(get_services),bayload:dict =  Body(...)):
    # print("----Cung cấp data cho DOM --- ")
    # status = bayload.get("status")
    choose_product_current = services.obj_choose_product.get_choose_product()
    # print("Sản phẩm đang chọn là :",choose_product_current.data)
    if choose_product_current.data == -1:
        msg = " Hiện tại chưa chọn sản phẩm. Vui lòng chọn sản phẩm trước khi chụp!"
        return {"status":False, "message": msg}
    else:
        result = services.obj_products_service.get_arr_path_img_roi_product_by_id(choose_product_current.data)
        # print("result",result.data)
        # print("status result.ok path_arr_img result.data",result.ok ,result.data)
        return {"status": result.ok ,"path_arr_img":result.data}


@router.get("/api/product_count")
def get_product_count(services: ServiceContainer = Depends(get_services)):
    """
    Lấy số lượng sản phẩm OK, NG và Tổng đã lưu trong file JSON.
    """
    return services.obj_product_count_service.get_counts()


@router.post("/api/product_count/reset")
def reset_product_count(services: ServiceContainer = Depends(get_services)):
    """
    Đặt lại số lượng sản phẩm về 0 (OK=0, NG=0, Tổng=0) khi nhấn nút 'Đặt lại'.
    """
    return services.obj_product_count_service.reset_counts()


@router.get("/api/hardware_status")
def get_hardware_status(services: ServiceContainer = Depends(get_services)):
    """
    Lấy trạng thái kết nối phần cứng thực tế cho Camera và Ethernet TCP.
    """
    is_cam = services.obj_camera.get_is_connect() if getattr(services, "obj_camera", None) else False
    is_tcp = getattr(services, "is_tcp_connected", False)
    return {
        "camera": bool(is_cam),
        "tcp": bool(is_tcp),
    }


