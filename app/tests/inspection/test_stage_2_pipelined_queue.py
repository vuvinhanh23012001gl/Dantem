import unittest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Any
import time

from app.stages.stage_2_transform import StageTransform, InspectionTaskItem
from app.container import EnumMode


@dataclass
class DummyPreparedProduct:
    product_id: str
    frames: list[dict[str, Any]]
    scale_mm_per_pixel: float
    session_id: str
    number_step: int


class TestStage2PipelinedQueue(unittest.TestCase):
    """Kiểm tra chuyên sâu kiến trúc hàng đợi bất đồng bộ Producer-Consumer của Stage 2."""

    def setUp(self) -> None:
        self.mock_services = MagicMock()
        self.mock_services.obj_iai_config.move_retry_count = 1
        self.mock_services.obj_iai_config.move_timeout = 1.0
        self.mock_services.obj_iai_control.get_status.return_value.name = "AUTO"
        self.mock_services.runtime_state.is_stop_requested.return_value = False
        self.mock_services.obj_camera.capture_once.return_value = (True, MagicMock())
        self.mock_services.obj_judment.run_summary.return_value = {
            "status": "OK",
            "overall": True,
            "inspectors": {},
        }
        self.mock_services.obj_product_count_service.record_result.return_value = {
            "total": 1,
            "ok": 1,
            "ng": 0,
        }

    def _create_dummy_product(self, count: int = 3) -> DummyPreparedProduct:
        points = []
        for i in range(count):
            points.append({
                "point_id": str(i),
                "x": 1000 + i * 100,
                "y": 2000 + i * 100,
                "z": 3000 + i * 100,
                "judgment": {"ForeignObjectInspector": {}},
                "source": {},
            })
        return DummyPreparedProduct(
            product_id="test_prod_queue",
            frames=[{"frame_id": "0", "points": points}],
            scale_mm_per_pixel=0.05,
            session_id="session_queue_test",
            number_step=count,
        )

    def test_pipelined_execution_results_and_ordering(self) -> None:
        """Kiểm tra toàn bộ các point được xử lý và danh sách kết quả được sắp xếp đúng step."""
        prepared = self._create_dummy_product(count=4)
        self.mock_services.prepared_product = prepared
        self.mock_services.obj_iai_control.move_to_point.return_value = True

        stage = StageTransform(self.mock_services, queue_maxsize=2)

        with patch.object(stage, "_save_image", return_value="url/test.jpg"), \
             patch.object(stage, "_output_url", return_value="url/judgment.jpg"), \
             patch.object(stage, "_session_item_dir", return_value=MagicMock()):
            results = stage.run()

        self.assertEqual(len(results), 4, "Phải có đúng 4 kết quả item.")
        # Kiểm tra thứ tự các step luôn tăng dần: 1, 2, 3, 4
        steps = [r["step"] for r in results]
        self.assertEqual(steps, [1, 2, 3, 4], "Kết quả tổng hợp phải được sắp xếp theo đúng thứ tự step.")

        # Kiểm tra chuyển mode sang MODE_EXPORT
        self.mock_services.set_mode.assert_called_with(EnumMode.MODE_EXPORT)

    def test_backpressure_queue_blocking(self) -> None:
        """Kiểm tra cơ chế backpressure: queue đầy sẽ giữ luồng chụp đợi worker giải phóng."""
        prepared = self._create_dummy_product(count=5)
        self.mock_services.prepared_product = prepared
        self.mock_services.obj_iai_control.move_to_point.return_value = True

        stage = StageTransform(self.mock_services, queue_maxsize=1)

        def slow_summary(*args, **kwargs):
            time.sleep(0.01)
            return {"status": "OK", "overall": True, "inspectors": {}}

        self.mock_services.obj_judment.run_summary.side_effect = slow_summary

        with patch.object(stage, "_save_image", return_value="url/test.jpg"), \
             patch.object(stage, "_output_url", return_value="url/judgment.jpg"), \
             patch.object(stage, "_session_item_dir", return_value=MagicMock()):
            results = stage.run()

        self.assertEqual(len(results), 5, "Dù queue maxsize=1 vẫn phải xử lý trọn vẹn 5 items mà không rơi rớt.")

    def test_consumer_exception_handling(self) -> None:
        """Kiểm tra khi worker AI gặp ngoại lệ thì hệ thống ghi nhận NG và re-raise có kiểm soát."""
        prepared = self._create_dummy_product(count=2)
        self.mock_services.prepared_product = prepared
        self.mock_services.obj_iai_control.move_to_point.return_value = True

        self.mock_services.obj_judment.run_summary.side_effect = RuntimeError("AI Model VRAM Out")

        stage = StageTransform(self.mock_services, queue_maxsize=2)

        with patch.object(stage, "_save_image", return_value="url/test.jpg"), \
             patch.object(stage, "_output_url", return_value="url/judgment.jpg"), \
             patch.object(stage, "_session_item_dir", return_value=MagicMock()):
            with self.assertRaises(RuntimeError):
                stage.run()

        # Kiểm tra đã ghi nhận NG vào bộ đếm sản phẩm
        self.mock_services.obj_product_count_service.record_result.assert_called_with(False)


if __name__ == "__main__":
    unittest.main()
