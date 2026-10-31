import runpy
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


class TestPackagedPathConfig(unittest.TestCase):
    """Kiểm tra resolver đường dẫn cho cấu trúc PyInstaller onedir."""

    def _load_frozen_config(self, exe_dir: Path) -> dict:
        """Nạp path_config trong ngữ cảnh frozen giả lập.

        Input: ``exe_dir`` là thư mục phân phối có EXE và ``_internal``.
        Output: Namespace do ``runpy`` tạo từ path_config.
        Errors: Lỗi import hoặc lỗi khởi tạo thư mục được truyền lên test.
        """
        internal_dir = exe_dir / "_internal"
        executable_path = exe_dir / "WidthLineDetection.exe"
        path_config_file = Path(__file__).resolve().parents[1] / "config" / "path_config.py"
        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "executable", str(executable_path)), \
             patch.object(sys, "_MEIPASS", str(internal_dir), create=True):
            return runpy.run_path(str(path_config_file))

    def _create_distribution(self, exe_dir: Path) -> Path:
        """Tạo cấu trúc build tối thiểu để kiểm tra đường dẫn.

        Input: ``exe_dir`` là thư mục tạm làm gốc bản phân phối.
        Output: Đường dẫn ``_internal`` chứa assets và storage đã đóng gói.
        Errors: ``OSError`` nếu không tạo được thư mục hoặc file giả lập.
        """
        internal_dir = exe_dir / "_internal"
        app_dir = internal_dir / "app"
        (app_dir / "templates").mkdir(parents=True)
        (app_dir / "storage").mkdir()
        (exe_dir / "input" / "model").mkdir(parents=True)
        (exe_dir / "WidthLineDetection.exe").touch()
        return internal_dir

    def test_clean_distribution_uses_internal_storage_and_external_runtime_dirs(self) -> None:
        """Build sạch dùng storage trong _internal, input/output cạnh EXE."""
        with TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "WidthLineDetection"
            exe_dir.mkdir()
            internal_dir = self._create_distribution(exe_dir)

            paths = self._load_frozen_config(exe_dir)

            self.assertEqual(paths["BASE_DIR"], internal_dir / "app")
            self.assertEqual(paths["BASE_PATH_STORAGE"], internal_dir / "app" / "storage")
            self.assertEqual(paths["BASE_PATH_INPUT_STORAGE"], exe_dir / "input")
            self.assertEqual(paths["BASE_PATH_OUTPUT"], exe_dir / "output")

    def test_existing_external_storage_remains_an_override(self) -> None:
        """Storage cạnh EXE tiếp tục được dùng nếu đã tồn tại từ bản cũ."""
        with TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "WidthLineDetection"
            exe_dir.mkdir()
            internal_dir = self._create_distribution(exe_dir)
            external_storage = exe_dir / "storage"
            external_storage.mkdir()

            paths = self._load_frozen_config(exe_dir)

            self.assertEqual(paths["BASE_DIR"], internal_dir / "app")
            self.assertEqual(paths["BASE_PATH_STORAGE"], external_storage)


if __name__ == "__main__":
    unittest.main()