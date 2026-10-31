import os
from fastapi import APIRouter, Depends, Body
from typing import Any
from app.machine.anti_blur_service import AntiBlurService
from app.core.dependencies import get_services
from app.config import PATH_FEATUERES_CFG_CAM, CameraConfig

router = APIRouter(
    prefix="/api/anti_blur",
    tags=["AntiBlur"]
)


@router.get("/config")
def get_anti_blur_config():
    """Lấy cấu hình tham số chống rung nhòe cơ khí (Anti-Blur) từ file storage/anti_blur.json."""
    config = AntiBlurService.load_config()
    try:
        calculated = AntiBlurService.calculate_recommended_timers(
            fov_mm=float(config.get("fov_mm", 40.0)),
            sensor_px=int(config.get("sensor_px", 2000)),
            b_max_px=float(config.get("b_max_px", 0.5)),
            a0_um=float(config.get("a0_um", 50.0)),
            fn_hz=float(config.get("fn_hz", 50.0)),
            zeta=float(config.get("zeta", 0.08)),
            t_exp_ms=float(config.get("t_exp_ms", 2.0)),
            is_hardware_trigger=bool(config.get("is_hardware_trigger", False)),
            t_safety_ms=float(config.get("t_safety_ms", 5.0)),
        )
    except Exception:
        calculated = {}
    return {
        "status": True,
        "data": config,
        "calculated": calculated,
    }


@router.post("/config")
def save_anti_blur_config(payload: dict = Body(...), services=Depends(get_services)):
    """Lưu cấu hình tham số chống rung nhòe cơ khí vào file storage/anti_blur.json
    và đồng bộ thời gian thực sang dịch vụ IAI."""
    saved_config = AntiBlurService.save_config(payload)

    # Đồng bộ sang obj_iai_config nếu có trong container
    iai_config = getattr(services, "obj_iai_config", None)
    if iai_config:
        try:
            iai_config.t_settle_ms = float(saved_config.get("t_settle_ms", 40.0))
            iai_config.t_hold_safety_ms = float(saved_config.get("t_hold_safety_ms", 15.0))
            iai_config.blur_threshold = float(saved_config.get("blur_threshold", 100.0))
            iai_config.auto_retrigger_on_blur = bool(saved_config.get("auto_retrigger_on_blur", True))
            iai_config.max_retrigger_count = int(saved_config.get("max_retrigger_count", 1))
            iai_config.save()
        except Exception:
            pass

    return {
        "status": True,
        "message": "Đã lưu cấu hình Anti-Blur thành công vào storage",
        "data": saved_config,
    }


@router.post("/calculate")
def calculate_anti_blur_timers(payload: dict = Body(...)):
    """Tính toán thời gian T_settle, T_hold và các chỉ số rung lắc dựa trên thông số nhập vào."""
    fov_mm = float(payload.get("fov_mm", 40.0))
    sensor_px = int(payload.get("sensor_px", 2000))
    b_max_px = float(payload.get("b_max_px", 0.5))
    a0_um = float(payload.get("a0_um", 50.0))
    fn_hz = float(payload.get("fn_hz", 50.0))
    zeta = float(payload.get("zeta", 0.08))
    t_exp_ms = float(payload.get("t_exp_ms", 2.0))
    is_hardware_trigger = bool(payload.get("is_hardware_trigger", False))
    t_safety_ms = float(payload.get("t_safety_ms", 5.0))

    result = AntiBlurService.calculate_recommended_timers(
        fov_mm=fov_mm,
        sensor_px=sensor_px,
        b_max_px=b_max_px,
        a0_um=a0_um,
        fn_hz=fn_hz,
        zeta=zeta,
        t_exp_ms=t_exp_ms,
        is_hardware_trigger=is_hardware_trigger,
        t_safety_ms=t_safety_ms,
    )
    return {
        "status": True,
        "data": result,
    }


@router.post("/reload_features")
def reload_features_config(services=Depends(get_services)):
    """Nạp lại cấu hình phần cứng từ features.cfg vào Camera và trích xuất ExposureTime thực tế."""
    if not os.path.exists(PATH_FEATUERES_CFG_CAM):
        return {
            "status": False,
            "message": f"Không tìm thấy file cấu hình {PATH_FEATUERES_CFG_CAM}",
            "hardware_info": None,
        }

    try:
        cam_config = CameraConfig.from_feature_file(PATH_FEATUERES_CFG_CAM)
        exp_ms = round(cam_config.exposure_time / 1000.0, 3)
        hardware_info = {
            "exposure_time_ms": exp_ms,
            "acquisition_frame_rate": cam_config.acquisition_frame_rate,
            "gain": cam_config.gain,
            "trigger_mode": cam_config.trigger_mode,
        }
    except Exception as e:
        return {
            "status": False,
            "message": f"Lỗi đọc file features.cfg: {str(e)}",
            "hardware_info": None,
        }

    camera_applied = False
    camera_service = getattr(services, "obj_camera", None) if services else None
    if camera_service and hasattr(camera_service, "nodemap") and camera_service.nodemap:
        try:
            camera_service.reload_feature_file()
            camera_applied = True
        except Exception:
            camera_applied = False

    msg = f"Đã nạp features.cfg thành công (Exposure: {exp_ms} ms)."
    if camera_applied:
        msg += " Đã đồng bộ trực tiếp vào Camera Sentech phần cứng!"
    else:
        msg += " (Camera đang offline - đã nạp và áp dụng giá trị từ file)."

    return {
        "status": True,
        "camera_applied": camera_applied,
        "message": msg,
        "hardware_info": hardware_info,
    }


@router.get("/defaults")
def get_anti_blur_defaults():
    """Lấy danh sách tham số mặc định chuẩn của Anti-Blur."""
    return {
        "status": True,
        "data": dict(AntiBlurService.DEFAULT_CONFIG),
        "message": "Đã lấy danh sách tham số mặc định chuẩn an toàn",
    }
