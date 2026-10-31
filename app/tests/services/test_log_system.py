import csv
from datetime import datetime
from pathlib import Path
import tempfile
import time
import unittest
import numpy as np
from unittest.mock import patch

from app.services.log.log_csv import Log_CSV, SUMMARY_DAILY_HEADER, SESSION_DETAIL_HEADER
from app.services.log.log_img import Log_Img
from app.services.log.log_txt import Log_Txt
from app.services.log.log_cleanup import LogCleanupWorker
from app.services.log.config_software import Config_SoftWare
from app.services.log.log_manager import Manager_Log


class DummyProductCountService:
    def get_counts(self):
        return {"ok": 95, "ng": 5, "total": 100}


class TestLogSystem(unittest.TestCase):
    def test_legacy_retrain_setting_migrates_to_anomaly_point(self):
        with patch(
            "app.services.log.config_software.Folder.get_or_create_json_by_path",
            return_value=Path("legacy-config.json"),
        ), patch(
            "app.services.log.config_software.Folder.read_json_from_file",
            return_value={
                "retrain_inspectors": {
                    "EndChippingInspector": False,
                    "ForeignObjectInspector": False,
                }
            },
        ):
            config = Config_SoftWare()

        self.assertFalse(config.get_retrain_inspectors()["AnomalyPointInspector"])
        self.assertFalse(config.get_retrain_inspectors()["ForeignObjectInspector"])
        self.assertNotIn("EndChippingInspector", config.to_dict()["retrain_inspectors"])

    def test_new_retrain_setting_takes_precedence_over_legacy_setting(self):
        with patch(
            "app.services.log.config_software.Folder.get_or_create_json_by_path",
            return_value=Path("legacy-config.json"),
        ), patch(
            "app.services.log.config_software.Folder.read_json_from_file",
            return_value={
                "retrain_inspectors": {
                    "EndChippingInspector": False,
                    "AnomalyPointInspector": True,
                }
            },
        ):
            config = Config_SoftWare()

        self.assertTrue(config.get_retrain_inspectors()["AnomalyPointInspector"])

    def test_new_log_folder_structure(self):
        """Kiểm tra sinh đúng cây thư mục: Log/YYYY-MM-DD/Log_txt và Log/YYYY-MM-DD/Product_xxx/"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config_SoftWare()
            config.disk_select = Path(temp_dir)
            paths = config.create_path_by_name_product("vinhanh")

            date_str = datetime.now().strftime("%Y-%m-%d")
            expected_base = Path(temp_dir) / "Log"
            expected_date = expected_base / date_str
            expected_txt = expected_date / "Log_txt"
            expected_product = expected_date / "Product_vinhanh"
            expected_img = expected_product / "Log_img"
            expected_csv = expected_product / "Log_csv"
            expected_session = expected_csv / "session"

            self.assertEqual(paths["path_base"], expected_base)
            self.assertEqual(paths["path_log_txt"], expected_txt)
            self.assertEqual(paths["path_product"], expected_product)
            self.assertEqual(paths["path_log_img"], expected_img)
            self.assertEqual(paths["path_log_csv"], expected_csv)
            self.assertEqual(paths["path_log_csv_session"], expected_session)

    def test_log_txt_timestamp_file(self):
        """Kiểm tra Log_Txt tự động tạo file log có timestamp khi khởi động."""
        with tempfile.TemporaryDirectory() as temp_dir:
            txt_logger = Log_Txt(
                path_folder_log=temp_dir,
                enable_file=True,
                enable_console=False,
            )
            txt_logger.info("Khởi động phần mềm ca 1")
            txt_logger.disable_file()

            files = list(Path(temp_dir).glob("system_*.log"))
            self.assertEqual(len(files), 1, "Phải tạo đúng 1 file log có timestamp")
            content = files[0].read_text(encoding="utf-8")
            self.assertIn("Khởi động phần mềm ca 1", content)

    def test_log_csv_summary_daily_format(self):
        """Kiểm tra ghi file CSV tổng summary_daily.csv đúng theo chuẩn Ảnh 1."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_logger = Log_CSV(folder=temp_dir, enable=True)
            summary_record = {
                "Time": "2026-10-03 10:45:12",
                "Product": "vinhanh",
                "Session": "session_test_01",
                "OK/NG": "OK",
                "Tỷ lệ phán định": "95.00%",
                "Message": "Sản phẩm đạt chuẩn toàn bộ hạng mục",
            }

            saved_file = csv_logger.write_summary(summary_record)
            self.assertTrue(saved_file.exists())
            self.assertEqual(saved_file.name, "summary_daily.csv")

            with open(saved_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["Product"], "vinhanh")
                self.assertEqual(rows[0]["Session"], "session_test_01")
                self.assertEqual(rows[0]["OK/NG"], "OK")
                self.assertEqual(rows[0]["Tỷ lệ phán định"], "95.00%")
                self.assertEqual(rows[0]["Message"], "Sản phẩm đạt chuẩn toàn bộ hạng mục")

    def test_log_csv_session_detail_format(self):
        """Kiểm tra schema mới không còn cột Bọt khí và giữ đủ dữ liệu Tem."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_logger = Log_CSV(folder=temp_dir, enable=True)
            item_record = {
                "timestamp": "2026-10-03 10:45:15",
                "product_id": 1,
                "product_name": "vinhanh",
                "frame_id": 0,
                "item_id": 1,
                "overall_status": "NG",
                # Kiểm tra Có/Không tem (Stamp)
                "status_stamp": "NG",
                "stamp_theory": "Có tem (2 khung)",
                "stamp_reality": "1/2 khung có tem",
                "stamp_message": 'Thiếu tem tại 1/2 khung ("Tem 2")',
                # Ảnh item
                "image_name": "NG_session_test_01_f0_item_1.jpg",
            }

            saved_file = csv_logger.write_session_item("session_test_01", item_record)
            self.assertTrue(saved_file.exists())
            self.assertEqual(saved_file.name, "session_test_01.csv")

            with open(saved_file, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)
                header = rows[0]
                first_row = rows[1]

                self.assertNotIn("session_id", header)
                self.assertIn("Theory", header)
                self.assertIn("Reality", header)
                self.assertIn("message", header)
                self.assertNotIn("status_air_bubble", header)
                self.assertEqual(header[34], "status_stamp")
                self.assertEqual(header[-1], "Ảnh item")
                self.assertEqual(first_row[-1], "NG_session_test_01_f0_item_1.jpg")
                self.assertEqual(first_row[5], "NG")  # overall_status

                self.assertEqual(first_row[34], "NG")
                self.assertEqual(first_row[35], "Có tem (2 khung)")
                self.assertEqual(first_row[36], "1/2 khung có tem")
                self.assertEqual(first_row[37], 'Thiếu tem tại 1/2 khung ("Tem 2")')

                self.assertEqual(first_row[22], "NA")
                self.assertEqual(first_row[23], "NA")
                self.assertEqual(first_row[24], "N/A")
                self.assertEqual(first_row[25], "NA")

    def test_session_uncalled_inspectors_na_values(self):
        """Kiểm tra khi chỉ cấu hình Tem, các hạng mục không được gọi xuất NA."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_logger = Log_CSV(folder=temp_dir, enable=True)
            item_record = {
                "timestamp": "2026-10-03 11:20:00",
                "product_id": 1,
                "product_name": "Product_A",
                "frame_id": 0,
                "item_id": 4,
                "overall_status": "OK",
                # Stamp (được gọi)
                "status_stamp": "OK",
                "stamp_theory": "Có tem (2 khung)",
                "stamp_reality": "2/2 khung có tem",
                "stamp_message": "Đủ tem trên tất cả 2/2 khung",
                "image_name": "OK_session_100_f0_item_4.jpg",
            }

            saved_file = csv_logger.write_session_item("session_100", item_record)
            self.assertTrue(saved_file.exists())

            with open(saved_file, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                rows = list(reader)
                row = rows[1]

                # Các cột công cụ cũ đã gỡ bỏ luôn ghi NA, NA, N/A, NA
                for start_col in (6, 10, 14, 18, 22, 26, 30):
                    self.assertEqual(row[start_col], "NA")
                    self.assertEqual(row[start_col + 1], "NA")
                    self.assertEqual(row[start_col + 2], "N/A")
                    self.assertEqual(row[start_col + 3], "NA")

                self.assertEqual(row[34], "OK")
                self.assertEqual(row[35], "Có tem (2 khung)")
                self.assertEqual(row[36], "2/2 khung có tem")
                self.assertEqual(row[37], "Đủ tem trên tất cả 2/2 khung")

    def test_log_img_ok_ng_prefix(self):
        """Kiểm tra tên file ảnh có tiền tố OK_ hoặc NG_ và được lưu vào thư mục Log_img."""
        with tempfile.TemporaryDirectory() as temp_dir:
            img_logger = Log_Img(
                path_img=temp_dir,
                open_log_img=True,
                save_mode="ALL",
            )
            dummy_img = np.zeros((60, 60, 3), dtype=np.uint8)

            file_ok = img_logger.save(
                img=dummy_img,
                file_name="session_01_f0_item_0",
                status="OK",
            )
            self.assertIsNotNone(file_ok)
            self.assertTrue(file_ok.name.startswith("OK_"))
            self.assertTrue(file_ok.exists())

            file_ng = img_logger.save(
                img=dummy_img,
                file_name="session_01_f0_item_1",
                status="NG",
            )
            self.assertIsNotNone(file_ng)
            self.assertTrue(file_ng.name.startswith("NG_"))
            self.assertTrue(file_ng.exists())

    def test_manager_log_pipeline_integration(self):
        """Kiểm tra luồng tích hợp hoàn chỉnh qua Manager_Log."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config_SoftWare()
            config.disk_select = Path(temp_dir)
            config.set_open_csv(True)
            config.set_open_img(True)
            config.set_open_txt(True)
            config.set_image_save_mode("ALL")

            dummy_count_service = DummyProductCountService()

            manager = Manager_Log(
                Config_Software=config,
                product_count_service=dummy_count_service,
            )

            try:
                manager.queue_manager_log.put({
                    "type": "system",
                    "level": "info",
                    "msg": "Kiểm thử hệ thống logging mới",
                })

                dummy_img = np.zeros((40, 40, 3), dtype=np.uint8)
                manager.queue_manager_log.put({
                    "type": "image",
                    "msg": dummy_img,
                    "status": "NG",
                    "file_name": "NG_session_demo_f0_item_1",
                    "product_name": "vinhanh",
                })

                manager.queue_manager_log.put({
                    "type": "csv_item",
                    "session_id": "session_demo",
                    "msg": {
                        "session_id": "session_demo",
                        "product_id": 1,
                        "product_name": "vinhanh",
                        "frame_id": 0,
                        "item_id": 1,
                        "overall_status": "NG",
                        "status_stamp": "NG",
                        "stamp_theory": "Có tem (1 khung)",
                        "stamp_reality": "0/1 khung có tem",
                        "stamp_message": 'Thiếu tem tại 1/1 khung ("Tem 1")',
                        "image_name": "NG_session_demo_f0_item_1.jpg",
                    },
                })

                manager.queue_manager_log.put({
                    "type": "csv_summary",
                    "msg": {
                        "Session": "session_demo",
                        "Product": "vinhanh",
                        "OK/NG": "NG",
                        "Message": "Thiếu tem",
                    },
                })

                time.sleep(0.4)

                date_str = datetime.now().strftime("%Y-%m-%d")
                base_dir = Path(temp_dir) / "Log" / date_str

                txt_files = list((base_dir / "Log_txt").glob("system_*.log"))
                self.assertGreaterEqual(len(txt_files), 1)

                img_files = list((base_dir / "Product_UNKNOWN_PRODUCT" / "Log_img").glob("NG_*.jpg"))
                self.assertGreaterEqual(len(img_files), 1)

                csv_folder = base_dir / "Product_UNKNOWN_PRODUCT" / "Log_csv"
                summary_file = csv_folder / "summary_daily.csv"
                session_file = csv_folder / "session" / "session_demo.csv"

                self.assertTrue(summary_file.exists(), "summary_daily.csv phải tồn tại")
                self.assertTrue(session_file.exists(), "session/session_demo.csv phải tồn tại")

                with open(summary_file, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    self.assertEqual(len(rows), 1)
                    self.assertEqual(rows[0]["Tỷ lệ phán định"], "95.00%")
                    self.assertEqual(rows[0]["OK/NG"], "NG")

            finally:
                manager.stop_log_thread()

    def test_cleanup_entire_date_folder(self):
        """Kiểm tra cơ chế dọn dẹp log: xóa trọn vẹn toàn bộ thư mục ngày YYYY-MM-DD cũ."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_log_dir = Path(temp_dir) / "Log"
            old_date_dir = base_log_dir / "2026-08-01"
            today_date_dir = base_log_dir / datetime.now().strftime("%Y-%m-%d")

            (old_date_dir / "Log_txt").mkdir(parents=True, exist_ok=True)
            (old_date_dir / "Log_txt" / "system.log").write_text("old text log", encoding="utf-8")
            (old_date_dir / "Product_A" / "Log_img").mkdir(parents=True, exist_ok=True)
            (old_date_dir / "Product_A" / "Log_img" / "old.jpg").write_bytes(b"dummy")
            (old_date_dir / "Product_A" / "Log_csv").mkdir(parents=True, exist_ok=True)
            (old_date_dir / "Product_A" / "Log_csv" / "summary.csv").write_text("old csv", encoding="utf-8")

            (today_date_dir / "Log_txt").mkdir(parents=True, exist_ok=True)
            (today_date_dir / "Log_txt" / "system.log").write_text("today text log", encoding="utf-8")

            self.assertTrue(old_date_dir.exists())
            self.assertTrue(today_date_dir.exists())

            deleted_count = LogCleanupWorker.cleanup_now(temp_dir, retention_days=30)
            self.assertEqual(deleted_count, 1)

            self.assertFalse(old_date_dir.exists(), "Thư mục Log/2026-08-01 phải bị xóa hoàn toàn")
            self.assertTrue(today_date_dir.exists(), "Thư mục hôm nay phải được giữ nguyên")

    def test_config_software_log_dir_and_retrain_inspectors(self):
        """Kiểm tra cấu hình log và lọc ba inspector retrain còn hoạt động."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config_SoftWare()
            custom_log_dir = Path(temp_dir) / "CustomLogRoot"
            config.set_log_dir(str(custom_log_dir))
            config.set_time_save_log(15)

            paths = config.create_path_by_name_product("Product_Test")
            self.assertEqual(paths["path_base"], custom_log_dir / "Log")
            self.assertEqual(config.get_time_save_log(), 15)

            config.set_open_retrain(True)
            custom_inspectors = {
                "AirBubblesItemInspector": True,
                "AnomalyPointInspector": True,
                "ForeignObjectInspector": False,
                "MembraneInspector": False,
                "ScratchedPipeItemInspector": False,
                "StampItemInspector": True,
            }
            config.set_retrain_inspectors(custom_inspectors)

            enabled = config.get_enabled_retrain_inspectors()
            self.assertEqual(
                enabled,
                {"AnomalyPointInspector", "StampItemInspector"},
            )

            # Kiểm tra Master switch tắt -> không inspector nào được bật
            config.set_open_retrain(False)
            enabled_when_disabled = config.get_enabled_retrain_inspectors()
            self.assertEqual(
                enabled_when_disabled,
                set(),
                "Khi master switch tắt, danh sách inspector retrain phải là tập rỗng",
            )


if __name__ == "__main__":
    unittest.main()
