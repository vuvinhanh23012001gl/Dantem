import asyncio
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np

from app.core import Result
from app.routers.api_tool_law_regulations import run_model_stamp_alignment
from app.judger.stamp_alignment_detector import StampAlignmentDetector


class FakePointService:
    def __init__(self, image_path):
        self.image_path = image_path

    def get_path_img_point(self, product_id, frame_id, item_id):
        return Result.Ok(self.image_path)


class FakeStampAlignmentService:
    def __init__(self):
        self.last_boxes = None

    def inspect_alignment_boxes(self, image, boxes, width_canvas=None):
        self.last_boxes = boxes
        box_evals = []
        for b in boxes:
            box_evals.append({
                "id": b.get("id", 0),
                "name": b.get("name", "Tem 1"),
                "status": "OK",
                "metrics": {
                    "du": 2.5,
                    "dv": 1.2,
                    "magnitude": 2.77,
                    "direction_deg": 25.6,
                    "delta_angle_deg": 0.5,
                    "is_contained": True,
                    "unit": "pixel",
                },
                "details": {
                    "pass_position_u": True,
                    "pass_position_v": True,
                    "pass_rotation": True,
                    "pass_containment": True,
                },
                "tolerances": {
                    "max_du": b.get("max_du", 15.0),
                    "max_dv": b.get("max_dv", 15.0),
                    "max_deg": b.get("max_deg", 3.0),
                    "margin": b.get("margin", 5.0),
                },
            })
        return Result.Ok({
            "boxes": box_evals,
            "objects": [
                {
                    "roi_id": 0,
                    "type": "obb_frame",
                    "corners": [[10, 10], [90, 10], [90, 50], [10, 50]],
                    "color": "#00E676",
                }
            ],
            "image_width": image.shape[1],
            "image_height": image.shape[0],
        })


class TestStampAlignmentAPI(unittest.TestCase):
    def test_run_model_stamp_alignment_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "test_item.png"
            image = np.zeros((100, 200, 3), dtype=np.uint8)
            self.assertTrue(cv2.imwrite(str(image_path), image))

            mock_service = FakeStampAlignmentService()
            services = type(
                "Services",
                (),
                {
                    "obj_point_service": FakePointService(image_path),
                    "obj_stamp_alignment_service": mock_service,
                },
            )()

            payload = {
                "select": {"product_id": 1, "frame_id": 0, "items_id": 2},
                "boxes": [
                    {
                        "id": 0,
                        "name": "Tem Test",
                        "xStart": 10,
                        "yStart": 10,
                        "xEnd": 50,
                        "yEnd": 40,
                        "max_du": 12.0,
                        "max_dv": 12.0,
                        "max_deg": 2.5,
                        "margin": 4.0,
                    }
                ],
                "WidthCanvas": 600,
            }

            res = asyncio.run(run_model_stamp_alignment(data=payload, services=services))
            self.assertTrue(res.get("ok"))
            data = res.get("data")
            self.assertIsNotNone(data)
            self.assertEqual(len(data["boxes"]), 1)
            box = data["boxes"][0]
            self.assertEqual(box["status"], "OK")
            self.assertEqual(box["name"], "Tem Test")
            self.assertEqual(box["metrics"]["du"], 2.5)
            self.assertTrue(box["metrics"]["is_contained"])

    def test_stamp_alignment_detector_judge(self):
        mock_service = FakeStampAlignmentService()
        detector = StampAlignmentDetector(mock_service)
        image = np.zeros((100, 200, 3), dtype=np.uint8)
        boxes = [{"id": 0, "name": "Tem 1", "x1": 10, "y1": 10, "x2": 50, "y2": 40}]

        runtime_data = detector.define(image, boxes)
        comparison_data = detector.compare(standard_data={}, runtime_data=runtime_data)
        judgment = detector.judge(comparison_data)

        self.assertTrue(judgment.ok)
        self.assertEqual(judgment.status, "OK")
        self.assertIn("Tem chuẩn vị trí", judgment.message)


if __name__ == "__main__":
    unittest.main()
