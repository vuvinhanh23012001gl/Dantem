import unittest
import numpy as np

from app.engines.service.stamp_reversed_service import StampReversedService
from app.judger import JudgmentResult, Judment, StampReversedDetector


class FakeOCRService:
    def __init__(self, responses):
        self.responses = list(responses)

    def inspect_image(self, image):
        if self.responses:
            return self.responses.pop(0)
        return {"success": False, "lines": [], "text": ""}


class FakeYoloOBB:
    def __init__(self, predictions=None):
        self.predictions = list(predictions or [])

    def predict(self, crop):
        if self.predictions:
            return self.predictions.pop(0)
        return []


def create_ocr_line(text="LOT 2026", angle=0, confidence=0.95):
    return {
        "text": text,
        "angle": angle,
        "confidence": confidence,
        "skew_angle": 1.2,
        "bbox": [5, 5, 50, 20],
        "polygon": [[5, 5], [50, 5], [50, 20], [5, 20]],
    }


class TestStampReversedService(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((100, 150, 3), dtype=np.uint8)
        self.box = {
            "id": 1,
            "name": "Tem 1",
            "xStart": 10,
            "yStart": 10,
            "xEnd": 120,
            "yEnd": 80,
            "max_deg": 15.0,
        }

    def test_normal_text_zero_degree_is_ok(self):
        fake_ocr = FakeOCRService([{
            "success": True,
            "lines": [create_ocr_line("ABC 123", angle=0, confidence=0.96)],
            "text": "ABC 123",
        }])
        service = StampReversedService(yolo_obb=None, ocr_service=fake_ocr)
        res = service.inspect_single_box(self.image, self.box)

        self.assertEqual(res["status"], "OK")
        self.assertEqual(res["error_code"], "NONE")
        self.assertEqual(res["text_angle"], 0)
        self.assertFalse(res["is_reversed"])

    def test_reversed_text_180_degree_is_ng(self):
        fake_ocr = FakeOCRService([{
            "success": True,
            "lines": [create_ocr_line("ABC 123", angle=180, confidence=0.92)],
            "text": "ABC 123",
        }])
        service = StampReversedService(yolo_obb=None, ocr_service=fake_ocr)
        res = service.inspect_single_box(self.image, self.box)

        self.assertEqual(res["status"], "NG")
        self.assertEqual(res["error_code"], "TEXT_REVERSED")
        self.assertEqual(res["text_angle"], 180)
        self.assertTrue(res["is_reversed"])

    def test_rotated_text_90_degree_is_ng(self):
        fake_ocr = FakeOCRService([{
            "success": True,
            "lines": [create_ocr_line("ABC 123", angle=90, confidence=0.90)],
            "text": "ABC 123",
        }])
        service = StampReversedService(yolo_obb=None, ocr_service=fake_ocr)
        res = service.inspect_single_box(self.image, self.box)

        self.assertEqual(res["status"], "NG")
        self.assertEqual(res["error_code"], "TEXT_ROTATED")
        self.assertEqual(res["text_angle"], 90)

    def test_obb_angle_exceeding_tolerance_is_ng(self):
        fake_ocr = FakeOCRService([{
            "success": True,
            "lines": [create_ocr_line("ABC 123", angle=0, confidence=0.95)],
            "text": "ABC 123",
        }])
        # OBB angle = 22° > max_deg 15°
        fake_obb = FakeYoloOBB([[
            {
                "class_name": "stamp",
                "confidence": 0.88,
                "angle_deg": 22.5,
                "polygon": [[10, 10], [80, 15], [75, 45], [5, 40]],
            }
        ]])
        service = StampReversedService(yolo_obb=fake_obb, ocr_service=fake_ocr)
        res = service.inspect_single_box(self.image, self.box)

        self.assertEqual(res["status"], "NG")
        self.assertEqual(res["error_code"], "LABEL_ROTATED")
        self.assertAlmostEqual(res["obb_angle"], 22.5, places=1)

    def test_empty_text_returns_unknown(self):
        fake_ocr = FakeOCRService([{
            "success": False,
            "lines": [],
            "text": "",
        }])
        service = StampReversedService(yolo_obb=None, ocr_service=fake_ocr)
        res = service.inspect_single_box(self.image, self.box)

        self.assertEqual(res["status"], "UNKNOWN")
        self.assertEqual(res["error_code"], "TEXT_NOT_DETECTED")


class TestStampReversedDetector(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((100, 150, 3), dtype=np.uint8)
        self.boxes = [{
            "id": 1,
            "name": "Tem ngược 1",
            "xStart": 10,
            "yStart": 10,
            "xEnd": 120,
            "yEnd": 80,
            "max_deg": 15.0,
        }]

    def test_detector_judge_all_ok(self):
        fake_ocr = FakeOCRService([{
            "success": True,
            "lines": [create_ocr_line("ABC", angle=0)],
            "text": "ABC",
        }])
        service = StampReversedService(yolo_obb=None, ocr_service=fake_ocr)
        detector = StampReversedDetector(service)

        defined = detector.define(self.image, self.boxes)
        compared = detector.compare(None, defined)
        judged = detector.judge(compared)

        self.assertTrue(judged.ok)
        self.assertEqual(len(judged.errors), 0)

    def test_detector_judge_reversed_ng(self):
        fake_ocr = FakeOCRService([{
            "success": True,
            "lines": [create_ocr_line("ABC", angle=180)],
            "text": "ABC",
        }])
        service = StampReversedService(yolo_obb=None, ocr_service=fake_ocr)
        detector = StampReversedDetector(service)

        defined = detector.define(self.image, self.boxes)
        compared = detector.compare(None, defined)
        judged = detector.judge(compared)

        self.assertFalse(judged.ok)
        self.assertTrue(any("TEXT_REVERSED" in err for err in judged.errors))

    def test_judment_coordinator_integration(self):
        fake_ocr = FakeOCRService([{
            "success": True,
            "lines": [create_ocr_line("ABC 123", angle=0)],
            "text": "ABC 123",
        }])
        service = StampReversedService(yolo_obb=None, ocr_service=fake_ocr)
        detector = StampReversedDetector(service)
        judment = Judment({"StampReversedInspector": detector})

        item_config = {
            "StampReversedInspector": {
                "0": {
                    "id": 0,
                    "name": "Tem ngược 1",
                    "xStart": 10,
                    "yStart": 10,
                    "xEnd": 120,
                    "yEnd": 80,
                    "max_deg": 15.0,
                }
            }
        }
        summary = judment.run_summary(
            image=self.image,
            inspectors=item_config,
        )

        self.assertTrue(summary["overall"])
        self.assertEqual(len(summary["errors"]), 0)
        self.assertEqual(summary["status"], "OK")
        self.assertIn("StampReversedInspector", summary["inspectors"])
        self.assertTrue(summary["inspectors"]["StampReversedInspector"]["ok"])


if __name__ == "__main__":
    unittest.main()
