from fastapi import APIRouter, Depends
from pathlib import Path
from app.config.path_config import (
    PATH_FILE_MODEL_YOLO_STAMP,
    PATH_FILE_MODEL_YOLO_FOREIGN,
    PATH_FOLDER_MODEL_DETECT_PATCH_CORE,
    PATH_FILE_DEFAULT_PATCHCORE_INDEX,
    PATH_FOLDER_IMG_COORDINATE_OUTPUT,
    PATH_FOLDER_OUTPUT_JUDGMENT,
    PATH_FOLDER_OUTPUT_RETRAIN,
)
from app.core.dependencies import get_services

router = APIRouter(
    prefix="/software",
    tags=["Software"]
)

@router.get("/version")
def software_version():
    return {"version": "1.0.0"}


@router.get("/ai_model_paths")
def get_ai_model_paths():
    """Trả về đường dẫn tuyệt đối chi tiết của tất cả các mô hình AI phục vụ hiển thị trên giao diện."""
    def to_abs(p):
        return str(Path(p).resolve())

    return {
        "status": True,
        "paths": {
            # YOLO Object
            "yolo_obj_stamp": to_abs(PATH_FILE_MODEL_YOLO_STAMP),
            "yolo_obj_foreign": to_abs(PATH_FILE_MODEL_YOLO_FOREIGN),
            # PatchCore
            "patchcore_model_folder": to_abs(PATH_FOLDER_MODEL_DETECT_PATCH_CORE),
            "patchcore_index": to_abs(PATH_FILE_DEFAULT_PATCHCORE_INDEX),
        }
    }


@router.post("/browse_log_dir")
def browse_log_dir():
    """Mở hộp thoại Windows native folder picker để người dùng chọn thư mục lưu trữ log."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        selected_dir = filedialog.askdirectory(title="Chọn thư mục lưu trữ Log")
        root.destroy()
        if selected_dir:
            return {"status": True, "selected_path": str(Path(selected_dir).resolve())}
        return {"status": False, "selected_path": ""}
    except Exception as e:
        return {"status": False, "error": str(e)}


@router.post("/browse_output_dir")
def browse_output_dir():
    """Mở hộp thoại Windows native folder picker để người dùng chọn thư mục lưu trữ Output (app\\output)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        selected_dir = filedialog.askdirectory(title="Chọn thư mục lưu trữ Output (app\\output)")
        root.destroy()
        if selected_dir:
            return {"status": True, "selected_path": str(Path(selected_dir).resolve())}
        return {"status": False, "selected_path": ""}
    except Exception as e:
        return {"status": False, "error": str(e)}


@router.get("/information")
def software_information(services=Depends(get_services)):
    """Trả về metadata phần mềm và các đường dẫn model/output cho giao diện.

    Input: service container của ứng dụng do FastAPI inject.
    Output: metadata và danh sách model, thư mục output theo ba nhóm.
    Errors: lỗi cấu hình service có thể được FastAPI trả về dưới dạng HTTP 500.
    """
    def display_path(path):
        """Chuẩn hóa đường dẫn cấu hình thành đường dẫn tuyệt đối.

        Input: đường dẫn file hoặc thư mục trong cấu hình.
        Output: đường dẫn tuyệt đối theo hệ điều hành hiện tại.
        Errors: OSError nếu hệ thống không thể phân giải đường dẫn.
        """
        return str(Path(path).resolve())

    return {
        "software": services.obj_infor_software.to_dict(),
        "models": [
            {"label": "Mô hình YOLO nhận diện Tem (Stamp)", "path": display_path(PATH_FILE_MODEL_YOLO_STAMP)},
            {"label": "Mô hình YOLO nhận diện dị vật", "path": display_path(PATH_FILE_MODEL_YOLO_FOREIGN)},
            {
                "label": "Mô hình PatchCore",
                "message": "Hãy vào ‘Điều chỉnh master’ -> ‘Kiểm tra điểm bất thường’ hoặc ‘Kiểm tra dị vật’ để thay đổi mô hình",
            },
        ],
        "outputs": [
            {"label": "Thư mục output phán định", "path": display_path(PATH_FOLDER_OUTPUT_JUDGMENT)},
            {"label": "Thư mục output PatchCore", "path": display_path(PATH_FOLDER_IMG_COORDINATE_OUTPUT)},
        ],
    }


@router.get("/config_logs")
def get_config_logs(services=Depends(get_services)):
    """Lấy cấu hình hiện tại của hệ thống Log & Retention."""
    cfg = getattr(services, "obj_config_software", None)
    if cfg is None:
        from app.services.log.config_software import Config_SoftWare
        cfg = Config_SoftWare()
    retrain_path = (
        str(cfg.get_output_retrain_dir().resolve())
        if hasattr(cfg, "get_output_retrain_dir")
        else str(PATH_FOLDER_OUTPUT_RETRAIN.resolve())
    )
    return {
        "status": True,
        "data": cfg.to_dict(),
        "available_drives": cfg.get_arr_disk_on_pc(),
        "retrain_folder_path": retrain_path,
    }


@router.get("/config_logs/defaults")
def get_config_logs_defaults():
    """Trả về cấu hình Log & Retention mặc định (không ghi file)."""
    from app.services.log.config_software import Config_SoftWare
    return {
        "status": True,
        "data": Config_SoftWare.get_default_config(),
        "retrain_folder_path": str(PATH_FOLDER_OUTPUT_RETRAIN.resolve()),
    }


@router.post("/config_logs")
def update_config_logs(payload: dict, services=Depends(get_services)):
    """Cập nhật cấu hình lưu trữ Log và đồng bộ ngay với Manager_Log."""
    cfg = getattr(services, "obj_config_software", None)
    if cfg is None:
        from app.services.log.config_software import Config_SoftWare
        cfg = Config_SoftWare()

    # Cập nhật đường dẫn lưu log
    if "log_dir" in payload:
        cfg.set_log_dir(payload["log_dir"])
    elif "disk_select" in payload:
        cfg.set_disk_select(payload["disk_select"])

    # Cập nhật đường dẫn lưu output (app/output)
    if "output_dir" in payload:
        cfg.set_output_dir(payload["output_dir"])

    # Cập nhật thời gian lưu log hợp nhất
    if "time_save_log" in payload:
        cfg.set_time_save_log(payload["time_save_log"])
    else:
        if "time_save_img" in payload:
            cfg.set_time_save_img(payload["time_save_img"])
        if "time_save_txt" in payload:
            cfg.set_time_save_txt(payload["time_save_txt"])
        if "time_save_csv" in payload:
            cfg.set_time_save_csv(payload["time_save_csv"])

    # Các công tắc bật tắt
    if "open_img" in payload:
        cfg.set_open_img(payload["open_img"])
    if "open_txt" in payload:
        cfg.set_open_txt(payload["open_txt"])
    if "open_csv" in payload:
        cfg.set_open_csv(payload["open_csv"])
    if "open_log_cosole" in payload:
        cfg.set_open_log_cosole(payload["open_log_cosole"])
    if "open_log_print" in payload:
        cfg.set_open_log_print(payload["open_log_print"])
    if "image_save_mode" in payload:
        cfg.set_image_save_mode(payload["image_save_mode"])
    if "max_judger_workers" in payload:
        cfg.set_max_judger_workers(payload["max_judger_workers"])

    # Thu thập ảnh retrain
    if "open_retrain" in payload:
        cfg.set_open_retrain(payload["open_retrain"])
    if "retrain_inspectors" in payload:
        cfg.set_retrain_inspectors(payload["retrain_inspectors"])

    cfg.save_config_software()

    if getattr(services, "obj_manager_log", None):
        try:
            services.obj_manager_log.Init()
        except Exception as e:
            print(f"[Config_Logs] Lỗi reload Manager_Log: {e}")

    retrain_path = (
        str(cfg.get_output_retrain_dir().resolve())
        if hasattr(cfg, "get_output_retrain_dir")
        else str(PATH_FOLDER_OUTPUT_RETRAIN.resolve())
    )
    return {
        "status": True,
        "message": "Đã lưu cấu hình Log thành công",
        "data": cfg.to_dict(),
        "retrain_folder_path": retrain_path,
    }
