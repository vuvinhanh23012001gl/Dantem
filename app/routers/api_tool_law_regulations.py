from fastapi import APIRouter, Body, Depends
from app.container import ServiceContainer
from app.core.dependencies import get_services
from app.core import Result, ErrorCode
from app.config import WIDTH_IMG_CAMERA_CAPTURE, HEIGHT_IMG_CAMERA_CAPTURE
from app.validate import ValidateToolLawRegulation
import cv2
import numpy as np

router = APIRouter(
    prefix="/law_regulation",
    tags=["law_regulation"]
)

#------- main ---------------------

@router.get("/")
def header_function(services: ServiceContainer = Depends(get_services)):
    print("🔧 [Master] Người dùng đã nhấn 'Điều chỉnh master'.")
    print("🔎 [Master] Đang xác định sản phẩm hiện tại...")
    choose_product_current = services.obj_choose_product.get_choose_product()
    print("📦 [Master] Sản phẩm đang chọn:", choose_product_current)
    if not choose_product_current.ok:
        print("❌ [Master] Không xác định được sản phẩm đang chọn.")
        return Result.Fail(choose_product_current.error).to_dict()
    product_id = choose_product_current.data
    product_result = services.obj_products_service.get_product_by_id(product_id)
    if not product_result.ok:
        print(f"❌ [Master] Không lấy được thông tin sản phẩm: {product_id}")
        return Result.Fail(product_result.error).to_dict()
    product = product_result.data
    print(f"✅ [Master] Đã lấy thông tin sản phẩm: {product_id}")

    print("📸 [Master] Đang lấy danh sách ảnh master và điểm kiểm tra...")
    points_result = services.obj_point_service.get_points_by_product_id(product_id)
    if points_result.ok:
        print(f"✅ [Master] Đã lấy dữ liệu điểm/ảnh master cho sản phẩm: {product_id}")
    else:
        print("⚠️ [Master] Không lấy được đầy đủ dữ liệu điểm/ảnh master.")

    print("📋 [Master] Đang lấy cây luật phán định...")
    tree = services.obj_law_regulation_service.get_product_data(str(product_id))
    point_tree = services.obj_point_service.get_point_tree_by_product_id(product_id)
    if not tree.ok or tree.data is None:
        print("⚠️ [Master] Chưa có cây luật riêng, chuyển sang lấy cây điểm mặc định...")
        tree = point_tree
    elif point_tree.ok and point_tree.data:
        # Tự động đồng bộ các frame và point từ points.json vào cây luật master
        product_key = str(product_id)
        if product_key in point_tree.data and product_key in tree.data:
            base_frames = point_tree.data[product_key]
            current_frames = tree.data[product_key]
            for f_id, points_map in base_frames.items():
                if f_id not in current_frames:
                    current_frames[f_id] = {}
                for p_id in points_map.keys():
                    if p_id not in current_frames[f_id]:
                        current_frames[f_id][p_id] = {}
    if tree.ok and tree.data is not None:
        if services.obj_law_regulation_service.repo.clean_undefined_keys(tree.data):
            services.obj_law_regulation_service.repo.clean_undefined_keys(services.obj_law_regulation_service.repo.data)
            services.obj_law_regulation_service.repo.save()
        print("✅ [Master] Đã lấy cây luật phán định của master.")
    else:
        print("⚠️ [Master] Không có cây luật phán định để nạp.")
    print("✅ [Master] Hoàn tất chuẩn bị dữ liệu điều chỉnh master.")
    return Result.Ok({
        "wid_img": WIDTH_IMG_CAMERA_CAPTURE,
        "hei_img": HEIGHT_IMG_CAMERA_CAPTURE,
        "product": product,
        "data_point": points_result.data if points_result.ok else [],
        "data_master": None,
        "tree": tree.data if tree.ok else None,
    }).to_dict()

@router.get("/exit")
async def exit():
    return {
        "status": "ok",
        "redirect_url": "/"
}

@router.post("/save")
def save(data:dict= Body(),services: ServiceContainer = Depends(get_services)):
    print("---API save---")
    print("Dữ liệu nhận save",data)
    logs = ["Bắt đầu lưu dữ liệu master."]

    def response_with_logs(result):
        """Bổ sung nhật ký các bước lưu vào response API."""
        response = result.to_dict()
        response["logs"] = logs
        return response

    if not data:
        logs.append("Dữ liệu master rỗng.")
        return response_with_logs(Result.Fail(ErrorCode.DATA_INVALID))
    canvas_width = data.get("WidthCanvas", 1024)
    canvas_height = data.get("HeightCanvas", 768)
    payload = data.get("data", data)
    try:
        canvas_width = int(canvas_width)
        canvas_height = int(canvas_height)
    except (TypeError, ValueError):
        logs.append("Kích thước canvas không hợp lệ.")
        return response_with_logs(Result.Fail(ErrorCode.INVALID_INPUT))
    logs.append(f"Đã nhận canvas {canvas_width} x {canvas_height}.")
    choose_product_current = services.obj_choose_product.get_choose_product()
    print("Sản phẩm đang chọn",choose_product_current)
    if not choose_product_current.ok:
        logs.append("Không xác định được sản phẩm đang chọn.")
        return response_with_logs(Result.Fail(choose_product_current.error))
    product_id = choose_product_current.data
    logs.append(f"Đang xử lý master của sản phẩm {product_id}.")
    tree = services.obj_point_service.get_point_tree_by_product_id(product_id)
    if not tree.ok or tree.data is None:
        logs.append("Không tìm thấy cấu trúc point/frame của sản phẩm.")
        return response_with_logs(Result.Fail(ErrorCode.FRAME_NOT_FOUND))
    logs.append("Đã kiểm tra cấu trúc point/frame.")

    # Làm sạch payload: loại bỏ các frame_id hoặc point_id rác (như "-1") không thuộc cây định danh hợp lệ của sản phẩm
    product_key = str(product_id)
    if isinstance(payload, dict) and product_key in payload and isinstance(payload[product_key], dict) and product_key in tree.data:
        valid_frames = tree.data[product_key]
        cleaned_product_frames = {}
        for f_id, f_data in payload[product_key].items():
            str_f_id = str(f_id)
            if str_f_id in valid_frames and isinstance(f_data, dict):
                cleaned_points = {}
                for p_id, p_data in f_data.items():
                    str_p_id = str(p_id)
                    if str_p_id in valid_frames[str_f_id]:
                        cleaned_points[str_p_id] = p_data
                    else:
                        print(f"⚠️ [Master][Save] Bỏ qua point_id không hợp lệ: {p_id}")
                cleaned_product_frames[str_f_id] = cleaned_points
            else:
                print(f"⚠️ [Master][Save] Bỏ qua frame_id không hợp lệ: {f_id}")
        payload[product_key] = cleaned_product_frames

    services.obj_law_regulation_service.repo.clean_undefined_keys(payload)

    converted = services.obj_law_regulation_service.convert_canvas_coordinates(
        payload,
        product_id,
        services.obj_point_service,
        canvas_width,
        canvas_height,
    )
    if not converted.ok:
        logs.append("Quy đổi tọa độ master thất bại.")
        return response_with_logs(converted)
    logs.append("Đã chuyển tọa độ canvas sang pixel ảnh master.")
    result_save = services.obj_law_regulation_service.save_data(converted.data,tree.data)
    if result_save.ok:
        services.notify_config_changed("law_regulation_save")
        logs.append("Lưu dữ liệu master thành công.")
    else:
        logs.append(f"Lưu dữ liệu master thất bại: {result_save.message()}.")
    return response_with_logs(result_save)

@router.post("/delete_product")
def delete_product(payload: dict = Body(...), services: ServiceContainer = Depends(get_services)):
    print("---API delete product---")
    product_id = payload.get("product_id")
    if product_id is not None:
        result = services.obj_law_regulation_service.delete_product_data(str(product_id))
        if result.ok or (isinstance(result.data, dict) and result.data.get("law_deleted")):
            services.notify_config_changed("law_regulation_delete_product")
        return result.to_dict()
    return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.post("/anomaly_point/create_model")
async def create_anomaly_point_model(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Nhận ROI Điểm bất thường (kèm roi_id) và khởi động train PatchCore nền."""
    try:
        product_id = int(data["product_id"])
        frame_id = int(data.get("face_id", data.get("frame_id")))
        item_id = int(data.get("item_id", data.get("items_id")))
        roi_id = int(data.get("roi_id", 0))
        image_count = int(data.get("image_count", 16))
        crop_roi = data["crop_roi"]
        width_canvas = int(data.get("width_canvas", 0)) or None
    except (KeyError, TypeError, ValueError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()
    try:
        return services.obj_anomaly_point_patch_core_service.create_model(
            product_id, frame_id, item_id, crop_roi, image_count, width_canvas, roi_id=roi_id
        )
    except ValueError as error:
        if "đang chạy" in str(error) or "bận" in str(error):
            return Result.Fail(ErrorCode.PATCHCORE_BUSY).to_dict()
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.post("/anomaly_point/run_model")
async def run_anomaly_point_model(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Chạy inference PatchCore cho một khung roi_id trên item Điểm bất thường."""
    try:
        product_id = int(data["product_id"])
        frame_id = int(data.get("face_id", data.get("frame_id")))
        item_id = int(data.get("item_id", data.get("items_id")))
        roi_id = int(data.get("roi_id", 0))
        crop_roi = data["crop_roi"]
        width_canvas = int(data.get("width_canvas", 0)) or None
        return services.obj_anomaly_point_patch_core_service.run_model(
            product_id, frame_id, item_id, crop_roi, width_canvas, roi_id=roi_id
        )
    except (KeyError, TypeError, ValueError) as error:
        if "đang chạy" in str(error) or "bận" in str(error):
            return Result.Fail(ErrorCode.PATCHCORE_BUSY).to_dict()
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.get("/anomaly_point/train_status")
async def anomaly_point_train_status(
    product_id: int,
    frame_id: int | None = None,
    face_id: int | None = None,
    item_id: int = 0,
    roi_id: int = 0,
    services: ServiceContainer = Depends(get_services),
):
    """Lấy trạng thái phiên train PatchCore Điểm bất thường cho khung roi_id."""
    try:
        return services.obj_anomaly_point_patch_core_service.training_status(
            int(product_id),
            int(face_id if face_id is not None else (frame_id or 0)),
            int(item_id),
            roi_id=int(roi_id),
        )
    except (TypeError, ValueError, AttributeError, OSError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.get("/anomaly_point/runtime_images")
async def anomaly_point_runtime_images(
    product_id: int,
    frame_id: int | None = None,
    face_id: int | None = None,
    item_id: int = 0,
    roi_id: int = 0,
    services: ServiceContainer = Depends(get_services),
):
    """Lấy ảnh runtime/good của khung roi_id Điểm bất thường mới nhất."""
    return services.obj_anomaly_point_patch_core_service.get_runtime_images(
        product_id,
        (face_id if face_id is not None else (frame_id or 0)),
        item_id,
        roi_id=int(roi_id),
    )


@router.delete("/anomaly_point/runtime_image")
async def delete_anomaly_point_runtime_image(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Xóa một ảnh runtime/good của khung roi_id Điểm bất thường."""
    try:
        return services.obj_anomaly_point_patch_core_service.delete_runtime_image(
            int(data["product_id"]),
            int(data.get("face_id", data.get("frame_id"))),
            int(data.get("item_id", data.get("items_id"))),
            str(data["image_name"]),
            roi_id=int(data.get("roi_id", 0)),
        )
    except (KeyError, TypeError, ValueError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.delete("/anomaly_point/model")
async def delete_anomaly_point_model(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Xóa session model PatchCore và record tương ứng của khung roi_id Điểm bất thường."""
    try:
        return services.obj_anomaly_point_patch_core_service.delete_model(
            int(data["product_id"]),
            int(data.get("face_id", data.get("frame_id"))),
            int(data.get("item_id", data.get("items_id"))),
            roi_id=int(data.get("roi_id", 0)),
        )
    except (KeyError, TypeError, ValueError, OSError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.post("/foreign_object/create_model")
async def create_foreign_object_model(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Nhận ROI Dị vật và khởi động train PatchCore nền.

    Args:
        data: Product, frame, item, roi_id (vùng ROI), crop ROI, số lượng ảnh và canvas width.
        services: Container cung cấp service PatchCore Dị vật.

    Returns:
        dict: Trạng thái khởi động train hoặc lỗi dữ liệu đầu vào.

    Raises:
        Không phát sinh lỗi ra ngoài; lỗi được đóng gói bằng Result.
    """
    try:
        return services.obj_foreign_object_patch_core_service.create_model(
            int(data["product_id"]),
            int(data.get("face_id", data.get("frame_id"))),
            int(data.get("item_id", data.get("items_id"))),
            data["crop_roi"],
            int(data.get("image_count", 16)),
            int(data.get("width_canvas", 0)) or None,
            roi_id=int(data.get("roi_id", 0)),
        )
    except (KeyError, TypeError, ValueError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.get("/foreign_object/train_status")
async def foreign_object_train_status(
    product_id: int,
    frame_id: int | None = None,
    face_id: int | None = None,
    item_id: int = 0,
    roi_id: int = 0,
    services: ServiceContainer = Depends(get_services),
):
    """Lấy trạng thái train PatchCore Dị vật của một vùng ROI trên item hiện tại.

    Args:
        product_id: Mã product.
        frame_id: Mã frame.
        item_id: Mã item.
        roi_id: Mã vùng ROI trên item.
        services: Container cung cấp service PatchCore Dị vật.

    Returns:
        dict: Trạng thái worker và model đã tạo.

    Raises:
        Không phát sinh lỗi ra ngoài; lỗi được đóng gói bằng Result.
    """
    try:
        return services.obj_foreign_object_patch_core_service.training_status(
            product_id,
            face_id if face_id is not None else (frame_id or 0),
            item_id,
            roi_id=roi_id,
        )
    except (TypeError, ValueError, AttributeError, OSError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.get("/foreign_object/runtime_images")
async def foreign_object_runtime_images(
    product_id: int,
    frame_id: int | None = None,
    face_id: int | None = None,
    item_id: int = 0,
    roi_id: int = 0,
    services: ServiceContainer = Depends(get_services),
):
    """Lấy danh sách ảnh runtime/good của model Dị vật của một vùng ROI.

    Args:
        product_id: Mã product.
        frame_id: Mã frame.
        item_id: Mã item.
        roi_id: Mã vùng ROI trên item.
        services: Container cung cấp service PatchCore Dị vật.

    Returns:
        dict: Danh sách ảnh runtime hoặc trạng thái không có model.

    Raises:
        Không phát sinh lỗi ra ngoài.
    """
    try:
        return services.obj_foreign_object_patch_core_service.get_runtime_images(
            product_id,
            face_id if face_id is not None else (frame_id or 0),
            item_id,
            roi_id=roi_id,
        )
    except (TypeError, ValueError, OSError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.delete("/foreign_object/runtime_image")
async def delete_foreign_object_runtime_image(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Xóa một ảnh runtime/good của model Dị vật.

    Args:
        data: Product, frame, item và tên ảnh cần xóa.
        services: Container cung cấp service PatchCore Dị vật.

    Returns:
        dict: Tên ảnh đã xóa hoặc lỗi dữ liệu.

    Raises:
        Không phát sinh lỗi ra ngoài; lỗi được đóng gói bằng Result.
    """
    try:
        return services.obj_foreign_object_patch_core_service.delete_runtime_image(
            int(data["product_id"]),
            int(data.get("face_id", data.get("frame_id"))),
            int(data.get("item_id", data.get("items_id"))),
            str(data["image_name"]),
            roi_id=int(data.get("roi_id", 0)),
        )
    except (KeyError, TypeError, ValueError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.post("/foreign_object/run_model")
async def run_foreign_object_model(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Chạy inference PatchCore cho model Dị vật của item hiện tại.

    Args:
        data: Product, frame, item, crop ROI và canvas width.
        services: Container cung cấp service PatchCore Dị vật.

    Returns:
        dict: Ảnh overlay, anomaly score, bounding boxes hoặc lỗi.

    Raises:
        Không phát sinh lỗi ra ngoài; lỗi được đóng gói bằng Result.
    """
    try:
        return services.obj_foreign_object_patch_core_service.run_model(
            int(data["product_id"]),
            int(data.get("face_id", data.get("frame_id"))),
            int(data.get("item_id", data.get("items_id"))),
            data["crop_roi"],
            int(data.get("width_canvas", 0)) or None,
            roi_id=int(data.get("roi_id", 0)),
        )
    except (KeyError, TypeError, ValueError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.post("/foreign_object/run_object_model")
async def run_foreign_object_detection_model(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Chạy YOLO trên từng vùng bất thường do PatchCore phát hiện.

    Args:
        data: Product, frame, item, crop ROI và canvas width.
        services: Container cung cấp service PatchCore Dị vật.

    Returns:
        dict: Ảnh overlay, các vùng bất thường đã crop và detection YOLO.

    Raises:
        Không phát sinh lỗi ra ngoài; lỗi được đóng gói bằng Result.
    """
    try:
        return services.obj_foreign_object_patch_core_service.run_model_with_object_detection(
            int(data["product_id"]),
            int(data.get("face_id", data.get("frame_id"))),
            int(data.get("item_id", data.get("items_id"))),
            data["crop_roi"],
            int(data.get("width_canvas", 0)) or None,
            roi_id=int(data.get("roi_id", 0)),
        )
    except (KeyError, TypeError, ValueError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


@router.delete("/foreign_object/model")
async def delete_foreign_object_model(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Xóa session PatchCore và record manifest đúng của model Dị vật.

    Args:
        data: Product, frame và item của model cần xóa.
        services: Container cung cấp service PatchCore Dị vật.

    Returns:
        dict: Thư mục model, số record đã xóa hoặc lỗi.

    Raises:
        Không phát sinh lỗi ra ngoài; lỗi được đóng gói bằng Result.
    """
    try:
        return services.obj_foreign_object_patch_core_service.delete_model(
            int(data["product_id"]),
            int(data.get("face_id", data.get("frame_id"))),
            int(data.get("item_id", data.get("items_id"))),
            roi_id=int(data.get("roi_id", 0)),
        )
    except (KeyError, TypeError, ValueError, OSError):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()


# Kiểm tra Có/Không tem (Stamp)

@router.post("/stamp/run_model")
async def run_model_stamp(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Nhận diện đối tượng nhãn 'stamp' trên nhiều khung ROI của một item."""
    if not isinstance(data, dict):
        return Result.Fail(ErrorCode.INVALID_FORMAT).to_dict()

    raw_select = data.get("select")
    normalized_data = dict(data)
    if isinstance(raw_select, dict) and "frame_id" not in raw_select and "face_id" in raw_select:
        select_copy = dict(raw_select)
        select_copy["frame_id"] = select_copy["face_id"]
        normalized_data["select"] = select_copy

    result_val = ValidateToolLawRegulation.validate_judment_item(normalized_data)
    if not result_val.ok:
        return result_val.to_dict()

    try:
        select_data = normalized_data["select"]
        boxes = normalized_data.get("boxes")
        product_id = int(select_data["product_id"])
        frame_id = int(select_data.get("face_id", select_data.get("frame_id")))
        items_id = int(select_data["items_id"])
        width_canvas = int(normalized_data.get("WidthCanvas", 1))
    except (KeyError, TypeError, ValueError) as error:
        return Result.Fail(f"Dữ liệu không hợp lệ: {error}").to_dict()

    if not isinstance(boxes, list) or not boxes or width_canvas <= 0:
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()

    try:
        result_path = services.obj_point_service.get_path_img_point(
            product_id, frame_id, items_id
        )
        if not result_path.ok:
            return result_path.to_dict()

        img = cv2.imread(str(result_path.data))
        if img is None:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()

        res = services.obj_structure_model_service.inspect_stamp_boxes(
            image=img,
            boxes=boxes,
            label=services.CLASS_STRUCTURE_NAME.STAMP.value,
            width_canvas=width_canvas,
        )
        if not res.ok:
            return res.to_dict()

        return Result.Ok(
            {
                "width": res.data["width"],
                "height": res.data["height"],
                "boxes": res.data["boxes"],
                "objects": res.data["objects"],
            }
        ).to_dict()
    except Exception as error:
        print(f"Lỗi hệ thống trong quá trình kiểm tra tem: {error}")
        return {
            "ok": False,
            "data": None,
            "error_code": ErrorCode.DATA_INVALID.value,
            "error_name": ErrorCode.DATA_INVALID.name,
            "message": f"[Lỗi hệ thống] {error}",
        }


# Kiểm tra Có, lệch tem (Stamp Alignment OBB)

@router.post("/stamp_alignment/run_model")
async def run_model_stamp_alignment(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Nhận diện OBB và kiểm tra độ lệch tem trên các khung ROI của một item."""
    if not isinstance(data, dict):
        return Result.Fail(ErrorCode.INVALID_FORMAT).to_dict()

    raw_select = data.get("select")
    normalized_data = dict(data)
    if isinstance(raw_select, dict) and "frame_id" not in raw_select and "face_id" in raw_select:
        select_copy = dict(raw_select)
        select_copy["frame_id"] = select_copy["face_id"]
        normalized_data["select"] = select_copy

    result_val = ValidateToolLawRegulation.validate_judment_item(normalized_data)
    if not result_val.ok:
        return result_val.to_dict()

    try:
        select_data = normalized_data["select"]
        boxes = normalized_data.get("boxes")
        product_id = int(select_data["product_id"])
        frame_id = int(select_data.get("face_id", select_data.get("frame_id")))
        items_id = int(select_data["items_id"])
        width_canvas = int(normalized_data.get("WidthCanvas", 1))
    except (KeyError, TypeError, ValueError) as error:
        return Result.Fail(f"Dữ liệu không hợp lệ: {error}").to_dict()

    if not isinstance(boxes, list) or not boxes or width_canvas <= 0:
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()

    try:
        result_path = services.obj_point_service.get_path_img_point(
            product_id, frame_id, items_id
        )
        if not result_path.ok:
            return result_path.to_dict()

        img = cv2.imread(str(result_path.data))
        if img is None:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()

        res = services.obj_stamp_alignment_service.inspect_alignment_boxes(
            image=img,
            boxes=boxes,
            width_canvas=width_canvas,
        )
        if not res.ok:
            return res.to_dict()

        return Result.Ok(
            {
                "width": res.data["image_width"],
                "height": res.data["image_height"],
                "boxes": res.data["boxes"],
                "objects": res.data["objects"],
            }
        ).to_dict()
    except Exception as error:
        print(f"Lỗi hệ thống trong quá trình kiểm tra lệch tem: {error}")
        return {
            "ok": False,
            "data": None,
            "error_code": ErrorCode.DATA_INVALID.value,
            "error_name": ErrorCode.DATA_INVALID.name,
            "message": f"[Lỗi hệ thống] {error}",
        }


# Kiểm tra tem in ngược (Stamp Reversed Inspection)

@router.post("/stamp_reversed/run_model")
async def run_model_stamp_reversed(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Kiểm tra hướng tem và hướng chữ in trên các khung ROI của một item."""
    if not isinstance(data, dict):
        return Result.Fail(ErrorCode.INVALID_FORMAT).to_dict()

    raw_select = data.get("select")
    normalized_data = dict(data)
    if isinstance(raw_select, dict) and "frame_id" not in raw_select and "face_id" in raw_select:
        select_copy = dict(raw_select)
        select_copy["frame_id"] = select_copy["face_id"]
        normalized_data["select"] = select_copy

    result_val = ValidateToolLawRegulation.validate_judment_item(normalized_data)
    if not result_val.ok:
        return result_val.to_dict()

    try:
        select_data = normalized_data["select"]
        boxes = normalized_data.get("boxes")
        product_id = int(select_data["product_id"])
        frame_id = int(select_data.get("face_id", select_data.get("frame_id")))
        items_id = int(select_data["items_id"])
        width_canvas = int(normalized_data.get("WidthCanvas", 1))
    except (KeyError, TypeError, ValueError) as error:
        return Result.Fail(f"Dữ liệu không hợp lệ: {error}").to_dict()

    if not isinstance(boxes, list) or not boxes or width_canvas <= 0:
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()

    try:
        result_path = services.obj_point_service.get_path_img_point(
            product_id, frame_id, items_id
        )
        if not result_path.ok:
            return result_path.to_dict()

        img = cv2.imread(str(result_path.data))
        if img is None:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()

        height, width = img.shape[:2]
        scale = width / width_canvas if width_canvas > 0 else 1.0
        scaled_boxes = []
        for box in boxes:
            scaled_box = dict(box)
            if "xStart" in box and "xEnd" in box:
                scaled_box["xStart"] = float(box["xStart"]) * scale
                scaled_box["yStart"] = float(box["yStart"]) * scale
                scaled_box["xEnd"] = float(box["xEnd"]) * scale
                scaled_box["yEnd"] = float(box["yEnd"]) * scale
            elif "x1" in box and "x2" in box:
                scaled_box["x1"] = float(box["x1"]) * scale
                scaled_box["y1"] = float(box["y1"]) * scale
                scaled_box["x2"] = float(box["x2"]) * scale
                scaled_box["y2"] = float(box["y2"]) * scale
            scaled_boxes.append(scaled_box)

        res = services.obj_stamp_reversed_service.inspect_boxes(
            image=img,
            boxes=scaled_boxes,
        )

        return Result.Ok(
            {
                "width": width,
                "height": height,
                "all_ok": res.get("all_ok", False),
                "boxes": res.get("boxes", []),
                "count_total": res.get("count_total", 0),
                "count_ok": res.get("count_ok", 0),
                "count_ng": res.get("count_ng", 0),
                "count_unknown": res.get("count_unknown", 0),
            }
        ).to_dict()
    except Exception as error:
        print(f"Lỗi hệ thống trong quá trình kiểm tra tem in ngược: {error}")
        return {
            "ok": False,
            "data": None,
            "error_code": ErrorCode.DATA_INVALID.value,
            "error_name": ErrorCode.DATA_INVALID.name,
            "message": f"[Lỗi hệ thống] {error}",
        }


@router.post("/ocr/run_model")
async def run_model_ocr(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Chạy OCR và so khớp nội dung cho đúng ROI đang được chọn."""
    if not isinstance(data, dict):
        return Result.Fail(ErrorCode.INVALID_FORMAT).to_dict()

    raw_select = data.get("select")
    normalized_data = dict(data)
    if isinstance(raw_select, dict) and "frame_id" not in raw_select and "face_id" in raw_select:
        select_copy = dict(raw_select)
        select_copy["frame_id"] = select_copy["face_id"]
        normalized_data["select"] = select_copy

    result_val = ValidateToolLawRegulation.validate_judment_item(normalized_data)
    if not result_val.ok:
        return result_val.to_dict()

    region = normalized_data.get("roi")
    if not isinstance(region, dict):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()
    try:
        select_data = normalized_data["select"]
        product_id = int(select_data["product_id"])
        frame_id = int(select_data.get("face_id", select_data.get("frame_id")))
        items_id = int(select_data["items_id"])
        width_canvas = int(normalized_data.get("WidthCanvas", 0))
        height_canvas = int(normalized_data.get("HeightCanvas", 0))
        x1 = int(region["xStart"])
        y1 = int(region["yStart"])
        x2 = int(region["xEnd"])
        y2 = int(region["yEnd"])
        expected_text = str(region.get("expected_text") or "")
    except (KeyError, TypeError, ValueError) as error:
        return Result.Fail(f"Dữ liệu OCR không hợp lệ: {error}").to_dict()
    if (
        width_canvas <= 0
        or height_canvas <= 0
        or x1 < 0
        or y1 < 0
        or x2 <= x1
        or y2 <= y1
    ):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()

    try:
        result_path = services.obj_point_service.get_path_img_point(
            product_id, frame_id, items_id
        )
        if not result_path.ok:
            return result_path.to_dict()

        encoded_image = np.fromfile(str(result_path.data), dtype=np.uint8)
        image = cv2.imdecode(encoded_image, cv2.IMREAD_COLOR)
        if image is None:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()

        image_height, image_width = image.shape[:2]
        region_for_image = {
            **region,
            "x1": round(x1 * image_width / width_canvas),
            "y1": round(y1 * image_height / height_canvas),
            "x2": round(x2 * image_width / width_canvas),
            "y2": round(y2 * image_height / height_canvas),
            "expected_text": expected_text,
        }
        judgment = services.obj_ocr_text_detector.evaluate_roi(
            image,
            region_for_image,
        )
        return Result.Ok(
            {
                "ok": judgment.ok,
                "status": judgment.status,
                "message": judgment.message,
                "boxes": judgment.runtime_data["boxes"],
            }
        ).to_dict()
    except Exception as error:
        print(f"Lỗi hệ thống trong quá trình nhận diện OCR: {error}")
        return Result.Fail(f"[Lỗi OCR] {error}").to_dict()


# Kiểm tra Màu sắc (Color Inspection)

@router.post("/color/run_model")
async def run_model_color(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Đo màu trung bình và kiểm tra độ sai lệch màu trên các khung ROI của một item."""
    if not isinstance(data, dict):
        return Result.Fail(ErrorCode.INVALID_FORMAT).to_dict()

    raw_select = data.get("select")
    normalized_data = dict(data)
    if isinstance(raw_select, dict) and "frame_id" not in raw_select and "face_id" in raw_select:
        select_copy = dict(raw_select)
        select_copy["frame_id"] = select_copy["face_id"]
        normalized_data["select"] = select_copy

    result_val = ValidateToolLawRegulation.validate_judment_item(normalized_data)
    if not result_val.ok:
        return result_val.to_dict()

    try:
        select_data = normalized_data["select"]
        boxes = normalized_data.get("boxes")
        product_id = int(select_data["product_id"])
        frame_id = int(select_data.get("face_id", select_data.get("frame_id")))
        items_id = int(select_data["items_id"])
        width_canvas = int(normalized_data.get("WidthCanvas", 1))
    except (KeyError, TypeError, ValueError) as error:
        return Result.Fail(f"Dữ liệu không hợp lệ: {error}").to_dict()

    if not isinstance(boxes, list) or not boxes or width_canvas <= 0:
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()

    try:
        result_path = services.obj_point_service.get_path_img_point(
            product_id, frame_id, items_id
        )
        if not result_path.ok:
            return result_path.to_dict()

        encoded_image = np.fromfile(str(result_path.data), dtype=np.uint8)
        img = cv2.imdecode(encoded_image, cv2.IMREAD_COLOR)
        if img is None:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()

        res = services.obj_color_service.inspect_color_boxes(
            image=img,
            boxes=boxes,
            width_canvas=width_canvas,
        )
        if not res.ok:
            return res.to_dict()

        return Result.Ok(
            {
                "width": res.data["image_width"],
                "height": res.data["image_height"],
                "boxes": res.data["boxes"],
            }
        ).to_dict()
    except Exception as error:
        print(f"Lỗi hệ thống trong quá trình kiểm tra màu: {error}")
        return {
            "ok": False,
            "data": None,
            "error_code": ErrorCode.DATA_INVALID.value,
            "error_name": ErrorCode.DATA_INVALID.name,
            "message": f"[Lỗi hệ thống] {error}",
        }


@router.post("/barcode/run_model")
async def run_model_barcode(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Chạy đọc Barcode 1D và so khớp nội dung cho ROI đang được chọn."""
    if not isinstance(data, dict):
        return Result.Fail(ErrorCode.INVALID_FORMAT).to_dict()

    raw_select = data.get("select")
    normalized_data = dict(data)
    if isinstance(raw_select, dict) and "frame_id" not in raw_select and "face_id" in raw_select:
        select_copy = dict(raw_select)
        select_copy["frame_id"] = select_copy["face_id"]
        normalized_data["select"] = select_copy

    result_val = ValidateToolLawRegulation.validate_judment_item(normalized_data)
    if not result_val.ok:
        return result_val.to_dict()

    region = normalized_data.get("roi")
    if not isinstance(region, dict):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()
    try:
        select_data = normalized_data["select"]
        product_id = int(select_data["product_id"])
        frame_id = int(select_data.get("face_id", select_data.get("frame_id")))
        items_id = int(select_data["items_id"])
        width_canvas = int(normalized_data.get("WidthCanvas", 0))
        height_canvas = int(normalized_data.get("HeightCanvas", 0))
        x1 = int(region["xStart"])
        y1 = int(region["yStart"])
        x2 = int(region["xEnd"])
        y2 = int(region["yEnd"])
        expected_text = str(region.get("expected_text") or "")
    except (KeyError, TypeError, ValueError) as error:
        return Result.Fail(f"Dữ liệu Barcode không hợp lệ: {error}").to_dict()
    if (
        width_canvas <= 0
        or height_canvas <= 0
        or x1 < 0
        or y1 < 0
        or x2 <= x1
        or y2 <= y1
    ):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()

    try:
        result_path = services.obj_point_service.get_path_img_point(
            product_id, frame_id, items_id
        )
        if not result_path.ok:
            return result_path.to_dict()

        encoded_image = np.fromfile(str(result_path.data), dtype=np.uint8)
        image = cv2.imdecode(encoded_image, cv2.IMREAD_COLOR)
        if image is None:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()

        image_height, image_width = image.shape[:2]
        region_for_image = {
            **region,
            "x1": round(x1 * image_width / width_canvas),
            "y1": round(y1 * image_height / height_canvas),
            "x2": round(x2 * image_width / width_canvas),
            "y2": round(y2 * image_height / height_canvas),
            "expected_text": expected_text,
        }
        judgment = services.obj_barcode_detector.evaluate_roi(
            image,
            region_for_image,
        )
        return Result.Ok(
            {
                "ok": judgment.ok,
                "status": judgment.status,
                "message": judgment.message,
                "boxes": judgment.runtime_data["boxes"],
            }
        ).to_dict()
    except Exception as error:
        print(f"Lỗi hệ thống trong quá trình nhận diện Barcode: {error}")
        return Result.Fail(f"[Lỗi Barcode] {error}").to_dict()


@router.post("/qr/run_model")
async def run_model_qr(
    data: dict = Body(),
    services: ServiceContainer = Depends(get_services),
):
    """Chạy đọc mã QR 2D và so khớp nội dung cho ROI đang được chọn."""
    if not isinstance(data, dict):
        return Result.Fail(ErrorCode.INVALID_FORMAT).to_dict()

    raw_select = data.get("select")
    normalized_data = dict(data)
    if isinstance(raw_select, dict) and "frame_id" not in raw_select and "face_id" in raw_select:
        select_copy = dict(raw_select)
        select_copy["frame_id"] = select_copy["face_id"]
        normalized_data["select"] = select_copy

    result_val = ValidateToolLawRegulation.validate_judment_item(normalized_data)
    if not result_val.ok:
        return result_val.to_dict()

    region = normalized_data.get("roi")
    if not isinstance(region, dict):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()
    try:
        select_data = normalized_data["select"]
        product_id = int(select_data["product_id"])
        frame_id = int(select_data.get("face_id", select_data.get("frame_id")))
        items_id = int(select_data["items_id"])
        width_canvas = int(normalized_data.get("WidthCanvas", 0))
        height_canvas = int(normalized_data.get("HeightCanvas", 0))
        x1 = int(region["xStart"])
        y1 = int(region["yStart"])
        x2 = int(region["xEnd"])
        y2 = int(region["yEnd"])
        expected_text = str(region.get("expected_text") or "")
    except (KeyError, TypeError, ValueError) as error:
        return Result.Fail(f"Dữ liệu QR không hợp lệ: {error}").to_dict()
    if (
        width_canvas <= 0
        or height_canvas <= 0
        or x1 < 0
        or y1 < 0
        or x2 <= x1
        or y2 <= y1
    ):
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()

    try:
        result_path = services.obj_point_service.get_path_img_point(
            product_id, frame_id, items_id
        )
        if not result_path.ok:
            return result_path.to_dict()

        encoded_image = np.fromfile(str(result_path.data), dtype=np.uint8)
        image = cv2.imdecode(encoded_image, cv2.IMREAD_COLOR)
        if image is None:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()

        image_height, image_width = image.shape[:2]
        region_for_image = {
            **region,
            "x1": round(x1 * image_width / width_canvas),
            "y1": round(y1 * image_height / height_canvas),
            "x2": round(x2 * image_width / width_canvas),
            "y2": round(y2 * image_height / height_canvas),
            "expected_text": expected_text,
        }
        judgment = services.obj_qr_detector.evaluate_roi(
            image,
            region_for_image,
        )
        return Result.Ok(
            {
                "ok": judgment.ok,
                "status": judgment.status,
                "message": judgment.message,
                "boxes": judgment.runtime_data["boxes"],
            }
        ).to_dict()
    except Exception as error:
        print(f"Lỗi hệ thống trong quá trình nhận diện QR: {error}")
        return Result.Fail(f"[Lỗi QR] {error}").to_dict()

