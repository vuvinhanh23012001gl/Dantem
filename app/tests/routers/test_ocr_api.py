import asyncio
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from app.core import Result
from app.judger import JudgmentResult
from app.routers.api_tool_law_regulations import run_model_ocr


class FakePointService:
    def __init__(self, image_path):
        self.image_path = image_path

    def get_path_img_point(self, product_id, frame_id, item_id):
        return Result.Ok(self.image_path)


class FakeOCRDetector:
    def __init__(self):
        self.region = None

    def evaluate_roi(self, image, region):
        self.region = region
        return JudgmentResult(
            ok=True,
            status="OK",
            runtime_data={
                "boxes": [
                    {
                        "id": region["id"],
                        "name": region["name"],
                        "expected_text": region["expected_text"],
                        "text": "ABC",
                        "lines": [{"text": "ABC", "angle": 180}],
                        "confidence": 0.95,
                        "has_text": True,
                        "ok": True,
                    }
                ]
            },
            message="Nhận diện đúng 1/1 khung OCR",
        )


class TestOCRAPI(unittest.TestCase):
    def test_run_model_ocr_scales_and_processes_only_selected_roi(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "item.png"
            image = np.zeros((100, 200, 3), dtype=np.uint8)
            self.assertTrue(cv2.imwrite(str(image_path), image))
            detector = FakeOCRDetector()
            services = type(
                "Services",
                (),
                {
                    "obj_point_service": FakePointService(image_path),
                    "obj_ocr_text_detector": detector,
                },
            )()
            payload = {
                "select": {
                    "product_id": 1,
                    "frame_id": 2,
                    "items_id": 3,
                },
                "roi": {
                    "id": 4,
                    "name": "Mã hàng",
                    "xStart": 10,
                    "yStart": 20,
                    "xEnd": 30,
                    "yEnd": 40,
                    "expected_text": "ABC",
                },
                "WidthCanvas": 100,
                "HeightCanvas": 100,
            }

            response = asyncio.run(run_model_ocr(payload, services))

            self.assertTrue(response["ok"])
            self.assertTrue(response["data"]["ok"])
            self.assertEqual(detector.region["x1"], 20)
            self.assertEqual(detector.region["y1"], 20)
            self.assertEqual(detector.region["x2"], 60)
            self.assertEqual(detector.region["y2"], 40)
            self.assertEqual(len(response["data"]["boxes"]), 1)


if __name__ == "__main__":
    unittest.main()
