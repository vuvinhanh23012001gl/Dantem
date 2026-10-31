from fastapi import APIRouter, Form, File, UploadFile,Query,Depends
from app.core.dependencies import get_services
from app.container import ServiceContainer
from app.model import Product
from app.utils import Tool_OpenCv2
router = APIRouter(
    prefix="/product",
    tags=["Product"]
)

@router.get("/get_inf_product")
def get_product(services: ServiceContainer = Depends(get_services)):
    data = services.obj_products_service.get_to_dict_arr_path_src()
    select_product = services.obj_choose_product.get_choose_product()
    print("get_inf_product",data)
    return { "success": True, "data": data.data,"current_option":select_product.data}

@router.get("/select_product_new")
def select_product_new(services: ServiceContainer = Depends(get_services),ID_Choose:int = Query(...,description="San pham chon")):
    print(ID_Choose)
    services.obj_products_service.reload_products()
    result = services.obj_choose_product.set_choose_product(ID_Choose)
    if result.ok:
        services.notify_config_changed("select_product_new")
        return {"success": True}
    return {"success": False}
    
@router.get("/")
def list_product(services: ServiceContainer = Depends(get_services)):
    data = services.obj_products_service.get_to_dict_arr_path_src()
    print("data.data",data.data)
    return { "success": True, "data": data.data}



@router.get("/erase_product")
def erase_product(
    services: ServiceContainer = Depends(get_services),
    ID_Erase: int = Query(..., description="Xoa San Pham")
):
    if (
        services.runtime_state.is_judgment_running()
        or services.get_mode().name in {"MODE_PREPOCESS", "MODE_TRANSFORM", "MODE_EXPORT"}
    ):
        return {
            "success": False,
            "message": "Không thể xóa sản phẩm khi pipeline đang chạy hoặc đang phán định.",
        }
    report = services.obj_products_service.delete_product_data(ID_Erase)
    try:
        services.obj_point_service.delete_product(ID_Erase)
    except Exception as error:
        print(f"[Cảnh báo] Lỗi dọn RAM PointService khi xóa sản phẩm: {error}")

    try:
        services.obj_law_regulation_service.delete_product_data(str(ID_Erase))
    except Exception as error:
        print(f"[Cảnh báo] Lỗi dọn RAM LawRegulationService khi xóa sản phẩm: {error}")

    if services.obj_choose_product.is_choose_product(ID_Erase):
        services.obj_choose_product.reset_choose_product()
    services.notify_config_changed("erase_product")
    if report["failed"]:
        message = "Đã xóa một phần dữ liệu; còn sót: " + "; ".join(
            f"{item['label']}: {item['error']}" for item in report["failed"]
        )
    else:
        message = "Đã xóa toàn bộ dữ liệu sản phẩm."
    return {
        "success": not report["failed"],
        "partial": bool(report["deleted"]) and bool(report["failed"]),
        "message": message,
        "report": report,
    }


@router.get("/delete_preview")
def delete_preview(
    services: ServiceContainer = Depends(get_services),
    ID_Erase: int = Query(..., description="Sản phẩm cần xem dữ liệu sẽ xóa"),
):
    """Liệt kê dữ liệu product sẽ bị xóa trước khi xác nhận."""
    return {
        "success": True,
        "data": services.obj_products_service.get_delete_preview(ID_Erase),
    }


   
@router.post("/add")
async def add_product(
    services: ServiceContainer = Depends(
        get_services
    ),
    id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    limit_x_max: int = Form(0),
    limit_y_max: int = Form(0),
    limit_z_max: int = Form(0),
    home_x: float = Form(0.0),
    home_y: float = Form(0.0),
    home_z: float = Form(0.0),
    images: UploadFile | None = File(None)
):
    if id <= 0:
        return {"success": False, "message": "ID sản phẩm phải là số nguyên dương."}
    

    img_np = None
    if images:
        contents = await images.read()
        img_np = (
            Tool_OpenCv2.bytes_to_ndarray(
                contents
            )
        )
    product = Product(
        id=id,
        name=name,
        description=description,
        limit_x_max=limit_x_max,
        limit_y_max=limit_y_max,
        limit_z_max=limit_z_max,
        home_x=home_x,
        home_y=home_y,
        home_z=home_z
    )
    result = (
        services.obj_products_service
        .add_product(
            product=product,
            img=img_np
        )
    )

    return{ "success": result.ok , "message": result.message()}