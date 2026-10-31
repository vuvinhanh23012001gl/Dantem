import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np

from app.config import (
    ClassNameObjectStructureDetectConfig,
    PATH_FILE_MODEL_YOLO_STAMP,
    YoloDetectObjectConfig,
)
from app.engines.AI_model_process import FrameModelYoloObject
from app.engines.model_AI import ModelYoloObject
from app.engines.service import StructureFaceYoloService
from app.judger import Judment, StampDetector
from app.core import Result
from app.routers.api_tool_law_regulations import run_model_stamp


class FakeStampFrameModel:
    """Stub FrameModelYoloObject cho phép kiểm thử đơn vị từng trường hợp ROI có/không có nhãn 'stamp'."""

    def __init__(self, present_x_ranges: list[tuple[int, int]]):
        self.present_x_ranges = present_x_ranges

    def search(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int, label: str):
        cx = (x1 + x2) // 2
        for left, right in self.present_x_ranges:
            if left <= cx <= right:
                obj = {
                    "class_id": 0,
                    "class_name": label,
                    "confidence": 0.91,
                    "image_width": image.shape[1],
                    "image_height": image.shape[0],
                    "bbox": {
                        "x1": float(x1 + 10),
                        "y1": float(y1 + 10),
                        "x2": float(x2 - 10),
                        "y2": float(y2 - 10),
                    },
                }
                return True, [f"Phát hiện {label}"], image, [obj]
        return False, [f"Không phát hiện {label}"], image, []


class TestStampDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.image = np.zeros((480, 640, 3), dtype=np.uint8)
        self.boxes = [
            {"id": 0, "key": "0", "name": "Tem 1", "x1": 20, "y1": 40, "x2": 180, "y2": 160},
            {"id": 1, "key": "1", "name": "Tem 2", "x1": 220, "y1": 40, "x2": 380, "y2": 160},
            {"id": 2, "key": "2", "name": "Tem 3", "x1": 420, "y1": 40, "x2": 580, "y2": 160},
        ]

    def test_all_boxes_have_stamp_returns_ok(self) -> None:
        """Khi toàn bộ các khung vuông đều phát hiện >= 1 'stamp', kết quả item là OK."""
        fake_frame = FakeStampFrameModel([(0, 200), (200, 400), (400, 620)])
        detector = StampDetector(StructureFaceYoloService(fake_frame))

        result = detector.evaluate({"boxes": self.boxes}, self.image, self.boxes)

        self.assertTrue(result.ok)
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.errors, [])
        self.assertEqual(result.runtime_data["present_count"], 3)
        self.assertEqual(result.runtime_data["missing_count"], 0)
        self.assertIn("3/3", result.message)

    def test_master_api_runs_only_the_requested_roi(self) -> None:
        fake_frame = FakeStampFrameModel([(200, 400)])
        services = MagicMock()
        services.obj_point_service.get_path_img_point.return_value = Result.Ok("test.png")
        services.obj_structure_model_service = StructureFaceYoloService(fake_frame)
        services.CLASS_STRUCTURE_NAME = ClassNameObjectStructureDetectConfig
        with patch("app.routers.api_tool_law_regulations.cv2.imread", return_value=self.image), \
             patch.object(fake_frame, "search", wraps=fake_frame.search) as search:
            response = asyncio.run(run_model_stamp({
                "select": {"product_id": 1, "frame_id": 0, "items_id": 3},
                "boxes": [{"id": 1, "name": "Tem 2",
                           "xStart": 110, "yStart": 20, "xEnd": 190, "yEnd": 80}],
                "WidthCanvas": 320,
            }, services))
        self.assertTrue(response["ok"])
        self.assertEqual(len(response["data"]["boxes"]), 1)
        self.assertEqual(response["data"]["boxes"][0]["id"], 1)
        search.assert_called_once()
        self.assertEqual(search.call_args.args[1:5], (220, 40, 380, 160))

    def test_missing_stamp_in_any_box_returns_ng_with_exact_frame_names(self) -> None:
        """Khi >= 1 khung thiếu 'stamp', kết quả là NG và báo rõ tên từng khung thiếu."""
        fake_frame = FakeStampFrameModel([(200, 400)])
        detector = StampDetector(StructureFaceYoloService(fake_frame))

        result = detector.evaluate({"boxes": self.boxes}, self.image, self.boxes)

        self.assertFalse(result.ok)
        self.assertEqual(result.status, "NG")
        self.assertEqual(result.runtime_data["present_boxes"], ["Tem 2"])
        self.assertEqual(result.runtime_data["missing_boxes"], ["Tem 1", "Tem 3"])
        self.assertEqual(
            result.errors,
            [
                '[Kiểm tra tem] NG - Khung "Tem 1" - Quy định: "Có tem" - Thực tế: "Không có tem"',
                '[Kiểm tra tem] NG - Khung "Tem 3" - Quy định: "Có tem" - Thực tế: "Không có tem"',
            ],
        )

    def test_real_yolo_stamp_model_loaded_and_inference(self) -> None:
        """Nạp trực tiếp model thật object_stamp_detect.pt (không giả lập) và kiểm chứng suy luận thật."""
        self.assertTrue(
            Path(PATH_FILE_MODEL_YOLO_STAMP).exists(),
            f"Thiếu file model thật tại {PATH_FILE_MODEL_YOLO_STAMP}",
        )
        yolo_cfg = YoloDetectObjectConfig(
            path_model=str(PATH_FILE_MODEL_YOLO_STAMP),
            device="cpu",
        )
        yolo_model = ModelYoloObject(yolo_cfg)
        model_names = [str(v).strip().lower() for v in yolo_model.model.names.values()]
        self.assertIn(ClassNameObjectStructureDetectConfig.STAMP.value, model_names)

        service = StructureFaceYoloService(FrameModelYoloObject(yolo_model))
        detector = StampDetector(service)

        # Ảnh nền trung tính đồng nhất (114, 114, 114 - trùng màu đệm letterbox của YOLO, không tạo biên giả)
        neutral_img = np.full((480, 640, 3), 114, dtype=np.uint8)
        result = detector.evaluate({"boxes": self.boxes[:2]}, neutral_img, self.boxes[:2])

        self.assertFalse(result.ok)
        self.assertEqual(result.status, "NG")
        self.assertNotIn("is_mock", result.runtime_data)
        self.assertEqual(result.runtime_data["missing_boxes"], ["Tem 1", "Tem 2"])
        self.assertEqual(result.runtime_data["objects"], [])

    def test_judment_integration_overlay_and_multi_roi_retrain_crops(self) -> None:
        """Kiểm tra Judment.run_summary điều phối StampItemInspector, vẽ overlay xanh/đỏ và cắt ảnh retrain đa ROI."""
        fake_frame = FakeStampFrameModel([(0, 200)])
        detector = StampDetector(StructureFaceYoloService(fake_frame))
        judment = Judment({"StampItemInspector": detector})

        item_config = {
            "StampItemInspector": {
                "0": {
                    "id": 0,
                    "name": "Tem mã vạch",
                    "xStart": 20,
                    "yStart": 40,
                    "xEnd": 180,
                    "yEnd": 160,
                },
                "1": {
                    "id": 1,
                    "name": "Tem QC",
                    "xStart": 220,
                    "yStart": 40,
                    "xEnd": 380,
                    "yEnd": 160,
                },
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(Judment, "RETRAIN_OUTPUT_DIR", Path(temp_dir)):
                training_ctx = {
                    "product_id": "1",
                    "frame_id": "0",
                    "item_id": "4",
                    "session_id": "sess_stamp_test",
                    "enabled_inspectors": {"StampItemInspector"},
                    "async_retrain": False,
                }
                summary = judment.run_summary(
                    self.image,
                    item_config,
                    training_context=training_ctx,
                )

                self.assertFalse(summary["overall"])
                self.assertEqual(summary["status"], "NG")
                self.assertIn("StampItemInspector", summary["inspectors"])
                stamp_summary = summary["inspectors"]["StampItemInspector"]
                self.assertEqual(stamp_summary["status"], "NG")
                self.assertIn("Tem QC", stamp_summary["message"])

                saved_crops = sorted(Path(temp_dir).rglob("*.jpg"))
                self.assertEqual(len(saved_crops), 2)
                crop_names = [p.name for p in saved_crops]
                self.assertTrue(any("roi_01" in name for name in crop_names))
                self.assertTrue(any("roi_02" in name for name in crop_names))


if __name__ == "__main__":
    unittest.main()
