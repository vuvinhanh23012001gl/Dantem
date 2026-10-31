# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Title      : Check OIL bivn / Module config software
# Description:  Module config software
# Author     : Vu Vinh Anh
# Email      : anh.vu@example.com
# Created    : 2025-06-30
# Version    : 0.1
# License    : MIT
# -----------------------------------------------------------------------------
# from pathlib import Path
# import sys
# sys.path.append(str(Path(__file__).resolve().parents[3]))
# # import psutil
# # for p in psutil.disk_partitions():
# #     print(p.device, p.mountpoint)

from pathlib import Path
from datetime import datetime
from app.config import PATH_CONFIG_SOFTWARE, PATH_DEFAULT_LOG_DISK, PATH_FOLDER_OUTPUT
from app.utils import Folder

class Config_SoftWare:
    """Quản lý cấu hình phần mềm & đường dẫn log"""

    # ====== TIME CONFIG ======
    SET_TIME_DEFAULT_SAVE_LOG_IMG = 30
    SET_TIME_DEFAULT_SAVE_LOG_TXT = 30
    SET_TIME_DEFAULT_SAVE_LOG_EXCELL = 30

    # ====== APP INFO ======
    NAME = "App_Line_Measurement_Check"

    # ====== FOLDER NAME ======
    NAME_FOLDER_LOG = "Log"
    NAME_FOLDER_LOG_TXT = "log_systems"
    NAME_FOLDER_LOG_CSV = "log_csv"
    NAME_FOLDER_LOG_IMG = "log_img"

    # ====== BASE PATH ======
    DISK_SAVE = PATH_DEFAULT_LOG_DISK

    # ====== DATE ======
    DATE_NOW = datetime.now().strftime("%d-%m-%Y")

    # ====== PATH CONFIG ======
    DEFAULT_PRODUCT = "UNKNOWN_PRODUCT"
    PATH_FOLDER_LOG = DISK_SAVE / NAME / NAME_FOLDER_LOG / f"date_{DATE_NOW}"

    PATH_SAVE_FOLDER_LOG_IMG = PATH_FOLDER_LOG / DEFAULT_PRODUCT / NAME_FOLDER_LOG_IMG
    PATH_SAVE_FOLDER_LOG_TXT = PATH_FOLDER_LOG / DEFAULT_PRODUCT / NAME_FOLDER_LOG_TXT
    PATH_SAVE_FOLDER_LOG_CSV = PATH_FOLDER_LOG / DEFAULT_PRODUCT / NAME_FOLDER_LOG_CSV

    # ====== RETRAIN INSPECTORS LIST ======
    DEFAULT_RETRAIN_INSPECTORS = {
        "AnomalyPointInspector": True,
        "ForeignObjectInspector": True,
        "StampItemInspector": True,
    }

    def __init__(self):
        self.path_config_software = Folder.get_or_create_json_by_path(PATH_CONFIG_SOFTWARE)
        self.data_read_head_config = Folder.read_json_from_file(self.path_config_software)
        self.path_file_config = self.path_config_software

        # Đường dẫn thư mục lưu log (mặc định C:\Log)
        raw_log_dir = self.data_read_head_config.get("log_dir")
        if not raw_log_dir:
            disk = self.data_read_head_config.get("disk_select", Config_SoftWare.DISK_SAVE)
            raw_log_dir = str(Path(disk) / Config_SoftWare.NAME_FOLDER_LOG)
        self.log_dir = str(raw_log_dir)
        self.disk_select = self.data_read_head_config.get("disk_select", Config_SoftWare.DISK_SAVE)

        # Đường dẫn thư mục lưu Output (app/output)
        raw_output_dir = self.data_read_head_config.get("output_dir")
        if not raw_output_dir:
            raw_output_dir = str(PATH_FOLDER_OUTPUT.resolve())
        self.output_dir = str(raw_output_dir)

        # Thời gian lưu log duy nhất (ngày)
        self.time_save_log = int(
            self.data_read_head_config.get(
                "time_save_log",
                self.data_read_head_config.get("time_save_img", 30)
            )
        )
        self.time_save_img = self.time_save_log
        self.time_save_txt = self.time_save_log
        self.time_save_csv = self.time_save_log

        # Các switch bật/tắt kênh log
        self.open_img = bool(self.data_read_head_config.get("open_img", True))
        self.open_txt = bool(self.data_read_head_config.get("open_txt", True))
        self.open_csv = bool(self.data_read_head_config.get("open_csv", True))
        self.open_log_print = bool(self.data_read_head_config.get("open_log_print", True))
        self.open_log_cosole = bool(self.data_read_head_config.get("open_log_cosole", True))
        self.image_save_mode = str(self.data_read_head_config.get("image_save_mode", "ALL"))
        raw_workers = self.data_read_head_config.get("max_judger_workers", 5)
        try:
            self.max_judger_workers = max(1, min(10, int(raw_workers)))
        except (ValueError, TypeError):
            self.max_judger_workers = 5

        # Thu thập ảnh huấn luyện (Retrain Images)
        self.open_retrain = bool(self.data_read_head_config.get("open_retrain", False))
        raw_retrain = self.data_read_head_config.get("retrain_inspectors", {})
        self.retrain_inspectors = dict(Config_SoftWare.DEFAULT_RETRAIN_INSPECTORS)
        if isinstance(raw_retrain, dict):
            if (
                "AnomalyPointInspector" not in raw_retrain
                and "EndChippingInspector" in raw_retrain
            ):
                self.retrain_inspectors["AnomalyPointInspector"] = bool(
                    raw_retrain["EndChippingInspector"]
                )
            for k, v in raw_retrain.items():
                if k in self.retrain_inspectors:
                    self.retrain_inspectors[k] = bool(v)

    def get_base_log_dir(self) -> Path:
        """Trả về đường dẫn gốc của thư mục Log theo cấu hình người dùng.
        Đảm bảo cấu trúc thư mục luôn chứa folder Log làm gốc cho các thư mục ngày.
        """
        try:
            # Hỗ trợ tương thích nếu disk_select được gán trực tiếp hoặc cấu hình
            if self.disk_select and Path(self.disk_select) != Path(Config_SoftWare.DISK_SAVE) and str(self.disk_select) not in str(self.log_dir):
                p = Path(self.disk_select)
            else:
                p = Path(self.log_dir)
            if p.name == "Log":
                return p
            return p / "Log"
        except Exception:
            return Path(Config_SoftWare.DISK_SAVE) / Config_SoftWare.NAME_FOLDER_LOG

    def get_enabled_retrain_inspectors(self) -> set[str]:
        """Trả về tập hợp các inspector được phép lưu ảnh retrain.
        Nếu master switch open_retrain tắt thì trả về rỗng."""
        if not self.open_retrain:
            return set()
        return {k for k, v in self.retrain_inspectors.items() if v}

    def create_path_by_name_product(self, name_product: str | None = None) -> dict[str, Path]:
        """Tạo cây thư mục log theo cấu trúc:
        Log / YYYY-MM-DD / Log_txt
        Log / YYYY-MM-DD / Product_<Tên_Sản_Phẩm> / Log_img
        Log / YYYY-MM-DD / Product_<Tên_Sản_Phẩm> / Log_csv / session
        """
        raw_name = str(name_product).strip() if name_product else Config_SoftWare.DEFAULT_PRODUCT
        if not raw_name:
            raw_name = Config_SoftWare.DEFAULT_PRODUCT

        # Chuẩn hóa tên thư mục Product_<name>
        if not raw_name.startswith("Product_"):
            product_folder = f"Product_{raw_name}"
        else:
            product_folder = raw_name

        date_str = datetime.now().strftime("%Y-%m-%d")
        base_dir = self.get_base_log_dir()
        date_folder = base_dir / date_str
        log_txt_folder = date_folder / "Log_txt"
        product_dir = date_folder / product_folder
        log_img_folder = product_dir / "Log_img"
        log_csv_folder = product_dir / "Log_csv"
        log_csv_session_folder = log_csv_folder / "session"

        return {
            "path_base": base_dir,
            "path_date": date_folder,
            "path_log_txt": log_txt_folder,
            "path_product": product_dir,
            "path_log_img": log_img_folder,
            "path_log_csv": log_csv_folder,
            "path_log_csv_session": log_csv_session_folder,
            "product_name": raw_name,
        }

    @classmethod
    def get_default_config(cls) -> dict:
        """Trả về cấu hình Log mặc định do backend định nghĩa (không đọc file)."""
        default_days = 30
        return {
            "log_dir": str(Path(cls.DISK_SAVE) / cls.NAME_FOLDER_LOG),
            "output_dir": str(PATH_FOLDER_OUTPUT.resolve()),
            "time_save_log": default_days,
            "time_save_img": default_days,
            "time_save_txt": default_days,
            "time_save_csv": default_days,
            "disk_select": str(cls.DISK_SAVE),
            "open_img": True,
            "open_txt": True,
            "open_csv": True,
            "open_log_print": True,
            "open_log_cosole": True,
            "image_save_mode": "ALL",
            "max_judger_workers": 5,
            "open_retrain": False,
            "retrain_inspectors": dict(cls.DEFAULT_RETRAIN_INSPECTORS),
        }

    def to_dict(self):
        return {
            "log_dir": str(self.log_dir),
            "output_dir": str(self.output_dir),
            "time_save_log": self.time_save_log,
            "time_save_img": self.time_save_log,
            "time_save_txt": self.time_save_log,
            "time_save_csv": self.time_save_log,
            "disk_select": str(self.disk_select),
            "open_img": self.open_img,
            "open_txt": self.open_txt,
            "open_csv": self.open_csv,
            "open_log_print": self.open_log_print,
            "open_log_cosole": self.open_log_cosole,
            "image_save_mode": self.image_save_mode,
            "max_judger_workers": self.max_judger_workers,
            "open_retrain": self.open_retrain,
            "retrain_inspectors": self.retrain_inspectors,
        }

    def get_output_dir(self) -> str:
        return self.output_dir

    def set_output_dir(self, value: str | Path) -> None:
        if value:
            p = Path(value).resolve()
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            self.output_dir = str(p)

    def get_output_judgment_dir(self) -> Path:
        p = Path(self.output_dir) / "judgment"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_output_retrain_dir(self) -> Path:
        p = Path(self.output_dir) / "retrain"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_output_patch_core_dir(self) -> Path:
        p = Path(self.output_dir) / "patch_core"
        p.mkdir(parents=True, exist_ok=True)
        return p



    def get_max_judger_workers(self) -> int:
        return self.max_judger_workers

    def set_max_judger_workers(self, value: int) -> None:
        try:
            val = int(value)
            self.max_judger_workers = max(1, min(10, val))
        except (ValueError, TypeError):
            self.max_judger_workers = 5

    def get_log_dir(self) -> str:
        return self.log_dir

    def set_log_dir(self, value: str | Path) -> None:
        if value:
            self.log_dir = str(value).strip()

    def get_time_save_log(self) -> int:
        return self.time_save_log

    def set_time_save_log(self, value: int) -> None:
        try:
            val = int(value)
            if val <= 0:
                val = 30
            self.time_save_log = val
            self.time_save_img = val
            self.time_save_txt = val
            self.time_save_csv = val
        except Exception:
            pass

    def get_open_retrain(self) -> bool:
        return self.open_retrain

    def set_open_retrain(self, value: bool) -> None:
        self.open_retrain = bool(value)

    def get_retrain_inspectors(self) -> dict[str, bool]:
        return self.retrain_inspectors

    def set_retrain_inspectors(self, value: dict) -> None:
        if isinstance(value, dict):
            if (
                "AnomalyPointInspector" not in value
                and "EndChippingInspector" in value
            ):
                self.retrain_inspectors["AnomalyPointInspector"] = bool(
                    value["EndChippingInspector"]
                )
            for k, v in value.items():
                if k in self.retrain_inspectors:
                    self.retrain_inspectors[k] = bool(v)

    def set_retrain_inspector_status(self, name: str, enabled: bool) -> None:
        if name in self.retrain_inspectors:
            self.retrain_inspectors[name] = bool(enabled)

    def save_config_software(self):
        Folder.write_json_in_file(self.path_file_config, self.to_dict())

    def get_time_save_img(self):
        return self.time_save_img

    def set_time_save_img(self, value):
        try:
            value = int(value)
            if value <= 0:
                value = Config_SoftWare.SET_TIME_DEFAULT_SAVE_LOG_IMG
        except (ValueError, TypeError):
            value = Config_SoftWare.SET_TIME_DEFAULT_SAVE_LOG_IMG
        self.time_save_img = value

    def get_time_save_txt(self):
        return self.time_save_txt

    def set_time_save_txt(self, value):
        try:
            value = int(value)
            if value <= 0:
                value = Config_SoftWare.SET_TIME_DEFAULT_SAVE_LOG_TXT
        except (ValueError, TypeError):
            value = Config_SoftWare.SET_TIME_DEFAULT_SAVE_LOG_TXT
        self.time_save_txt = value

    def get_time_save_csv(self):
        return self.time_save_csv

    def set_time_save_csv(self, value):
        try:
            value = int(value)
            if value <= 0:
                value = Config_SoftWare.SET_TIME_DEFAULT_SAVE_LOG_EXCELL
        except (ValueError, TypeError):
            value = Config_SoftWare.SET_TIME_DEFAULT_SAVE_LOG_EXCELL

        self.time_save_csv = value

    def get_image_save_mode(self):
        return self.image_save_mode

    def set_image_save_mode(self, value):
        self.image_save_mode = str(value)

    def get_disk_select(self):
        return self.disk_select

    def set_disk_select(self, value):
        try:
            self.disk_select = Path(value)
            self.log_dir = str(Path(value) / Config_SoftWare.NAME_FOLDER_LOG)
        except (TypeError, ValueError, OSError):
            self.disk_select = Config_SoftWare.PATH_SAVE_FOLDER_LOG_CSV

    def get_open_img(self):
        return self.open_img

    def set_open_img(self, value):
        self.open_img = bool(value)

    def get_open_csv(self):
        return self.open_csv

    def set_open_csv(self, value):
        self.open_csv = bool(value)

    def get_open_txt(self):
        return self.open_txt

    def set_open_txt(self, value):
        self.open_txt = bool(value)

    def get_open_log_print(self):
        return self.open_log_print

    def set_open_log_print(self, value):
        self.open_log_print = bool(value)

    def get_open_log_cosole(self):
        return self.open_log_cosole

    def set_open_log_cosole(self, value):
        self.open_log_cosole = bool(value)

    def get_arr_disk_on_pc(self):
        """Hàm trả về list rỗng nếu không"""
        return Folder.list_drives()


class Change_Disk:
    def __init__(self, obj_config_softWare: Config_SoftWare):
        self.obj_config_softWare = obj_config_softWare

    def arr_disk_on_pc(self):
        return Folder.list_drives()

    def found_currently_selecting(self, disk):
        """Kiểm tra ổ này có đang được chọn
        trả về 0 nếu tồn tại nhưng chưa được chọn
        trả về 1 nếu tồn tại và không được chọn
        trả vê -1 nếu không tồn tại
        """
        arr_disk = self.arr_disk_on_pc()
        if disk in arr_disk:
            print("Tìm thấy ổ")
            disk_current = self.obj_config_softWare.get_disk_select()
            if disk == disk_current:
                print("Ổ này đang được chọn")
                return 1, "Select"
            return 0, "DisSlect"
        else:
            print("Không tìm thấy ổ trong danh sách")
            return -1, "FoundDisk"
