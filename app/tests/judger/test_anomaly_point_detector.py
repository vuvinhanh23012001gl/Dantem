import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from app.judger import AnomalyPointDetector, Judment


class FakePatchCoreFrame:
    """Giả lập FrameModelPatchCore theo score cố định (chỉ dùng cho kiểm thử logic phán định)."""

    def __init__(self, score: float, boxes=None):
        self.score = score
        self.boxes = boxes or []

    def predict_with_anomaly_boxes(self, img, x1, y1, x2, y2, threshold=0.1, min_area=50):
        heatmap = np.zeros((y2 - y1, x2 - x1, 3), dtype=np.uint8)
        return self.score, heatmap, list(self.boxes)


class FakeAnomalyService:
    """Service giả: mỗi roi_id có score riêng hoặc chưa có model (FileNotFoundError)."""

    def __init__(self, frames: dict):
        self.frames = frames
        self.saved = []

    def get_patchcore_frame(self, product_id, frame_id, item_id, roi_id=0):
        key = str(roi_id)
        if key not in self.frames:
            raise FileNotFoundError(f"roi {roi_id} chưa có model")
        return self.frames[key]

    def save_runtime_image_for_training(self, product_id, frame_id, item_id, image, roi_id=None):
        self.saved.append((roi_id, image.shape))


def _item_config():
    return {
        "AnomalyPointInspector": {
            "0": {
                "id": 0, "name": "Đầu ống trái",
                "xStart": 10, "yStart": 10, "xEnd": 110, "yEnd": 110,
                "threshold": 0.3, "saveRuntimeImages": False,
            },
            "1": {
                "id": 1, "name": "Đầu ống phải",
                "xStart": 200, "yStart": 10, "xEnd": 300, "yEnd": 110,
                "threshold": 0.5, "saveRuntimeImages": False,
            },
            "2": {
                "id": 2, "name": "Thân ống",
                "xStart": 10, "yStart": 150, "xEnd": 300, "yEnd": 250,
                "threshold": 0.2, "saveRuntimeImages": False,
            },
        }
    }


class TestAnomalyPointDetector(unittest.TestCase):
    def _run(self, frames: dict):
        service = FakeAnomalyService(frames)
        detector = AnomalyPointDetector(anomaly_point_service=service)
        judment = Judment({"AnomalyPointInspector": detector})
        img = np.zeros((300, 400, 3), dtype=np.uint8)
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            Judment, "RETRAIN_OUTPUT_DIR", Path(temp_dir)
        ):
            summary = judment.run_summary(
                img,
                _item_config(),
                training_context={"product_id": "1", "frame_id": "0", "item_id": "5"},
            )
        return summary

    def test_tasks_parse_multi_roi_with_individual_threshold(self):
        detector = AnomalyPointDetector(anomaly_point_service=FakeAnomalyService({}))
        tasks = Judment._tasks_from_config(
            _item_config(),
            {"AnomalyPointInspector": detector},
            1.0,
            context={"product_id": 1, "frame_id": 0, "item_id": 5},
        )
        self.assertEqual(len(tasks), 1)
        boxes = tasks[0].define_args[0]
        self.assertEqual([b["name"] for b in boxes], ["Đầu ống trái", "Đầu ống phải", "Thân ống"])
        self.assertEqual([b["threshold"] for b in boxes], [0.3, 0.5, 0.2])
        self.assertEqual(tasks[0].define_kwargs.get("item_id"), 5)

    def test_legacy_end_chipping_config_maps_to_anomaly_point(self):
        detector = AnomalyPointDetector(anomaly_point_service=FakeAnomalyService({}))
        legacy_config = {
            "EndChippingInspector": {
                "id": 0,
                "name": "Legacy ROI",
                "xStart": 10,
                "yStart": 20,
                "xEnd": 110,
                "yEnd": 120,
                "thresholdNG": 0.35,
            }
        }

        tasks = Judment._tasks_from_config(
            legacy_config,
            {"AnomalyPointInspector": detector},
            1.0,
        )

        self.assertEqual(len(tasks), 1)
        self.assertIs(tasks[0].inspector, detector)
        self.assertEqual(tasks[0].define_args[0][0]["threshold"], 0.35)
        self.assertIn("EndChippingInspector", legacy_config)

    def test_threshold_outside_zero_to_one_is_rejected(self):
        detector = AnomalyPointDetector(anomaly_point_service=FakeAnomalyService({}))
        with self.assertRaisesRegex(ValueError, "khoảng 0 đến 1"):
            detector.define(
                np.zeros((100, 100, 3), dtype=np.uint8),
                [{
                    "id": 0,
                    "name": "ROI",
                    "x1": 0,
                    "y1": 0,
                    "x2": 50,
                    "y2": 50,
                    "threshold": 1.1,
                }],
            )

    def test_all_regions_within_threshold_is_ok(self):
        summary = self._run({
            "0": FakePatchCoreFrame(0.10),
            "1": FakePatchCoreFrame(0.45),
            "2": FakePatchCoreFrame(0.20),
        })
        self.assertTrue(summary["overall"])
        result = summary["inspectors"]["AnomalyPointInspector"]
        self.assertTrue(result["ok"])
        self.assertEqual(result["standard_data"]["total_boxes"], 3)
        self.assertEqual(result["runtime_data"]["ok_count"], 3)

    def test_one_region_over_threshold_is_ng_and_names_region(self):
        summary = self._run({
            "0": FakePatchCoreFrame(0.10),
            "1": FakePatchCoreFrame(0.60, boxes=[(210, 20, 30, 30)]),
            "2": FakePatchCoreFrame(0.05),
        })
        self.assertFalse(summary["overall"])
        result = summary["inspectors"]["AnomalyPointInspector"]
        self.assertFalse(result["ok"])
        self.assertEqual(result["runtime_data"]["ok_count"], 2)
        joined = "\n".join(result["errors"])
        self.assertIn("Đầu ống phải", joined)
        self.assertNotIn("Đầu ống trái", joined)
        self.assertNotIn("Thân ống", joined)

    def test_region_without_model_is_ng_not_exception(self):
        summary = self._run({
            "0": FakePatchCoreFrame(0.10),
            "2": FakePatchCoreFrame(0.05),
        })
        self.assertFalse(summary["overall"])
        result = summary["inspectors"]["AnomalyPointInspector"]
        self.assertFalse(result["ok"])
        self.assertIn("Chưa tạo model", "\n".join(result["errors"]))
        self.assertIn("Đầu ống phải", "\n".join(result["errors"]))

    def test_save_runtime_images_goes_to_each_roi(self):
        service = FakeAnomalyService({"0": FakePatchCoreFrame(0.1), "1": FakePatchCoreFrame(0.1)})
        detector = AnomalyPointDetector(anomaly_point_service=service)
        boxes = [
            {"id": 0, "key": "0", "name": "A", "x1": 0, "y1": 0, "x2": 50, "y2": 50,
             "threshold": 0.3, "saveRuntimeImages": True},
            {"id": 1, "key": "1", "name": "B", "x1": 60, "y1": 0, "x2": 120, "y2": 50,
             "threshold": 0.3, "saveRuntimeImages": False},
        ]
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        detector.define(img, boxes, product_id=1, frame_id=0, item_id=5)
        import time
        time.sleep(0.2)
        self.assertEqual([roi for roi, _ in service.saved], [0])


if __name__ == "__main__":
    unittest.main()
