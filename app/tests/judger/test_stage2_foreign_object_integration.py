"""Kiểm thử tích hợp luồng Stage 2 cho ForeignObjectInspector từ config_judgment_law.json.

Kiểm tra:
1. Cấu hình item 1/0/0 trong config_judgment_law.json chứa ForeignObjectInspector.
2. Judment.run_summary thực thi thành công với inspector này mà không bị lỗi:
   'Chưa có detector cho inspector ForeignObjectInspector'.
3. Mô hình PatchCore của point 1/0/0 được nạp động chính xác và phán định thành công.
"""

from pathlib import Path
import json
import sys
import unittest
from unittest.mock import MagicMock


import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import (
    PATH_FILE_MODEL_YOLO_FOREIGN,
    PATH_FOLDER_MODEL_DETECT_PATCH_CORE,
    YoloDetectObjectConfig,
)
from app.engines.model_AI import ModelYoloObject
from app.engines.service import ForeignObjectPatchCoreService
from app.judger import ForeignObjectDetector, Judment
from app.services import PointService
from app.repository import PointRepository


class TestStage2ForeignObjectIntegration(unittest.TestCase):
    """Kiểm tra tích hợp Judment với ForeignObjectInspector từ config_judgment_law.json."""

    def test_run_summary_with_foreign_object_inspector_from_config(self) -> None:
        config_path = PROJECT_ROOT / "app" / "storage" / "config_judgment_law.json"
        image_path = PROJECT_ROOT / "app" / "storage" / "img_points" / "1" / "0" / "0.jpg"

        self.assertTrue(config_path.exists(), f"Không tìm thấy file config: {config_path}")
        self.assertTrue(image_path.exists(), f"Không tìm thấy ảnh: {image_path}")

        with config_path.open("r", encoding="utf-8-sig") as f:
            full_config = json.load(f)

        item_config = full_config.get("1", {}).get("0", {}).get("0", {})
        self.assertIn(
            "ForeignObjectInspector",
            item_config,
            "Cấu hình 1/0/0 phải chứa ForeignObjectInspector",
        )

        image = cv2.imread(str(image_path))
        self.assertIsNotNone(image, "Không đọc được ảnh test")

        # Khởi tạo service và detector giống như trong ServiceContainer
        point_repo = PointRepository()
        point_service = PointService(point_repo)

        yolo_config = YoloDetectObjectConfig(
            path_model=PATH_FILE_MODEL_YOLO_FOREIGN,
            device="cpu",
            image_size=640,
            confidence=0.25,
            iou=0.45,
        )
        yolo_model = ModelYoloObject(yolo_config)

        foreign_service = ForeignObjectPatchCoreService(
            point_service=point_service,
            yolo_object_model=yolo_model,
        )

        foreign_detector = ForeignObjectDetector(foreign_service=foreign_service)

        judment = Judment({
            "ForeignObjectInspector": foreign_detector,
        })



        # Gọi run_summary với training_context y hệt Stage 2
        training_context = {
            "session_id": "session_test_integration",
            "product_id": "1",
            "frame_id": "0",
            "item_id": "0",
        }

        print("\n[TEST] Bắt đầu gọi judment.run_summary với cấu hình 1/0/0...")
        summary = judment.run_summary(
            image=image,
            inspectors=item_config,
            scale_mm_per_pixel=1.0,
            training_context=training_context,
        )

        print(f"[TEST] Kết quả tổng: overall={summary.get('overall')}, status={summary.get('status')}")
        self.assertIn("inspectors", summary)
        self.assertIn("ForeignObjectInspector", summary["inspectors"])

        foreign_res = summary["inspectors"]["ForeignObjectInspector"]
        print(f"[TEST] Kết quả ForeignObjectInspector: {foreign_res.get('status')} - {foreign_res.get('message')}")
        self.assertIn("status", foreign_res)
        self.assertIn(foreign_res["status"], {"OK", "NG"})
        self.assertNotIn("Chưa có detector cho inspector 'ForeignObjectInspector'", str(summary))


if __name__ == "__main__":
    unittest.main(verbosity=2)
