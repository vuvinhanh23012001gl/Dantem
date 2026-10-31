from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any


class Log_Txt:
    """Quản lý log văn bản của phần mềm:
    - Ghi log ra console (terminal)
    - Ghi log ra file xoay vòng (tránh tràn ổ cứng)
    - Tự động tạo file log mới mỗi lần phần mềm khởi động
    """

    def __init__(
        self,
        obj_folder: Any = None,
        path_folder_log: str | Path = "log_systems",
        name: str = "app",
        name_file: str | None = None,
        enable_console: bool = True,
        enable_file: bool = True,
        max_bytes: int = 20 * 1024 * 1024,  # 20 MB / file
        backup_count: int = 10,
    ):
        self.path_folder = Path(path_folder_log)
        if not name_file:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.name_file = f"system_{timestamp_str}.log"
        else:
            self.name_file = name_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        self.logger.propagate = False

        self.formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        self.handler_console: logging.StreamHandler | None = None
        self.handler_file: logging.Handler | None = None
        self.path_log: Path | None = None

        if enable_file:
            self.enable_file()

        if enable_console:
            self.enable_console()

    def enable_console(self) -> None:
        """Kích hoạt xuất log ra console."""
        if self.handler_console is None:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(self.formatter)
            self.logger.addHandler(ch)
            self.handler_console = ch

    def disable_console(self) -> None:
        """Tắt xuất log ra console."""
        if self.handler_console:
            self.logger.removeHandler(self.handler_console)
            self.handler_console = None

    def enable_file(self) -> None:
        """Kích hoạt ghi log vào file xoay vòng."""
        if self.handler_file is None:
            try:
                self.path_folder.mkdir(parents=True, exist_ok=True)
                self.path_log = self.path_folder / self.name_file
                fh = RotatingFileHandler(
                    str(self.path_log),
                    maxBytes=self.max_bytes,
                    backupCount=self.backup_count,
                    encoding="utf-8",
                )
                fh.setLevel(logging.DEBUG)
                fh.setFormatter(self.formatter)
                self.logger.addHandler(fh)
                self.handler_file = fh
            except Exception as e:
                print(f"[Log_Txt] Không thể khởi tạo FileHandler: {e}")

    def disable_file(self) -> None:
        """Tắt ghi log file và giải phóng handle."""
        if self.handler_file:
            self.logger.removeHandler(self.handler_file)
            self.handler_file.close()
            self.handler_file = None

    # Log APIs
    def debug(self, msg: str) -> None:
        self.logger.debug(str(msg))

    def info(self, msg: str) -> None:
        self.logger.info(str(msg))

    def warning(self, msg: str) -> None:
        self.logger.warning(str(msg))

    def error(self, msg: str) -> None:
        self.logger.error(str(msg))

    def critical(self, msg: str) -> None:
        self.logger.critical(str(msg))
