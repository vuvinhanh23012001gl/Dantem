import unittest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Any
import threading
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


class TestStage2MultiWorkers(unittest.TestCase):
    """Kiểm tra chuyên sâu kiến trúc Multi-Worker Pool của Stage 2 (tối đa 5 worker song song)."""

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

    def _create_dummy_product(self, count: int = 5) -> DummyPreparedProduct:
        points = []
        for i in range(count):
            points.append({
                "point_id": str(i + 1),
                "x": 1000 + i * 100,
                "y": 2000 + i * 100,
                "z": 3000 + i * 100,
                "judgment": {"StampItemInspector": {}},
                "source": {},
            })
        return DummyPreparedProduct(
            product_id="test_prod_multi_worker",
            frames=[{"frame_id": "0", "points": points}],
            scale_mm_per_pixel=0.05,
            session_id="session_multi_worker_test",
            number_step=count,
        )

    def test_disabled_retrain_passes_empty_allowlist(self) -> None:
        """Khi retrain tắt, Stage 2 phải chặn lưu ảnh đầu vào retrain."""
        prepared = self._create_dummy_product(count=1)
        self.mock_services.obj_config_software = MagicMock()
        self.mock_services.obj_config_software.get_open_retrain.return_value = False
        self.mock_services.queue_manage_log = None
        stage = StageTransform(self.mock_services)
        task = InspectionTaskItem(
            prepared=prepared,
            frame={"frame_id": "0"},
            point={"point_id": "1", "x": 1000, "y": 2000, "z": 3000},
            step=1,
            image=object(),
            inspectors={},
        )

        with patch.object(stage, "_session_item_dir", return_value=MagicMock()), \
             patch.object(stage, "_output_url", return_value="url/judgment.jpg"), \
             patch.object(stage, "_save_judgment_result", return_value="url/judgment.jpg"):
            stage._execute_judgment_task(task)

        training_context = self.mock_services.obj_judment.run_summary.call_args.kwargs[
            "training_context"
        ]
        self.assertEqual(training_context["enabled_inspectors"], set())
        self.assertFalse(training_context["async_retrain"])
        self.mock_services.obj_config_software.get_enabled_retrain_inspectors.assert_not_called()

    def test_multi_worker_concurrency(self) -> None:
        """Kiểm tra tối đa 5 worker cùng chạy phán định AI song song."""
        prepared = self._create_dummy_product(count=5)
        self.mock_services.prepared_product = prepared
        self.mock_services.obj_iai_control.move_to_point.return_value = True

        stage = StageTransform(self.mock_services, queue_maxsize=5, max_judger_workers=5)

        active_workers = 0
        max_concurrent_seen = 0
        seen_thread_names = set()
        lock = threading.Lock()
        barrier = threading.Barrier(3)

        def slow_concurrent_summary(*args, **kwargs):
            nonlocal active_workers, max_concurrent_seen
            t_name = threading.current_thread().name
            with lock:
                seen_thread_names.add(t_name)
                active_workers += 1
                if active_workers > max_concurrent_seen:
                    max_concurrent_seen = active_workers

            try:
                barrier.wait(timeout=2.0)
            except (threading.BrokenBarrierError, Exception):
                pass

            time.sleep(0.01)

            with lock:
                active_workers -= 1

            return {"status": "OK", "overall": True, "inspectors": {}}

        self.mock_services.obj_judment.run_summary.side_effect = slow_concurrent_summary

        with patch("app.machine.anti_blur_service.AntiBlurService.evaluate_sharpness", return_value=(True, 200.0)), \
             patch.object(stage, "_save_image", return_value="url/test.jpg"), \
             patch.object(stage, "_output_url", return_value="url/judgment.jpg"), \
             patch.object(stage, "_session_item_dir", return_value=MagicMock()):
            results = stage.run()

        self.assertEqual(len(results), 5, "Phải xử lý đủ 5 items.")
        self.assertGreaterEqual(max_concurrent_seen, 3, "Phải có ít nhất 3 worker chạy đồng thời tại thời điểm Barrier.")
        judger_worker_names = {name for name in seen_thread_names if "Stage2JudgerWorker" in name}
        self.assertGreaterEqual(len(judger_worker_names), 3, "Phải có ít nhất 3 worker tham gia xử lý.")
        self.assertLessEqual(len(judger_worker_names), 5, "Số lượng worker không vượt quá max_judger_workers=5.")

    def test_multi_worker_results_ordering_with_varying_latencies(self) -> None:
        """Kiểm tra khi các worker hoàn tất lộn xộn thời gian, kết quả tổng hợp vẫn đúng thứ tự step 1..5."""
        prepared = self._create_dummy_product(count=5)
        self.mock_services.prepared_product = prepared
        self.mock_services.obj_iai_control.move_to_point.return_value = True

        stage = StageTransform(self.mock_services, queue_maxsize=5, max_judger_workers=5)

        latencies = {1: 0.05, 2: 0.03, 3: 0.02, 4: 0.01, 5: 0.005}

        def mock_varying_summary(image, inspectors, **kwargs):
            ctx = kwargs.get("training_context") or {}
            item_id = int(ctx.get("item_id", 1))
            delay = latencies.get(item_id, 0.01)
            time.sleep(delay)
            return {"status": "OK", "overall": True, "inspectors": {}}

        self.mock_services.obj_judment.run_summary.side_effect = mock_varying_summary

        with patch.object(stage, "_save_image", return_value="url/test.jpg"), \
             patch.object(stage, "_output_url", return_value="url/judgment.jpg"), \
             patch.object(stage, "_session_item_dir", return_value=MagicMock()):
            results = stage.run()

        self.assertEqual(len(results), 5)
        steps = [r["step"] for r in results]
        self.assertEqual(steps, [1, 2, 3, 4, 5], "Kết quả tổng hợp phải luôn luôn được sắp xếp theo step 1..5.")

    def test_multi_worker_error_propagation(self) -> None:
        """Kiểm tra khi 1 worker gặp lỗi exception, toàn bộ pool được dọn dẹp và lỗi được ném ra ngoài."""
        prepared = self._create_dummy_product(count=4)
        self.mock_services.prepared_product = prepared
        self.mock_services.obj_iai_control.move_to_point.return_value = True

        def failing_summary(*args, **kwargs):
            raise RuntimeError("CUDA Out of Memory on worker")

        self.mock_services.obj_judment.run_summary.side_effect = failing_summary

        stage = StageTransform(self.mock_services, queue_maxsize=5, max_judger_workers=5)

        with patch.object(stage, "_save_image", return_value="url/test.jpg"), \
             patch.object(stage, "_output_url", return_value="url/judgment.jpg"), \
             patch.object(stage, "_session_item_dir", return_value=MagicMock()):
            with self.assertRaises(RuntimeError) as ctx:
                stage.run()

        self.assertIn("CUDA Out of Memory", str(ctx.exception))
        self.mock_services.obj_product_count_service.record_result.assert_called_with(False)

    def test_multi_worker_fewer_items_than_max(self) -> None:
        """Kiểm tra khi sản phẩm chỉ có 2 item nhưng max_judger_workers=5, chỉ khởi tạo đúng 2 worker."""
        prepared = self._create_dummy_product(count=2)
        self.mock_services.prepared_product = prepared
        self.mock_services.obj_iai_control.move_to_point.return_value = True

        stage = StageTransform(self.mock_services, queue_maxsize=5, max_judger_workers=5)

        with patch.object(stage, "_save_image", return_value="url/test.jpg"), \
             patch.object(stage, "_output_url", return_value="url/judgment.jpg"), \
             patch.object(stage, "_session_item_dir", return_value=MagicMock()):
            results = stage.run()

        self.assertEqual(len(results), 2)
        self.assertEqual([r["step"] for r in results], [1, 2])

    def test_dynamic_workers_from_config_software(self) -> None:
        """Kiểm tra khi Config_SoftWare cấu hình max_judger_workers=8, Stage 2 áp dụng số worker này."""
        prepared = self._create_dummy_product(count=10)
        self.mock_services.prepared_product = prepared
        self.mock_services.obj_iai_control.move_to_point.return_value = True

        mock_config_sw = MagicMock()
        mock_config_sw.get_max_judger_workers.return_value = 8
        self.mock_services.obj_config_software = mock_config_sw

        stage = StageTransform(self.mock_services, queue_maxsize=10, max_judger_workers=5)

        seen_threads = set()
        lock = threading.Lock()

        def capture_thread_name(*args, **kwargs):
            with lock:
                seen_threads.add(threading.current_thread().name)
            return {"status": "OK", "overall": True, "inspectors": {}}

        self.mock_services.obj_judment.run_summary.side_effect = capture_thread_name

        with patch.object(stage, "_save_image", return_value="url/test.jpg"), \
             patch.object(stage, "_output_url", return_value="url/judgment.jpg"), \
             patch.object(stage, "_session_item_dir", return_value=MagicMock()):
            results = stage.run()

        self.assertEqual(len(results), 10)
        judger_worker_names = {name for name in seen_threads if "Stage2JudgerWorker" in name}
        self.assertLessEqual(len(judger_worker_names), 8)
        self.assertGreaterEqual(len(judger_worker_names), 5)

    def test_config_software_max_workers_validation(self) -> None:
        """Kiểm tra getter, setter và validation clamp 1..10 của max_judger_workers trong Config_SoftWare."""
        from app.services.log.config_software import Config_SoftWare

        default_cfg = Config_SoftWare.get_default_config()
        self.assertEqual(default_cfg.get("max_judger_workers"), 5, "Mặc định phải là 5 worker.")

        with patch("app.services.log.config_software.Folder.read_json_from_file", return_value={}):
            cfg = Config_SoftWare()
            self.assertEqual(cfg.get_max_judger_workers(), 5)

            cfg.set_max_judger_workers(10)
            self.assertEqual(cfg.get_max_judger_workers(), 10)
            self.assertEqual(cfg.to_dict()["max_judger_workers"], 10)

            cfg.set_max_judger_workers(15)
            self.assertEqual(cfg.get_max_judger_workers(), 10)

            cfg.set_max_judger_workers(0)
            self.assertEqual(cfg.get_max_judger_workers(), 1)

            cfg.set_max_judger_workers("invalid")
            self.assertEqual(cfg.get_max_judger_workers(), 5)


if __name__ == "__main__":
    unittest.main()
