import unittest
import numpy as np
import cv2

from app.engines.service.color_service import (
    bgr_to_lab_chuan,
    delta_e76,
    delta_e2000,
    compute_color_similarity,
    ColorService,
)
from app.judger.color_detector import ColorDetector


class TestColorService(unittest.TestCase):
    def test_bgr_to_lab_chuan_white(self):
        # Màu trắng BGR (255, 255, 255) -> L* ≈ 100, a* ≈ 0, b* ≈ 0
        white_bgr = np.array([255, 255, 255], dtype=np.float32)
        L, a, b = bgr_to_lab_chuan(white_bgr)
        self.assertAlmostEqual(L, 100.0, places=1)
        self.assertAlmostEqual(a, 0.0, places=1)
        self.assertAlmostEqual(b, 0.0, places=1)

    def test_bgr_to_lab_chuan_black(self):
        # Màu đen BGR (0, 0, 0) -> L* ≈ 0, a* ≈ 0, b* ≈ 0
        black_bgr = np.array([0, 0, 0], dtype=np.float32)
        L, a, b = bgr_to_lab_chuan(black_bgr)
        self.assertAlmostEqual(L, 0.0, places=1)
        self.assertAlmostEqual(a, 0.0, places=1)
        self.assertAlmostEqual(b, 0.0, places=1)

    def test_delta_e_identical_colors(self):
        lab = (50.0, 10.0, -20.0)
        self.assertAlmostEqual(delta_e76(lab, lab), 0.0, places=4)
        self.assertAlmostEqual(delta_e2000(lab, lab), 0.0, places=4)
        self.assertAlmostEqual(compute_color_similarity(0.0), 100.0, places=2)

    def test_delta_e_different_colors(self):
        lab1 = (50.0, 10.0, 20.0)
        lab2 = (55.0, 12.0, 22.0)
        de76 = delta_e76(lab1, lab2)
        de00 = delta_e2000(lab1, lab2)
        self.assertGreater(de76, 0.0)
        self.assertGreater(de00, 0.0)
        sim = compute_color_similarity(de00)
        self.assertTrue(0 <= sim <= 100)

    def test_inspect_color_roi_ok(self):
        service = ColorService()
        # Tạo ảnh đỏ hoàn toàn BGR=(0, 0, 255)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[:, :] = [0, 0, 255]

        roi_cfg = {
            "id": 1,
            "name": "Vung Do",
            "xStart": 10,
            "yStart": 10,
            "xEnd": 50,
            "yEnd": 50,
            "ref_rgb": [255, 0, 0],  # Màu chuẩn là đỏ
            "max_delta_e": 5.0,
        }

        data = service.inspect_color_roi(image, roi_cfg, width_canvas=100)
        self.assertEqual(data["status"], "OK")
        self.assertLessEqual(data["delta_e"], 5.0)
        self.assertAlmostEqual(data["similarity_percent"], 100.0, places=1)

    def test_inspect_color_roi_ng(self):
        service = ColorService()
        # Ảnh xanh lá BGR=(0, 255, 0)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[:, :] = [0, 255, 0]

        roi_cfg = {
            "id": 2,
            "name": "Vung Xanh",
            "xStart": 10,
            "yStart": 10,
            "xEnd": 50,
            "yEnd": 50,
            "ref_rgb": [255, 0, 0],  # Màu chuẩn là đỏ -> Sai lệch màu lớn
            "max_delta_e": 5.0,
        }

        data = service.inspect_color_roi(image, roi_cfg, width_canvas=100)
        self.assertEqual(data["status"], "NG")
        self.assertGreater(data["delta_e"], 5.0)

    def test_color_detector_evaluate(self):
        service = ColorService()
        detector = ColorDetector(service)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[:, :] = [100, 150, 200]  # BGR

        boxes = [
            {
                "id": 3,
                "name": "Vung Test",
                "xStart": 10,
                "yStart": 10,
                "xEnd": 60,
                "yEnd": 60,
                "ref_rgb": [200, 150, 100],  # RGB tương ứng với BGR
                "max_delta_e": 5.0,
            }
        ]

        runtime_data = detector.define(image, boxes)
        comparison_data = detector.compare(standard_data={}, runtime_data=runtime_data)
        judgment = detector.judge(comparison_data)
        self.assertTrue(judgment.ok)
        self.assertEqual(judgment.status, "OK")


if __name__ == "__main__":
    unittest.main()
