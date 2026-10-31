import unittest
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.api_config_camera import router as camera_router
from app.services.camera import Camera
from app.core.dependencies import get_services


class TestCameraConfigAPI(unittest.TestCase):
    """Kiểm tra API thông tin camera và thiết bị phần cứng ở chế độ chỉ đọc (Read-only)."""

    def setUp(self):
        self.mock_services = MagicMock()
        self.mock_camera = MagicMock(spec=Camera)
        self.mock_services.obj_camera = self.mock_camera

        self.app = FastAPI(title="Camera Test App")
        self.app.include_router(camera_router)
        self.app.dependency_overrides[get_services] = lambda: self.mock_services
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def test_camera_get_device_info_structure(self):
        """Kiểm tra method get_device_info() của Camera trả về đầy đủ các trường chỉ đọc."""
        real_camera = Camera.__new__(Camera)
        real_camera.lock_connect = MagicMock()
        real_camera._isConnect = True
        real_camera.st_device = None
        real_camera.nodemap = None
        real_camera._image = None
        real_camera._lock = MagicMock()
        real_camera.get_is_connect = MagicMock(return_value=True)

        info = Camera.get_device_info(real_camera)
        self.assertTrue(info["connected"])
        self.assertEqual(info["status"], "Đang kết nối (Online)")
        self.assertIn("OMRON SENTECH", info["vendor"].upper())
        self.assertIn("USB3 VISION", info["interface"].upper())
        self.assertEqual(info["resolution"], "2448 x 2048 px")
        self.assertIn("payload_size", info)
        self.assertIn("device_model", info)
        self.assertIn("serial_number", info)

    def test_get_camera_config_endpoint_includes_device_info(self):
        """Kiểm tra endpoint GET /camera/config trả về cả config và device_info."""
        self.mock_camera.get_config.return_value = {
            "acquisition_frame_rate": 30.0,
            "exposure_time": 10000.0,
            "gain": 0.0,
            "gamma": 1.0,
            "black_level": 0.0,
            "exposure_auto": "Off",
            "trigger_mode": "Off",
            "trigger_selector": "FrameStart",
        }
        self.mock_camera.get_device_info.return_value = {
            "connected": True,
            "status": "Đang kết nối (Online)",
            "device_name": "STC-MCS510U3V",
            "device_model": "STC-MCS510U3V",
            "serial_number": "20F4912",
            "vendor": "OMRON SENTECH",
            "resolution": "2448 x 2048 px",
            "width": 2448,
            "height": 2048,
            "payload_size": "5,013,504 bytes",
            "pixel_format": "BayerRG8",
            "interface": "USB3 Vision (U3V)",
        }

        response = self.client.get("/camera/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Kiểm tra config field
        self.assertEqual(data["acquisition_frame_rate"], 30.0)
        self.assertEqual(data["exposure_time"], 10000.0)

        # Kiểm tra device_info field
        self.assertIn("device_info", data)
        dev = data["device_info"]
        self.assertEqual(dev["device_model"], "STC-MCS510U3V")
        self.assertEqual(dev["serial_number"], "20F4912")
        self.assertEqual(dev["resolution"], "2448 x 2048 px")
        self.assertEqual(dev["status"], "Đang kết nối (Online)")

    def test_get_camera_status_endpoint_includes_device_info(self):
        """Kiểm tra endpoint GET /camera/status trả về status, config và device_info."""
        self.mock_camera.get_is_connect.return_value = True
        self.mock_camera.camera_lost = False
        self.mock_camera.get_config.return_value = {"exposure_time": 10000.0}
        self.mock_camera.get_device_info.return_value = {
            "connected": True,
            "status": "Đang kết nối (Online)",
            "device_model": "STC-MCS510U3V",
        }

        response = self.client.get("/camera/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["device_info"]["device_model"], "STC-MCS510U3V")

    def test_get_camera_exit_endpoint(self):
        """Kiểm tra endpoint GET /camera/exit trả về trạng thái ok và redirect_url."""
        response = self.client.get("/camera/exit")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["redirect_url"], "/")

    def test_mutation_endpoints_removed(self):
        """Kiểm tra toàn bộ endpoint ghi/sửa cấu hình camera đã bị loại bỏ (trả về 404 Not Found)."""
        apply_resp = self.client.post("/camera/config/apply", json={"gain": 50})
        self.assertEqual(apply_resp.status_code, 404)

        save_resp = self.client.post("/camera/config/save", json={"gain": 50})
        self.assertEqual(save_resp.status_code, 404)

        reset_resp = self.client.post("/camera/config/reset")
        self.assertEqual(reset_resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
