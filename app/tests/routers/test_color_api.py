import asyncio
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np

from app.core import Result
from app.routers.api_tool_law_regulations import run_model_color
from app.judger.color_detector import ColorDetector


class FakePointService:
    def __init__(self, image_path):
        self.image_path = image_path

    def get_path_img_point(self, product_id, frame_id, item_id):
        return Result.Ok(self.image_path)


class FakeColorService:
    def inspect_color_boxes(self, image, boxes, width_canvas=None):
        box_evals = []
        for b in boxes:
            box_evals.append({
                "id": b.get("id", 0),
                "name": b.get("name", "Vùng màu 1"),
                "status": "OK",
                "delta_e00": 1.2,
                "delta_e76": 1.5,
                "similarity": 98.8,
                "max_delta_e": b.get("max_delta_e", 5.0),
                "ref_rgb": b.get("ref_rgb", [255, 0, 0]),
                "measured_rgb": [250, 2, 5],
                "measured_lab": [53.0, 78.0, 65.0],
            })
        return Result.Ok({
            "boxes": box_evals,
            "image_width": image.shape[1],
            "image_height": image.shape[0],
        })


class TestColorAPI(unittest.TestCase):
    def test_run_model_color_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "test_color_item.png"
            image = np.zeros((100, 200, 3), dtype=np.uint8)
            self.assertTrue(cv2.imwrite(str(image_path), image))

            mock_service = FakeColorService()
            services = type(
                "Services",
                (),
                {
                    "obj_point_service": FakePointService(image_path),
                    "obj_color_service": mock_service,
                },
            )()

            payload = {
                "select": {
                    "product_id": 1,
                    "frame_id": 0,
                    "items_id": 2,
                },
                "boxes": [
                    {
                        "id": 1,
                        "name": "Vung 1",
                        "xStart": 10,
                        "yStart": 10,
                        "xEnd": 60,
                        "yEnd": 60,
                        "ref_rgb": [255, 0, 0],
                        "max_delta_e": 5.0,
                    }
                ],
                "WidthCanvas": 1024,
            }

            resp = asyncio.run(run_model_color(data=payload, services=services))
            self.assertTrue(resp["ok"])
            self.assertIn("boxes", resp["data"])
            self.assertEqual(len(resp["data"]["boxes"]), 1)
            self.assertEqual(resp["data"]["boxes"][0]["status"], "OK")


if __name__ == "__main__":
    unittest.main()
