import logging
from fastapi import APIRouter, Depends

from app.core.dependencies import get_services

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/camera",
    tags=["Camera"]
)


@router.get("/status")
def camera_status(services=Depends(get_services)):
    """Trả về trạng thái kết nối và cấu hình hiện tại của camera.

    Input: service container từ FastAPI dependency.
    Output: trạng thái camera, thông tin thiết bị và cấu hình hiện tại.
    Chế độ: Chỉ đọc (Read-only).
    """
    camera = services.obj_camera
    device_info = camera.get_device_info() if hasattr(camera, "get_device_info") else {}
    return {
        "status": "ok" if camera.get_is_connect() else "disconnected",
        "camera_lost": camera.camera_lost,
        "config": camera.get_config(),
        "device_info": device_info,
    }


@router.get("/config")
def get_camera_config(services=Depends(get_services)):
    """Lấy thông số cấu hình hoạt động và thông tin thiết bị phần cứng của camera.

    Ghi chú: Toàn bộ thông số hoạt động được khởi tạo cố định từ file features.cfg
    khi khởi động hệ thống. Giao diện người dùng và API không cho phép thay đổi.
    """
    camera = services.obj_camera
    config = camera.get_config()
    device_info = camera.get_device_info() if hasattr(camera, "get_device_info") else {}
    return {
        **config,
        "device_info": device_info,
    }


@router.get("/exit")
def exit_camera_config():
    """Xác nhận đóng màn hình thông tin camera và điều hướng trở lại màn hình chính."""
    logger.info("[CameraRouter] Yêu cầu thoát panel thông tin camera")
    return {"status": "ok", "redirect_url": "/"}
