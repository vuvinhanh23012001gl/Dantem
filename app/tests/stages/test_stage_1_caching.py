import unittest
from unittest.mock import MagicMock, patch
from dataclasses import replace

from app.stages.stage_1_preprocess import StagePreprocess, PreparedProduct
from app.container import EnumMode
from app.core.context import RuntimePipelineState


class TestStage1Caching(unittest.TestCase):
    """Kiểm tra chuyên sâu cơ chế Caching dữ liệu trong RAM và Invalidation của Stage 1 Preprocess."""

    def setUp(self) -> None:
        self.mock_services = MagicMock()
        self.mock_services.send_judgment_log = MagicMock()
        self.mock_services.set_mode = MagicMock()
        self.mock_services.runtime_state.set_pipeline_state = MagicMock()

        self.sample_prepared = PreparedProduct(
            product_id="101",
            frames=[
                {
                    "frame_id": "0",
                    "points": [
                        {"point_id": "0", "x": 100, "y": 200, "z": 300, "judgment": {}},
                        {"point_id": "1", "x": 150, "y": 250, "z": 350, "judgment": {}},
                    ],
                    "calibration": {"is_calibrated": True, "scale_mm_per_pixel": 0.05},
                }
            ],
            frame_calibrations={"0": {"is_calibrated": True, "scale_mm_per_pixel": 0.05}},
            scale_mm_per_pixel=0.05,
            session_id="session_initial",
            number_step=2,
        )

    @patch.object(StagePreprocess, "_load_product_data")
    @patch.object(StagePreprocess, "_has_files_changed_on_disk", return_value=False)
    def test_preload_on_init(self, mock_has_changed, mock_load):
        """Khởi tạo StagePreprocess phải tự động preload dữ liệu vào RAM."""
        mock_load.return_value = self.sample_prepared

        stage = StagePreprocess(self.mock_services)

        self.assertEqual(mock_load.call_count, 1)
        self.assertIsNotNone(stage._cached_product)
        self.assertEqual(stage._cached_product.product_id, "101")
        self.assertFalse(stage._is_dirty)

    @patch.object(StagePreprocess, "_load_product_data")
    @patch.object(StagePreprocess, "_has_files_changed_on_disk", return_value=False)
    def test_run_reuses_ram_cache_without_reading_disk(self, mock_has_changed, mock_load):
        """Mỗi chu kỳ chạy (Reset) lấy dữ liệu từ RAM, cấp phát session mới mà KHÔNG đọc lại đĩa."""
        mock_load.return_value = self.sample_prepared
        stage = StagePreprocess(self.mock_services)
        self.assertEqual(mock_load.call_count, 1)  # Đã load 1 lần khi preload

        # Chu kỳ 1
        product_cycle_1 = stage.run()
        self.assertEqual(mock_load.call_count, 1)  # Không load lại từ đĩa
        self.assertEqual(product_cycle_1.product_id, "101")
        self.assertTrue(product_cycle_1.session_id.startswith("session_"))
        self.mock_services.set_mode.assert_called_with(EnumMode.MODE_TRANSFORM)
        self.assertEqual(self.mock_services.prepared_product, product_cycle_1)

        # Chu kỳ 2 (Mô phỏng bấm Reset lần 2)
        product_cycle_2 = stage.run()
        self.assertEqual(mock_load.call_count, 1)  # Vẫn không đọc lại từ đĩa
        self.assertEqual(product_cycle_2.product_id, "101")
        self.assertTrue(product_cycle_2.session_id.startswith("session_"))
        # Hai chu kỳ phải có session_id độc nhất khác nhau
        self.assertNotEqual(product_cycle_1.session_id, product_cycle_2.session_id)
        # Nhưng dữ liệu cấu hình tọa độ điểm phải hoàn toàn nhất quán
        self.assertEqual(product_cycle_1.frames, product_cycle_2.frames)
        self.assertEqual(product_cycle_1.number_step, product_cycle_2.number_step)

    @patch.object(StagePreprocess, "_load_product_data")
    @patch.object(StagePreprocess, "_has_files_changed_on_disk", return_value=False)
    def test_mark_dirty_triggers_reload_and_notifies_ui(self, mock_has_changed, mock_load):
        """Khi có thay đổi từ giao diện UI (mark_dirty), hệ thống tự động reload cấu hình mới vào RAM."""
        mock_load.return_value = self.sample_prepared
        stage = StagePreprocess(self.mock_services)
        self.assertEqual(mock_load.call_count, 1)

        # Giả lập người dùng thay đổi sản phẩm trên UI thành 102
        new_prepared = replace(self.sample_prepared, product_id="102", number_step=5)
        mock_load.return_value = new_prepared

        stage.mark_dirty("select_product_new")

        # Phải được reload lại ngay lập tức
        self.assertEqual(mock_load.call_count, 2)
        self.assertEqual(stage._cached_product.product_id, "102")
        self.assertEqual(stage._cached_product.number_step, 5)

        # Thông báo phải được gửi lên ô log của giao diện
        self.mock_services.send_judgment_log.assert_called()
        last_log = self.mock_services.send_judgment_log.call_args[0][0]
        self.assertIn("Đã cập nhật cấu hình vào RAM", last_log)
        self.assertIn("102", last_log)

    @patch.object(StagePreprocess, "_load_product_data")
    @patch.object(StagePreprocess, "_has_files_changed_on_disk")
    def test_mtime_guard_auto_reloads_when_file_modified_externally(self, mock_has_changed, mock_load):
        """Nếu file JSON bị chỉnh sửa ngoài Explorer (mtime đổi), chu kỳ kế tiếp tự động reload."""
        mock_has_changed.return_value = False
        mock_load.return_value = self.sample_prepared
        stage = StagePreprocess(self.mock_services)
        self.assertEqual(mock_load.call_count, 1)

        # Lần chạy 1: mtime chưa đổi
        stage.run()
        self.assertEqual(mock_load.call_count, 1)

        # Giả lập file trên đĩa bị ai đó sửa ngoài Notepad (mtime đổi)
        mock_has_changed.return_value = True
        stage.run()
        # Phải tự động phát hiện và reload lại từ đĩa
        self.assertEqual(mock_load.call_count, 2)


if __name__ == "__main__":
    unittest.main()
