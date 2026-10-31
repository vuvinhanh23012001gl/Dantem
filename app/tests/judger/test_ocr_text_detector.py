import unittest

import numpy as np

from app.judger import JudgmentResult, Judment, OCRTextDetector


class FakeOCRService:
    def __init__(self, results):
        self.results = list(results)

    def inspect_image(self, image):
        self.last_shape = image.shape
        return self.results.pop(0)


def ocr_result(lines):
    return {
        "success": bool(lines),
        "text": "\n".join(line["text"] for line in lines),
        "lines": lines,
        "processing_time_ms": 2.0,
        "error_message": None if lines else "No text detected",
    }


class TestOCRTextDetector(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((80, 120, 3), dtype=np.uint8)
        self.region = {
            "id": 4,
            "key": "4",
            "name": "Mã sản phẩm",
            "xStart": 10,
            "yStart": 10,
            "xEnd": 70,
            "yEnd": 50,
            "expected_text": "ABC 123",
        }

    def test_exact_text_match_ignores_only_outer_whitespace_and_rotation(self):
        service = FakeOCRService(
            [
                ocr_result(
                    [
                        {
                            "text": " ABC 123 ",
                            "confidence": 0.94,
                            "angle": 180,
                            "skew_angle": 2.0,
                        }
                    ]
                )
            ]
        )
        detector = OCRTextDetector(service)

        result = detector.evaluate_roi(self.image, self.region)

        self.assertTrue(result.ok)
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.runtime_data["boxes"][0]["lines"][0]["angle"], 180)

    def test_comparison_is_case_sensitive_and_preserves_internal_spaces(self):
        service = FakeOCRService(
            [
                ocr_result(
                    [
                        {
                            "text": "abc  123",
                            "confidence": 0.99,
                            "angle": 0,
                        }
                    ]
                )
            ]
        )
        result = OCRTextDetector(service).evaluate_roi(self.image, self.region)

        self.assertFalse(result.ok)
        self.assertIn("abc  123", result.errors[0])

    def test_multiline_text_is_compared_with_newline_order_preserved(self):
        region = {**self.region, "expected_text": "LOT: 01\nDATE: 2026"}
        service = FakeOCRService(
            [
                ocr_result(
                    [
                        {"text": "LOT: 01", "confidence": 0.9, "angle": 0},
                        {"text": "DATE: 2026", "confidence": 0.8, "angle": 90},
                    ]
                )
            ]
        )
        result = OCRTextDetector(service).evaluate_roi(self.image, region)

        self.assertTrue(result.ok)
        self.assertEqual(
            result.runtime_data["boxes"][0]["text"],
            "LOT: 01\nDATE: 2026",
        )
        self.assertEqual(
            [line["angle"] for line in result.runtime_data["boxes"][0]["lines"]],
            [0, 90],
        )

    def test_empty_expected_text_and_no_text_are_always_ng(self):
        no_text = FakeOCRService([ocr_result([])])
        detector = OCRTextDetector(no_text)
        result = detector.evaluate_roi(
            self.image,
            {**self.region, "expected_text": ""},
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.runtime_data["boxes"][0]["text"], "")
        self.assertTrue(result.errors)

    def test_stage2_runs_each_configured_roi_and_requires_every_match(self):
        service = FakeOCRService(
            [
                ocr_result([{"text": "ABC 123", "confidence": 0.9, "angle": 180}]),
                ocr_result([{"text": "WRONG", "confidence": 0.9, "angle": 0}]),
            ]
        )
        detector = OCRTextDetector(service)
        judgment = Judment({OCRTextDetector.INSPECTOR_NAME: detector})
        config = {
            OCRTextDetector.INSPECTOR_NAME: {
                "4": self.region,
                "5": {
                    **self.region,
                    "id": 5,
                    "name": "Mã lô",
                    "xStart": 70,
                    "xEnd": 110,
                    "expected_text": "LOT 01",
                },
            }
        }

        result = judgment.run_summary(self.image, config)

        self.assertFalse(result["overall"])
        inspector_result = result["inspectors"][OCRTextDetector.INSPECTOR_NAME]
        self.assertEqual(inspector_result["runtime_data"]["total_boxes"], 2)
        self.assertEqual(inspector_result["runtime_data"]["matched_count"], 1)
        self.assertEqual(len(inspector_result["runtime_data"]["boxes"]), 2)


if __name__ == "__main__":
    unittest.main()
