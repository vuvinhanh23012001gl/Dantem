import unittest
from unittest.mock import MagicMock, patch
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
import cv2
import time

from app.machine.anti_blur_service import AntiBlurService
from app.config.iai_config import IAIConfig
from app.stages.stage_2_transform import StageTransform, InspectionTaskItem


class TestAntiBlurFormulas(unittest.TestCase):
    """Kiểm tra độ chính xác của các công thức tính toán thời gian chống rung nhòe (URD Section 5)."""

    def test_urd_section_5_benchmark(self) -> None:
        """Kiểm tra benchmark cụ thể trong tài liệu đặc tả URD:
        FOV = 40mm, Sensor = 2000px -> R = 20 um/px.
        B_max = 0.5 px -> A_allow = 10 um.
        A0 = 50 um, fn = 50 Hz, zeta = 0.08 -> T_settle ~ 64.0 ms.
        T_exp = 2.0 ms, Hardware Trigger -> T_hold = 0.1 + 2.0 + 2.0 = 4.1 ms.
        T_total_stop ~ 68.1 ms.
        """
        timers = AntiBlurService.calculate_recommended_timers(
            fov_mm=40.0,
            sensor_px=2000,
            b_max_px=0.5,
            a0_um=50.0,
            fn_hz=50.0,
            zeta=0.08,
            t_exp_ms=2.0,
            is_hardware_trigger=True,
            t_safety_ms=2.0,
        )

        self.assertAlmostEqual(timers["resolution_um_per_px"], 20.0, places=2)
        self.assertAlmostEqual(timers["allowed_vibration_um"], 10.0, places=2)
        self.assertAlmostEqual(timers["t_settle_ms"], 64.05, delta=0.2)
        self.assertAlmostEqual(timers["t_hold_ms"], 4.1, delta=0.1)
        self.assertAlmostEqual(timers["t_total_stop_ms"], 68.15, delta=0.2)

    def test_software_trigger_timers(self) -> None:
        """Kiểm tra Software Trigger có T_trig_delay_ms = 10ms và T_safety_ms = 5ms."""
        timers = AntiBlurService.calculate_recommended_timers(
            fov_mm=40.0,
            sensor_px=2000,
            b_max_px=0.5,
            a0_um=50.0,
            fn_hz=50.0,
            zeta=0.08,
            t_exp_ms=2.0,
            is_hardware_trigger=False,
        )
        # T_hold = 10.0 (delay) + 2.0 (exp) + 5.0 (safety) = 17.0 ms
        self.assertAlmostEqual(timers["t_hold_ms"], 17.0, delta=0.1)

    def test_small_amplitude_already_stable(self) -> None:
        """Nếu biên độ dao động ban đầu nhỏ hơn biên độ cho phép thì trả về fallback 5ms."""
        timers = AntiBlurService.calculate_recommended_timers(
            fov_mm=100.0,
            sensor_px=1000,
            b_max_px=1.0,
            a0_um=10.0,  # Nhỏ hơn A_allow (100 um)
            fn_hz=50.0,
            zeta=0.08,
        )
        self.assertEqual(timers["t_settle_ms"], 5.0)


class TestAntiBlurConfigCache(unittest.TestCase):
    """Kiểm tra cache cấu hình anti-blur và cơ chế nhận diện thay đổi file."""

    def test_load_config_caches_and_refreshes(self) -> None:
        previous_config = AntiBlurService._cached_config
        previous_mtime_ns = AntiBlurService._cached_config_mtime_ns
        previous_path = AntiBlurService._cached_config_path
        self.addCleanup(setattr, AntiBlurService, "_cached_config", previous_config)
        self.addCleanup(setattr, AntiBlurService, "_cached_config_mtime_ns", previous_mtime_ns)
        self.addCleanup(setattr, AntiBlurService, "_cached_config_path", previous_path)

        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "anti_blur.json"
            config_path.write_text('{"t_settle_ms": 21.0}', encoding="utf-8")
            with patch.object(AntiBlurService, "get_config_path", return_value=str(config_path)):
                AntiBlurService._cached_config = None
                AntiBlurService._cached_config_mtime_ns = None
                AntiBlurService._cached_config_path = None

                with patch("builtins.open", wraps=open) as open_spy:
                    first_config = AntiBlurService.load_config()
                    second_config = AntiBlurService.load_config()

                self.assertEqual(first_config["t_settle_ms"], 21.0)
                self.assertEqual(second_config["t_settle_ms"], 21.0)
                self.assertEqual(open_spy.call_count, 1)

                AntiBlurService.save_config({"t_settle_ms": 32.0})
                self.assertEqual(AntiBlurService.load_config()["t_settle_ms"], 32.0)

                config_path.write_text('{"t_settle_ms": 43.0}', encoding="utf-8")
                file_stat = config_path.stat()
                os.utime(
                    config_path,
                    ns=(file_stat.st_atime_ns, file_stat.st_mtime_ns + 1_000_000_000),
                )
                self.assertEqual(AntiBlurService.load_config()["t_settle_ms"], 43.0)


class TestAntiBlurSharpnessGate(unittest.TestCase):
    """Kiểm tra cổng kiểm soát độ nét ảnh (Laplacian Variance)."""

    def test_sharp_image(self) -> None:
        """Ảnh có cạnh tương phản cao (checkerboard) phải vượt qua ngưỡng nét."""
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        # Vẽ các khối bàn cờ tạo cạnh sắc nét
        for y in range(0, 200, 20):
            for x in range(0, 200, 20):
                if ((x // 20) + (y // 20)) % 2 == 0:
                    img[y:y+20, x:x+20] = 255

        is_sharp, score = AntiBlurService.evaluate_sharpness(img, threshold=100.0)
        self.assertTrue(is_sharp)
        self.assertGreater(score, 100.0)

    def test_blurred_image(self) -> None:
        """Ảnh bị làm nhòe mạnh (motion blur/gaussian) phải bị đánh giá là không đạt."""
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img[50:150, 50:150] = 255
        # Làm nhòe mạnh với GaussianBlur
        blurred = cv2.GaussianBlur(img, (31, 31), 10.0)

        is_sharp, score = AntiBlurService.evaluate_sharpness(blurred, threshold=100.0)
        self.assertFalse(is_sharp)
        self.assertLess(score, 100.0)

    def test_invalid_image(self) -> None:
        """Ảnh rỗng hoặc None trả về (False, 0.0)."""
        is_sharp, score = AntiBlurService.evaluate_sharpness(None)
        self.assertFalse(is_sharp)
        self.assertEqual(score, 0.0)

        empty_img = np.array([])
        is_sharp, score = AntiBlurService.evaluate_sharpness(empty_img)
        self.assertFalse(is_sharp)
        self.assertEqual(score, 0.0)


class TestStage2AntiBlurIntegration(unittest.TestCase):
    """Kiểm tra tích hợp logic chống rung nhòe vào Stage 2 Transform."""

    def setUp(self) -> None:
        self.mock_services = MagicMock()
        self.mock_services.obj_iai_config = IAIConfig()
        self.mock_services.obj_iai_config.t_settle_ms = 10.0  # 10ms for fast testing
        self.mock_services.obj_iai_config.t_hold_safety_ms = 10.0
        self.mock_services.obj_iai_config.blur_threshold = 100.0
        self.mock_services.obj_iai_config.auto_retrigger_on_blur = True
        self.mock_services.obj_iai_config.max_retrigger_count = 1
        self.mock_services.obj_iai_control.get_status.return_value.name = "AUTO"
        self.mock_services.runtime_state.is_stop_requested.return_value = False

    def test_capture_task_triggers_retrigger_on_blurred_image(self) -> None:
        """Nếu ảnh đầu tiên bị nhòe và auto_retrigger bật, hệ thống phải kích hoạt chụp lại."""
        stage = StageTransform(self.mock_services)

        # Tạo ảnh nhòe và ảnh nét
        blurred_img = cv2.GaussianBlur(np.ones((100, 100, 3), dtype=np.uint8) * 128, (15, 15), 5.0)
        sharp_img = np.zeros((100, 100, 3), dtype=np.uint8)
        sharp_img[::2, ::2] = 255

        # Lần 1 trả về ảnh nhòe, lần 2 trả về ảnh nét
        with patch.object(stage, "_move_with_retry", return_value=True), \
             patch.object(stage, "_capture_with_retry", side_effect=[blurred_img, sharp_img]) as mock_capture:

            prepared = MagicMock()
            frame = {"frame_id": "0", "calibration": {"scale_mm_per_pixel": 0.05, "is_calibrated": True}}
            point = {"point_id": "0", "x": 100, "y": 200, "z": 300, "judgment": {"Inspector": {}}}

            task = stage._capture_point_task(prepared, frame, point, step=1)

            # Phải gọi capture 2 lần vì lần đầu bị nhòe
            self.assertEqual(mock_capture.call_count, 2)
            self.assertGreaterEqual(task.sharpness_score, 100.0)



class TestAntiBlurAPI(unittest.TestCase):
    """Kiểm tra các endpoints REST API của AntiBlurService."""

    @classmethod
    def setUpClass(cls) -> None:
        from fastapi.testclient import TestClient
        from app.main import app
        cls.client = TestClient(app)

    def test_get_anti_blur_config(self) -> None:
        """GET /api/anti_blur/config trả về cấu hình hiện tại và tính toán metric."""
        response = self.client.get("/api/anti_blur/config")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["status"])
        self.assertIn("data", body)
        self.assertIn("t_settle_ms", body["data"])
        self.assertIn("calculated", body)

    def test_save_anti_blur_config(self) -> None:
        """POST /api/anti_blur/config lưu thành công dữ liệu vào storage file."""
        payload = {
            "t_settle_ms": 42.0,
            "t_hold_safety_ms": 16.0,
            "t_exp_ms": 2.5,
            "is_hardware_trigger": False,
            "blur_threshold": 115.0,
            "auto_retrigger_on_blur": True,
            "max_retrigger_count": 2,
            "extra_settle_ms": 25.0,
            "fov_mm": 40.0,
            "sensor_px": 2000,
            "b_max_px": 0.5,
            "a0_um": 50.0,
            "fn_hz": 50.0,
            "zeta": 0.08,
            "t_safety_ms": 5.0,
        }
        response = self.client.post("/api/anti_blur/config", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["status"])
        self.assertEqual(body["data"]["t_settle_ms"], 42.0)
        self.assertEqual(body["data"]["blur_threshold"], 115.0)

        # Đọc lại bằng GET để xác nhận lưu bền vững vào file
        get_res = self.client.get("/api/anti_blur/config")
        get_body = get_res.json()
        self.assertEqual(get_body["data"]["t_settle_ms"], 42.0)
        self.assertEqual(get_body["data"]["blur_threshold"], 115.0)

    def test_calculate_anti_blur_timers(self) -> None:
        """POST /api/anti_blur/calculate tính toán đúng các thông số URD."""
        payload = {
            "fov_mm": 40.0,
            "sensor_px": 2000,
            "b_max_px": 0.5,
            "a0_um": 50.0,
            "fn_hz": 50.0,
            "zeta": 0.08,
            "t_exp_ms": 2.0,
            "is_hardware_trigger": True,
            "t_safety_ms": 2.0,
        }
        response = self.client.post("/api/anti_blur/calculate", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["status"])
        self.assertAlmostEqual(body["data"]["t_settle_ms"], 64.05, delta=0.2)
    def test_reload_features_config(self) -> None:
        """POST /api/anti_blur/reload_features đọc file features.cfg thành công."""
        response = self.client.post("/api/anti_blur/reload_features")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["status"])
        self.assertIn("hardware_info", body)
        self.assertGreater(body["hardware_info"]["exposure_time_ms"], 0)

    def test_get_anti_blur_defaults(self) -> None:
        """GET /api/anti_blur/defaults trả về danh sách 14 tham số chuẩn an toàn."""
        response = self.client.get("/api/anti_blur/defaults")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["status"])
        self.assertIn("data", body)
        self.assertEqual(body["data"]["fov_mm"], 40.0)
        self.assertEqual(body["data"]["t_settle_ms"], 40.0)


if __name__ == "__main__":
    unittest.main()
