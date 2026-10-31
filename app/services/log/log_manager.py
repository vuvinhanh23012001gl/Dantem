from datetime import datetime
import logging
from pathlib import Path
from queue import Empty, Queue
import threading
import time
from typing import Any

from app.utils import Aggregate, Folder
from .config_software import Config_SoftWare
from .log_cleanup import LogCleanupWorker
from .log_csv import Log_CSV
from .log_img import Log_Img
from .log_txt import Log_Txt

logger = logging.getLogger(__name__)


class Manager_Log:
    """Quản trị viên logging trung tâm cho ứng dụng.

    Điều phối toàn bộ việc ghi log văn bản, hình ảnh, file CSV và dọn dẹp ổ đĩa
    thông qua hàng đợi bất đồng bộ Producer-Consumer (non-blocking).
    """

    def __init__(
        self,
        Config_Software: Config_SoftWare,
        choose_product: Any = None,
        product_service: Any = None,
        product_count_service: Any = None,
        queue_manager_log: Any = None,
        obj_folder: Any = None,
        obj_aggregate: Any = None,
    ):
        self.obj_Config_SoftWare = Config_Software
        self.obj_choose_product = choose_product
        self.obj_product_service = product_service
        self.obj_product_count_service = product_count_service
        self.obj_folder = obj_folder or Folder()
        self.obj_aggregate = obj_aggregate or Aggregate()

        if queue_manager_log is not None:
            self.queue_manager_log = queue_manager_log
        else:
            self.queue_manager_log = Queue(maxsize=500)

        self.thread: threading.Thread | None = None
        self.thread_running: bool = False
        self._lock = threading.Lock()

        self.obj_Log_Txt: Log_Txt | None = None
        self.obj_Log_Img: Log_Img | None = None
        self.obj_Log_Csv: Log_CSV | None = None
        self.obj_cleaner: LogCleanupWorker | None = None

        self.Init()

    def get_current_product_name(self) -> str:
        """Lấy tên chuẩn hóa của sản phẩm đang chọn."""
        try:
            if self.obj_choose_product and self.obj_product_service:
                id_select = self.obj_choose_product.get_choose_product()
                product_id = getattr(id_select, "data", None)
                if product_id is not None:
                    product_res = self.obj_product_service.get_product_by_id(product_id)
                    product_data = getattr(product_res, "data", None)
                    if product_data:
                        raw_name = getattr(product_data, "name", str(product_data))
                        norm_name = Aggregate.normalize_folder_name(raw_name)
                        if norm_name:
                            return norm_name
        except Exception as e:
            logger.debug("[Manager_Log] Không thể lấy tên sản phẩm: %s", e)
        return "UNKNOWN_PRODUCT"

    def calculate_pass_rate(self) -> str:
        """Tính tỷ lệ phán định % từ product_count_service (OK / Total * 100)."""
        try:
            if self.obj_product_count_service:
                counts = self.obj_product_count_service.get_counts()
                ok = counts.get("ok", 0)
                total = counts.get("total", 0)
                if total > 0:
                    rate = (ok / total) * 100.0
                    return f"{rate:.2f}%"
        except Exception as e:
            logger.debug("[Manager_Log] Lỗi tính tỷ lệ phán định: %s", e)
        return "0.00%"

    def Init(self) -> None:
        """Khởi tạo và cấu hình các thành phần ghi log."""
        product_name = self.get_current_product_name()
        paths = self.obj_Config_SoftWare.create_path_by_name_product(product_name)

        open_log_txt = self.obj_Config_SoftWare.get_open_txt()
        open_log_console = self.obj_Config_SoftWare.get_open_log_cosole()
        open_log_csv = self.obj_Config_SoftWare.get_open_csv()
        open_log_img = self.obj_Config_SoftWare.get_open_img()
        img_save_mode = self.obj_Config_SoftWare.get_image_save_mode()

        # 1. Khởi tạo Log Text (Mỗi lần bật phần mềm tạo 1 file mới có timestamp)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.obj_Log_Txt = Log_Txt(
            path_folder_log=paths["path_log_txt"],
            name_file=f"system_{timestamp_str}.log",
            enable_file=open_log_txt,
            enable_console=open_log_console,
        )

        # 2. Khởi tạo Log Img (Lưu phẳng trong Log/<Date>/Product_<Name>/Log_img/)
        self.obj_Log_Img = Log_Img(
            path_img=paths["path_log_img"],
            open_log_img=open_log_img,
            save_mode=img_save_mode,
        )

        # 3. Khởi tạo Log CSV (Lưu trong Log/<Date>/Product_<Name>/Log_csv/)
        self.obj_Log_Csv = Log_CSV(
            folder=paths["path_log_csv"],
            enable=open_log_csv,
            daily_rolling=False,
        )

        # 4. Khởi tạo Worker dọn dẹp đĩa cứng
        self.obj_cleaner = LogCleanupWorker(
            base_log_folder=paths["path_base"],
            retention_days=self.obj_Config_SoftWare.get_time_save_log(),
            scan_interval_seconds=3600,
            get_retention_days_callback=self.obj_Config_SoftWare.get_time_save_log,
        )

        # Tự động khởi động luồng tiêu thụ nếu có ít nhất 1 loại log được bật
        if any([open_log_txt, open_log_csv, open_log_img]):
            self.start_thread()
            if self.obj_cleaner:
                self.obj_cleaner.start()

    def start_thread(self) -> None:
        """Bắt đầu luồng ghi log nền."""
        with self._lock:
            if not self.thread_running:
                self.thread_running = True
                self.thread = threading.Thread(
                    target=self._log_thread_loop,
                    daemon=True,
                    name="ManagerLogWorker",
                )
                self.thread.start()
                logger.info("[Manager_Log] Đã mở luồng xử lý nhận log ngầm.")

    def _fetch_queue_item(self) -> dict[str, Any] | None:
        """Đọc an toàn từ queue_manager_log (hỗ trợ cả Worker và Queue chuẩn)."""
        if hasattr(self.queue_manager_log, "get_timeout"):
            return self.queue_manager_log.get_timeout(timeout=0.5)
        elif hasattr(self.queue_manager_log, "get"):
            try:
                return self.queue_manager_log.get(timeout=0.5)
            except (Empty, TypeError):
                try:
                    return self.queue_manager_log.get()
                except Exception:
                    return None
        return None

    def _log_thread_loop(self) -> None:
        """Vòng lặp tiêu thụ dữ liệu từ queue_manager_log mà không chiếm dụng CPU."""
        while self.thread_running:
            try:
                data = self._fetch_queue_item()
                if not data or not isinstance(data, dict):
                    time.sleep(0.05)
                    continue

                type_data = data.get("type", None)
                msg = data.get("msg", None)

                # 1. Ghi log hệ thống / console
                if type_data == "system" and self.obj_Log_Txt:
                    level = str(data.get("level", "infor")).lower()
                    if level in ("infor", "info"):
                        self.obj_Log_Txt.info(str(msg))
                    elif level == "warning":
                        self.obj_Log_Txt.warning(str(msg))
                    elif level == "debug":
                        self.obj_Log_Txt.debug(str(msg))
                    elif level == "error":
                        self.obj_Log_Txt.error(str(msg))
                    elif level == "critical":
                        self.obj_Log_Txt.critical(str(msg))

                # 2. Ghi hình ảnh phán định (OK_... / NG_...)
                elif type_data == "image" and self.obj_Log_Img:
                    file_name = data.get("file_name")
                    if not file_name:
                        now = datetime.now()
                        file_name = f"img_{now.strftime('%y%m%d_%H%M%S')}_{now.microsecond // 1000:03d}"
                    status = data.get("status", "OK")
                    product_name = data.get("product_name") or self.get_current_product_name()
                    source_file = data.get("source_file")
                    self.obj_Log_Img.save(
                        img=msg,
                        file_name=file_name,
                        status=status,
                        product_name=product_name,
                        source_file=source_file,
                    )

                # 3. Ghi kết quả chi tiết từng item vào file CSV session (Ảnh 2)
                elif type_data in ("csv", "csv_item") and self.obj_Log_Csv:
                    if isinstance(msg, dict):
                        session_id = data.get("session_id") or msg.get("session_id", "unknown_session")
                        self.obj_Log_Csv.write_session_item(session_id, msg)

                # 4. Ghi tổng kết session vào file CSV tổng summary_daily.csv (Ảnh 1)
                elif type_data in ("csv_summary", "csv_session") and self.obj_Log_Csv:
                    if isinstance(msg, dict):
                        # Tự động bổ sung tỷ lệ phán định và tên sản phẩm nếu chưa có
                        if not msg.get("Tỷ lệ phán định") and not msg.get("pass_rate"):
                            msg["Tỷ lệ phán định"] = self.calculate_pass_rate()
                        if not msg.get("Product") and not msg.get("product_name"):
                            msg["Product"] = self.get_current_product_name()

                        self.obj_Log_Csv.write_summary(msg)

            except Exception as e:
                logger.error("[Manager_Log] Lỗi xử lý bản ghi log: %s", e)

    def stop_log_thread(self, timeout: float = 2.0) -> None:
        """Dừng luồng ghi log và worker dọn dẹp an toàn."""
        with self._lock:
            self.thread_running = False
            thread = self.thread
            self.thread = None

        if thread and thread.is_alive():
            thread.join(timeout=timeout)

        if self.obj_cleaner:
            self.obj_cleaner.stop(timeout=timeout)

        if self.obj_Log_Txt:
            self.obj_Log_Txt.disable_file()