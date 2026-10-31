import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import cv2
import numpy as np

from app.services.log.log_img import Log_Img
from app.services.log.log_manager import Manager_Log
from app.services.log.config_software import Config_SoftWare
from app.stages.stage_2_transform import StageTransform, InspectionTaskItem
from app.judger.judment import Judment


class TestStorageOptimization(unittest.TestCase):
    """Kiểm tra toàn diện 3 giải pháp tối ưu hóa Disk I/O:
    1. Async Output Saver (Stage 2)
    2. Async Retrain Saver (Judment)
    3. Fast JPEG Copy (Log_Img)
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_solution_3_fast_jpeg_copy_when_source_exists(self):
        """Giải pháp 3: Khi có source_file hợp lệ, Log_Img copy trực tiếp thay vì encode JPEG."""
        log_img_dir = self.temp_path / "Log_img"
        log_img = Log_Img(path_img=log_img_dir, open_log_img=True, save_mode="ALL")

        # Tạo file ảnh nguồn giả lập
        source_file = self.temp_path / "source_judgment.jpg"
        source_file.write_bytes(b"DUMMY_JPEG_CONTENT_12345")

        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)

        # Mock cv2.imwrite để kiểm chứng nó KHÔNG được gọi khi copy thành công
        with patch("cv2.imwrite") as mock_imwrite:
            saved_path = log_img.save(
                img=dummy_img,
                file_name="test_copy",
                status="OK",
                source_file=source_file,
            )
            self.assertIsNotNone(saved_path)
            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.read_bytes(), b"DUMMY_JPEG_CONTENT_12345")
            mock_imwrite.assert_not_called()

    def test_solution_3_fallback_to_imwrite_when_source_missing(self):
        """Giải pháp 3 fallback: Khi không có source_file hoặc file không tồn tại, Log_Img gọi cv2.imwrite bình thường."""
        log_img_dir = self.temp_path / "Log_img"
        log_img = Log_Img(path_img=log_img_dir, open_log_img=True, save_mode="ALL")

        dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)

        saved_path = log_img.save(
            img=dummy_img,
            file_name="test_fallback",
            status="OK",
            source_file=self.temp_path / "non_existing.jpg",
        )
        self.assertIsNotNone(saved_path)
        self.assertTrue(saved_path.exists())
        self.assertTrue(saved_path.stat().st_size > 0)

    def test_solution_1_async_output_saver(self):
        """Giải pháp 1: StageTransform lưu file output trên luồng nền mà không block worker."""
        mock_services = MagicMock()
        mock_services.runtime_state.is_stop_requested.return_value = False
        stage = StageTransform(services=mock_services)

        # Tạo luồng saver ngầm
        import threading
        saver_thread = threading.Thread(
            target=stage._output_saver_worker,
            daemon=True,
        )
        stage._output_saver_thread = saver_thread
        saver_thread.start()

        # Dữ liệu giả lập
        prepared = MagicMock()
        prepared.session_id = "session_opt_test"
        prepared.product_id = "prod_99"

        frame = {"frame_id": "0"}
        point = {"point_id": "1"}
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        summary = {
            "overall": True,
            "status": "OK",
            "judgment_image": img,
            "inspectors": {},
        }

        # Override session item dir trỏ về temp
        target_item_dir = self.temp_path / "output_test" / "item_1"
        stage._session_item_dir = MagicMock(return_value=target_item_dir)

        # Gọi _save_judgment_result: phải trả về URL ngay
        url = stage._save_judgment_result(
            image=img,
            prepared=prepared,
            frame_id="0",
            point_id="1",
            summary=summary,
        )
        self.assertIn("judgment.jpg", url)

        # Chờ flush hàng đợi ngầm
        stage._output_save_queue.put(None)
        saver_thread.join(timeout=3.0)

        # Xác nhận các file đã được ghi xuống đĩa chính xác
        self.assertTrue((target_item_dir / "original.jpg").exists())
        self.assertTrue((target_item_dir / "judgment.jpg").exists())
        self.assertTrue((target_item_dir / "result.json").exists())

    def test_solution_2_async_retrain_saver(self):
        """Giải pháp 2: Judment hỗ trợ lưu ảnh retrain ngầm khi async_save=True."""
        dummy_img = np.zeros((30, 30, 3), dtype=np.uint8)
        original_root = Judment.RETRAIN_OUTPUT_DIR
        Judment.RETRAIN_OUTPUT_DIR = self.temp_path / "retrain"

        try:
            # Gọi với async_save=True
            Judment._save_training_inputs(
                image=dummy_img,
                inspector_name="ForeignObjectInspector",
                define_args=(),
                async_save=True,
            )

            # Đợi flush luồng nền
            Judment.flush_retrain_queue()

            # Kiểm tra ảnh retrain đã được ghi xuống thư mục
            saved_files = list((self.temp_path / "retrain").rglob("*.jpg"))
            self.assertGreaterEqual(len(saved_files), 1)
        finally:
            Judment.RETRAIN_OUTPUT_DIR = original_root


if __name__ == "__main__":
    unittest.main()
