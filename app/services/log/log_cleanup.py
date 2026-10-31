from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
import shutil
import threading
import time
from typing import Callable

logger = logging.getLogger(__name__)


class LogCleanupWorker:
    """Worker chạy nền định kỳ quét và dọn dẹp các tệp log/ảnh cũ hơn số ngày cấu hình.

    Phục vụ chính sách Retention Policy công nghiệp để bảo vệ dung lượng ổ cứng.
    """

    def __init__(
        self,
        base_log_folder: Path | str,
        retention_days: int = 30,
        scan_interval_seconds: int = 3600,
        get_retention_days_callback: Callable[[], int] | None = None,
    ):
        self.base_log_folder = Path(base_log_folder)
        self.retention_days = max(1, int(retention_days))
        self.scan_interval_seconds = max(60, int(scan_interval_seconds))
        self.get_retention_days = get_retention_days_callback

        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Bắt đầu luồng kiểm tra định kỳ."""
        with self._lock:
            if not self._running and not self._thread:
                self._running = True
                self._thread = threading.Thread(
                    target=self._worker_loop,
                    daemon=True,
                    name="LogCleanupWorker",
                )
                self._thread.start()
                logger.info(
                    "[LogCleanup] Đã khởi động worker dọn dẹp log (Chu kỳ: %ds, Giữ lại: %d ngày).",
                    self.scan_interval_seconds,
                    self.retention_days,
                )

    def stop(self, timeout: float = 2.0) -> None:
        """Dừng luồng dọn dẹp an toàn."""
        with self._lock:
            self._running = False
            thread = self._thread
            self._thread = None

        if thread and thread.is_alive():
            thread.join(timeout=timeout)
            logger.info("[LogCleanup] Đã dừng worker dọn dẹp log.")

    def _worker_loop(self) -> None:
        """Vòng lặp chạy nền định kỳ quét thư mục."""
        # Chạy dọn dẹp một lần ngay khi khởi động
        try:
            self.cleanup_now()
        except Exception as e:
            logger.warning("[LogCleanup] Lỗi dọn dẹp khởi tạo: %s", e)

        last_run = time.time()
        while self._running:
            try:
                time.sleep(1.0)
                now = time.time()
                if now - last_run >= self.scan_interval_seconds:
                    self.cleanup_now()
                    last_run = now
            except Exception as e:
                logger.error("[LogCleanup] Lỗi trong vòng lặp dọn dẹp: %s", e)

    @classmethod
    def cleanup_folder(cls, folder: Path | str, retention_days: int = 30) -> int:
        """Phương thức tiện ích gọi trực tiếp để dọn dẹp một thư mục log."""
        worker = cls(base_log_folder=folder, retention_days=retention_days)
        res = worker.cleanup_now()
        return res.get("deleted_folders", 0)

    def cleanup_now(self, folder: Path | str | None = None, retention_days: int | None = None) -> dict[str, int] | int:
        """Thực hiện quét và dọn dẹp ngay lập tức: Xóa nguyên toàn bộ thư mục theo ngày
        (YYYY-MM-DD) nếu cũ hơn retention_days cấu hình.
        Hỗ trợ gọi cả qua instance worker.cleanup_now() lẫn class LogCleanupWorker.cleanup_now(folder, retention_days=30).
        """
        # Xử lý trường hợp được gọi trực tiếp từ Class: LogCleanupWorker.cleanup_now(folder, retention_days=30)
        if not isinstance(self, LogCleanupWorker):
            worker = LogCleanupWorker(base_log_folder=self, retention_days=retention_days or 30)
            return worker.cleanup_now()["deleted_folders"]

        target_base = Path(folder) if folder is not None else self.base_log_folder
        days = retention_days if retention_days is not None else self.retention_days
        if self.get_retention_days is not None and retention_days is None:
            try:
                days = max(1, int(self.get_retention_days()))
            except Exception:
                pass

        if not target_base.exists():
            return {"deleted_files": 0, "deleted_folders": 0}

        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        cutoff_timestamp = time.time() - (days * 86400)
        deleted_folders = 0

        # Danh sách thư mục gốc cần kiểm tra (thư mục log hiện tại và thư mục con Log nếu có)
        target_dirs = [target_base]
        sub_log = target_base / "Log"
        if sub_log.exists() and sub_log.is_dir():
            target_dirs.append(sub_log)

        for scan_dir in target_dirs:
            try:
                for item in list(scan_dir.iterdir()):
                    if item.is_dir():
                        is_old = False
                        try:
                            folder_date = datetime.strptime(item.name, "%Y-%m-%d").date()
                            if folder_date < cutoff_date:
                                is_old = True
                        except ValueError:
                            # Fallback theo st_mtime nếu tên thư mục không theo chuẩn YYYY-MM-DD
                            try:
                                if item.stat().st_mtime < cutoff_timestamp:
                                    is_old = True
                            except Exception:
                                pass

                        if is_old:
                            try:
                                shutil.rmtree(item)
                                deleted_folders += 1
                                logger.info(
                                    "[LogCleanup] Đã xóa toàn bộ thư mục log theo ngày cũ: %s",
                                    item,
                                )
                            except Exception as rm_err:
                                logger.warning(
                                    "[LogCleanup] Không thể xóa thư mục %s: %s",
                                    item,
                                    rm_err,
                                )
            except Exception as e:
                logger.warning("[LogCleanup] Lỗi quét thư mục %s: %s", scan_dir, e)

        if deleted_folders > 0:
            logger.info(
                "[LogCleanup] Hoàn tất dọn dẹp: đã xóa %d thư mục ngày cũ.",
                deleted_folders,
            )

        return {"deleted_files": 0, "deleted_folders": deleted_folders}
