# from pathlib import Path
# import sys
# sys.path.append(str(Path(__file__).resolve().parents[3]))
# from app.utils import obj_queue,type_capture,name_queue_log_client
from app.model import Point
from fastapi import APIRouter, WebSocket, Body, Depends, WebSocketDisconnect
import asyncio
from app.container import ServiceContainer
from app.core.dependencies import get_services,get_services_ws
from app.config import TypeSend
import cv2
from pydantic import BaseModel
from app.core import (Result,ErrorCode)
from app.validate import ValidateCaptureProduct
from app.container import EnumMode
class PointData(BaseModel):
    x: float
    y: float
    z: float
    rx: float = 180.0
    ry: float = 0.0
    rz: float = 0.0

router = APIRouter(
    prefix="/captureproduct",
    tags=["Captureproduct"]
)

@router.post("/run_face")
@router.post("/run_frame")
async def run_frame(services: ServiceContainer = Depends(get_services),payload: dict = Body(...)):
    """Chạy lần lượt các điểm đã lưu trong một frame qua RobotControl 6-DOF."""
    try:
        product_id = int(payload.get("ProductID"))
        frame_id = int(payload.get("FaceID", payload.get("FrameID")))
    except (TypeError, ValueError):
        return {"ok": False, "message": "ProductID hoặc FrameID không hợp lệ."}
    points_result = services.obj_point_service.get_xyz_by_product_frame(
        product_id, frame_id
    )
    if not points_result.ok:
        return {"ok": False, "message": "Không tìm thấy frame cần chạy."}
    if not hasattr(services, "obj_robot_control") or services.obj_robot_control is None:
        return {"ok": False, "message": "RobotControl chưa được khởi tạo."}

    for point_id, point in points_result.data.items():
        x = float(point["x"])
        y = float(point["y"])
        z = float(point["z"])
        rx = float(point.get("rx", 180.0))
        ry = float(point.get("ry", 0.0))
        rz = float(point.get("rz", 0.0))
        moved, msg = await asyncio.to_thread(
            services.obj_robot_control.move_to_point,
            x, y, z, rx, ry, rz
        )
        if not moved:
            return {"ok": False, "message": f"Chạy thất bại tại point {point_id}: {msg}"}
    return {"ok": True, "message": f"Đã chạy xong frame {frame_id}."}

@router.post("/run_product")
async def run_product(services: ServiceContainer = Depends(get_services),payload: dict = Body(...)):
    """Chạy lần lượt toàn bộ điểm đã lưu của một sản phẩm qua RobotControl 6-DOF."""
    try:
        product_id = int(payload.get("ProductID"))
    except (TypeError, ValueError):
        return {"ok": False, "message": "ProductID không hợp lệ."}
    points_result = services.obj_point_service.get_all_xyz_by_product_id(product_id)
    if not points_result.ok:
        return {"ok": False, "message": "Không tìm thấy sản phẩm cần chạy."}
    if not hasattr(services, "obj_robot_control") or services.obj_robot_control is None:
        return {"ok": False, "message": "RobotControl chưa được khởi tạo."}

    for frame_id, points in points_result.data.items():
        for point in points:
            x = float(point["x"])
            y = float(point["y"])
            z = float(point["z"])
            rx = float(point.get("rx", 180.0))
            ry = float(point.get("ry", 0.0))
            rz = float(point.get("rz", 0.0))
            moved, msg = await asyncio.to_thread(
                services.obj_robot_control.move_to_point,
                x, y, z, rx, ry, rz
            )
            if not moved:
                return {
                    "ok": False,
                    "message": (
                        f"Chạy thất bại tại frame {frame_id}, "
                        f"point {point.get('point_id')}: {msg}"
                    )
                }
    return {"ok": True, "message": f"Đã chạy xong sản phẩm {product_id}."}



@router.post("/erase_item_img")
async def erase_item_img(services: ServiceContainer = Depends(get_services),payload: dict = Body(...)):
    print("--------------Xóa sản Item Point----------------")
    id_product_selecting_now = payload.get("id_product_selecting_now")
    frame_id =  payload.get("FaceID", payload.get("FrameID"))
    point_id = payload.get("PointID")
    print(f"Sản phẩm xóa Point :{id_product_selecting_now} Frame ID:{frame_id} Point ID:{point_id}")
    try:
        id_product_selecting_now = int(id_product_selecting_now)
        frame_id = int(frame_id)
        point_id = int(point_id)
    except Exception:
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()
    status_data = ValidateCaptureProduct.validate_erase_item_img(id_product_selecting_now,frame_id,point_id)
    if not status_data:
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()

    delete_result = services.obj_capture_item_delete_service.delete_capture_item(
        id_product_selecting_now,
        frame_id,
        point_id,
    )
    default_iai_config = services.obj_iai_config.get_dict()
    product = services.obj_products_service.get_product_by_id(id_product_selecting_now)
    points_result = services.obj_point_service.get_points_by_product_id(id_product_selecting_now)

    data_payload = {
        "data_point": points_result.data if points_result.ok else {},
        "default_iai": default_iai_config,
        "infor_iai": default_iai_config,
        "product": product.data if product.ok else None,
        "technical_report": (
            delete_result.data.get("technical_report", [])
            if delete_result.ok
            else delete_result.error.get("technical_report", [])
            if isinstance(delete_result.error, dict)
            else []
        ),
    }

    if delete_result.ok:
        services.notify_config_changed("erase_item_img")
        return Result.Ok(data_payload).to_dict() | {
            "message": "Đã xóa ảnh thành công.",
        }

    failure_message = "Xóa ảnh thất bại. Dữ liệu đã được rollback."
    if isinstance(delete_result.error, dict):
        failure_message = delete_result.error.get("message") or failure_message
    return {
        "ok": False,
        "data": data_payload,
        "error_code": ErrorCode.DATA_INVALID.value,
        "error_name": ErrorCode.DATA_INVALID.name,
        "message": failure_message,
    }


@router.post("/erase_face")
@router.post("/erase_frame")
async def erase_frame(services: ServiceContainer = Depends(get_services),payload: dict = Body(...)):
    print("--------------Xóa sản Item Point----------------")
    id_product_selecting_now = payload.get("id_product_selecting_now")
    frame_id =  payload.get("FaceID", payload.get("FrameID"))
    print(f"Sản phẩm xóa Frame :{id_product_selecting_now} Frame ID:{frame_id}")
    try:
        id_product_selecting_now = int(id_product_selecting_now)
        frame_id = int(frame_id)
    except Exception:
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()
    status_data = ValidateCaptureProduct.validate_erase_frame(id_product_selecting_now,frame_id)
    if not status_data:
        return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()

    frame_points = services.obj_point_service.points.get(id_product_selecting_now, {}).get(frame_id)
    aggregate_report = []
    first_error_message = None
    if frame_points is None:
        cleanup_result = services.obj_capture_item_delete_service.cleanup_empty_frame_structure(
            id_product_selecting_now,
            frame_id,
        )
        cleanup_steps = (
            cleanup_result.data.get("technical_report", [])
            if cleanup_result.ok
            else cleanup_result.error.get("technical_report", [])
            if isinstance(cleanup_result.error, dict)
            else []
        )
        aggregate_report.append(
            {
                "point_id": None,
                "ok": bool(cleanup_result.ok),
                "steps": cleanup_steps,
            }
        )
        if not cleanup_result.ok:
            first_error_message = "Xóa frame thất bại khi dọn cấu trúc thư mục rỗng."

    if frame_points is not None:
        point_ids = list(frame_points.keys())

        for point_id in point_ids:
            delete_result = services.obj_capture_item_delete_service.delete_capture_item(
                id_product_selecting_now,
                frame_id,
                int(point_id),
            )
            step_report = (
                delete_result.data.get("technical_report", [])
                if delete_result.ok
                else delete_result.error.get("technical_report", [])
                if isinstance(delete_result.error, dict)
                else []
            )
            aggregate_report.append({
                "point_id": int(point_id),
                "ok": bool(delete_result.ok),
                "steps": step_report,
            })

            if not delete_result.ok and first_error_message is None:
                if isinstance(delete_result.error, dict):
                    first_error_message = delete_result.error.get("message")
                if not first_error_message:
                    first_error_message = "Xóa frame thất bại ở một item."
                break

        if first_error_message is None:
            cleanup_result = services.obj_capture_item_delete_service.cleanup_empty_frame_structure(
                id_product_selecting_now,
                frame_id,
            )
            cleanup_steps = (
                cleanup_result.data.get("technical_report", [])
                if cleanup_result.ok
                else cleanup_result.error.get("technical_report", [])
                if isinstance(cleanup_result.error, dict)
                else []
            )
            aggregate_report.append(
                {
                    "point_id": None,
                    "ok": bool(cleanup_result.ok),
                    "steps": cleanup_steps,
                }
            )
            if not cleanup_result.ok:
                first_error_message = "Xóa frame thất bại khi dọn cấu trúc thư mục rỗng."

    default_iai_config = services.obj_iai_config.get_dict()
    product = services.obj_products_service.get_product_by_id(id_product_selecting_now)
    points_result = services.obj_point_service.get_points_by_product_id(id_product_selecting_now)

    robot_safety_limits = {}
    if hasattr(services, "obj_robot_config") and services.obj_robot_config:
        robot_safety_limits = services.obj_robot_config.to_dict().get("safety_limits", {})
    data_payload = {
        "data_point": points_result.data if points_result.ok else {},
        "default_iai": default_iai_config,
        "infor_iai": default_iai_config,
        "robot_safety_limits": robot_safety_limits,
        "product": product.data if product.ok else None,
        "technical_report": aggregate_report,
    }

    if first_error_message is None:
        services.notify_config_changed("erase_frame")
        return Result.Ok(data_payload).to_dict() | {
            "message": "Đã xóa frame thành công.",
        }

    return {
        "ok": False,
        "data": data_payload,
        "error_code": ErrorCode.DATA_INVALID.value,
        "error_name": ErrorCode.DATA_INVALID.name,
        "message": first_error_message,
    }








@router.post("/")
async def captureproduct_load(
    services: ServiceContainer = Depends(get_services),
    payload: dict = Body(...)
):
    print("--------------Vào UI capture----------------")
    status = payload.get("status")
    print("Status:", status)
    services.obj_products_service.reload_products()
    choose_product_current = services.obj_choose_product.get_choose_product()
    print("choose_product_current",choose_product_current)
    if not choose_product_current.ok:
        return Result.Fail(choose_product_current.error).to_dict()
    product_id = choose_product_current.data
    product_result = services.obj_products_service.get_product_by_id(product_id)
    if not product_result.ok:
        return Result.Fail(product_result.error).to_dict()
    product = product_result.data
    default_iai_config = services.obj_iai_config.get_dict() if hasattr(services, "obj_iai_config") and services.obj_iai_config else {}
    robot_safety_limits = {}
    if hasattr(services, "obj_robot_config") and services.obj_robot_config:
        robot_safety_limits = services.obj_robot_config.to_dict().get("safety_limits", {})
    points_result = services.obj_point_service.get_points_by_product_id(product_id)
    return Result.Ok({
        "product": product,
        "default_iai": default_iai_config,
        "infor_iai": default_iai_config,
        "robot_safety_limits": robot_safety_limits,
        "data_point": points_result.data if points_result.ok else [],
    }).to_dict()


    


@router.post("/capture")
async def capture(services: ServiceContainer = Depends(get_services),data: dict = Body(...)):
    print("--------------Chụp ảnh point----------------")
    try:
        product_selecting = int(data.get("product_selecting"))
        id_frame = int(data.get("id_frame"))
        id_point = int(data.get("id_point"))
        x = float(data.get("x", 0))
        y = float(data.get("y", 0))
        z = float(data.get("z", 0))
        rx = float(data.get("rx", 180.0))
        ry = float(data.get("ry", 0.0))
        rz = float(data.get("rz", 0.0))
    except Exception:
        print("Lỗi kiểu đinh dạng gửi vào")
        return {
            "ok": False,
            "error": "INVALID_INPUT",
            "message": "Dữ liệu đầu vào không hợp lệ x y z id frame id_point có thể không phải là int"
        }

    if services.obj_choose_product.get_choose_product().data == product_selecting:
        status_cam,img = services.obj_camera.capture_once(1)
        print("status camera",status_cam)
        status_check_point = services.obj_point_service.is_exists_product_frame_point_id(product_selecting,id_frame,id_point)
        product = services.obj_products_service.get_product_by_id(product_selecting)
        default_iai_config = services.obj_iai_config.get_dict()
        if not status_check_point:
                point = Point(id_point, x, y, z, rx, ry, rz)
                result_add_point = services.obj_point_service.add_point(product_selecting,id_frame,point,img)
                if result_add_point.ok:
                        print("Tạo điểm mới thành công.")
                        services.notify_config_changed("capture_add_point")
                        return Result.Ok({
                            "data_point": services.obj_point_service.get_points_by_product_id(product_selecting).data,
                            "default_iai": default_iai_config,
                            "infor_iai": default_iai_config,
                            "product": product.data
                        }).to_dict()
                print("Tạo điểm mới thất bại")
                return {
                    "ok": False,
                    "error": result_add_point.error,
                    "message": result_add_point.message()
                }
        else:
                print("Update điểm cũ đã tồn tại.")
                result_update  = services.obj_point_service.update_point(product_selecting,id_frame,id_point,x,y,z,img,rx=rx,ry=ry,rz=rz)
                if result_update.ok:
                        print("update điểm cũ thành công.")
                        services.notify_config_changed("capture_update_point")
                        return Result.Ok({
                            "data_point": services.obj_point_service.get_points_by_product_id(product_selecting).data,
                            "default_iai": default_iai_config,
                            "infor_iai": default_iai_config,
                            "product": product.data
                        }).to_dict()
                print("Update điểm cũ thất bại.Hãy kiễm tra lại nguyên nhân lỗi")
                return {
                    "ok": False,
                    "error": result_update.error,
                    "message": result_update.message()
                }


@router.get("/exit")
async def exit():
    return {
        "status": "ok",
        "redirect_url": "/"
}

   




      
@router.post("/run_point")
async def run_point(data: PointData, services: ServiceContainer = Depends(get_services)):
    x = data.x
    y = data.y
    z = data.z
    rx = data.rx
    ry = data.ry
    rz = data.rz
    print(f"Nh?n t?a ?? Robot: X={x}, Y={y}, Z={z}, Rx={rx}, Ry={ry}, Rz={rz}")

    if services is None:
        return {"ok": False, "message": "H? th?ng d?ch v? ch?a s?n s?ng."}

    # 1. ?u ti?n ?i?u khi?n Robot / Cobot 6-DOF qua TCP Socket
    if hasattr(services, "obj_robot_control") and services.obj_robot_control is not None:
        ok, msg = await asyncio.to_thread(
            services.obj_robot_control.move_to_point, x, y, z, rx, ry, rz
        )
        return {"ok": ok, "message": msg}

    # 2. Fallback IAI n?u ch?a c?u h?nh Robot
    if hasattr(services, "obj_iai_control") and services.obj_iai_control is not None:
        if not services.obj_iai_control.can_move_iai("Ch?y ?i?m"):
            return {
                "ok": False,
                "message": "? Kh?ng cho ph?p Ch?y ?i?m: IAI ch?a v? g?c. H?y nh?n n?t xanh ?? v? g?c tr??c.",
            }
        if services.obj_iai_service.is_valid_position(x, y, z):
            status_resquest_control_services_arm_move = await asyncio.to_thread(
                services.obj_iai_control.move_to_point, x, y, z
            )
            if status_resquest_control_services_arm_move:
                return {
                    "ok": True,
                    "message": f"? G?i ?i?m X:{x}, Y:{y}, Z:{z} th?nh c?ng."
                }
            return {
                "ok": False,
                "message": f"? G?i ?i?m X:{x}, Y:{y}, Z:{z} th?t b?i."
            }
        return {
            "ok": False,
            "message": f"?? Nh?n ?i?m X:{x}, Y:{y}, Z:{z} n?m ngo?i gi?i h?n tr?c."
        }

    return {"ok": False, "message": "Kh?ng t?m th?y b? ?i?u khi?n Robot ho?c IAI."}


@router.post("/home")
async def robot_home(services: ServiceContainer = Depends(get_services)):
    """??a Cobot v? v? tr? Home an to?n."""
    if services is not None and hasattr(services, "obj_robot_control") and services.obj_robot_control is not None:
        ok, msg = await asyncio.to_thread(services.obj_robot_control.home)
        return {"ok": ok, "message": msg}
    return {"ok": False, "message": "RobotControl ch?a ???c kh?i t?o."}


@router.post("/stop")
async def robot_stop(services: ServiceContainer = Depends(get_services)):
    """D?ng kh?n c?p / d?ng m?m Cobot."""
    if services is not None and hasattr(services, "obj_robot_control") and services.obj_robot_control is not None:
        ok, msg = await asyncio.to_thread(services.obj_robot_control.stop)
        return {"ok": ok, "message": msg}
    return {"ok": False, "message": "RobotControl ch?a ???c kh?i t?o."}


@router.post("/reset")
async def robot_reset(services: ServiceContainer = Depends(get_services)):
    """Reset tr?ng th?i l?i c?a Cobot."""
    if services is not None and hasattr(services, "obj_robot_control") and services.obj_robot_control is not None:
        ok, msg = await asyncio.to_thread(services.obj_robot_control.reset)
        return {"ok": ok, "message": msg}
    return {"ok": False, "message": "RobotControl ch?a ???c kh?i t?o."}


@router.websocket("/ws")
async def camera_ws(ws: WebSocket,services: ServiceContainer = Depends(get_services_ws)):
    # obj_queue.put(name_queue_log_client,{"type":TypeSend.type_capture,"message":"✅ Cammera đã được kết nối."})
    print("✅ Chuẩn bị mở luồng camera")
    await ws.accept()
    try:
        while True:
            image = services.obj_camera.image
            if image is not None:
                encoded, buf = await asyncio.to_thread(
                    cv2.imencode,
                    ".jpg",
                    image,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 70],
                )
                if encoded:
                    await ws.send_bytes(buf.tobytes())
            if services.obj_camera.camera_lost:
                print("Main: reconnect camera")
                services.obj_camera.release()
                await asyncio.sleep(1)
                services.obj_camera.refesh_data()
                services.obj_camera.init()
            else:
                await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        print("Client đã ngắt kết nối camera WebSocket")
    except (ConnectionResetError, BrokenPipeError):
        print("Client đã đóng kết nối camera WebSocket")
    except Exception as error:
        print(f"WebSocket error: {error}")
    finally:
        try:
            await ws.close()
        except (RuntimeError, ConnectionResetError):
            pass

