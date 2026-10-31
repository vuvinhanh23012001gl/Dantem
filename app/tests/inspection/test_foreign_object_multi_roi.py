"""Regression tests for foreign-object regions, API context and model ownership."""

import asyncio
import os
from pathlib import Path
from queue import Queue
import shutil
from tempfile import TemporaryDirectory
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from app.core import Result
from app.engines.model_AI import ModelPatchCore
from app.engines.service.foreign_object_patch_core_service import ForeignObjectPatchCoreService
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordRepository,
)
from app.judger import ForeignObjectDetector, Judment
from app.routers import api_tool_law_regulations as api
from app.services.judment_law_product_service import JudmentLawProductSevice


def region(roi_id, **changes):
    return {
        "id": roi_id, "name": f"Region {roi_id}", "x1": 10 + roi_id * 40,
        "y1": 10, "x2": 40 + roi_id * 40, "y2": 40,
        "threshold": 0.1 + roi_id * 0.1, "saveRuntimeImages": False, **changes,
    }


def config_region(roi_id):
    box = region(roi_id)
    return {
        **box, "xStart": box["x1"], "yStart": box["y1"],
        "xEnd": box["x2"], "yEnd": box["y2"],
    }


class MultiRegionDetectorTests(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((120, 120, 3), dtype=np.uint8)
        self.service = MagicMock()
        self.engines = [MagicMock(), MagicMock()]
        for engine in self.engines:
            engine.detect_anomaly_objects_with_heatmap.return_value = {
                "score": 0.05, "detections": [], "anomaly_boxes": [],
            }
        self.service.get_detector_engine.side_effect = lambda *args, roi_id: self.engines[int(roi_id)]
        self.detector = ForeignObjectDetector(foreign_service=self.service)
        self.context = {"product_id": 1, "frame_id": 0, "item_id": 3}

    def evaluate_regions(self, boxes=None):
        return self.detector.evaluate({}, self.image, boxes or [region(0), region(1)], **self.context)

    def test_all_regions_ok_and_legacy_thresholds_are_ignored(self):
        result = self.evaluate_regions()
        self.assertTrue(result.ok)
        self.assertEqual(len(result.runtime_data["boxes"]), 2)
        for i, engine in enumerate(self.engines):
            self.assertNotIn("threshold", engine.detect_anomaly_objects_with_heatmap.call_args.kwargs)
        self.assertEqual(self.service.get_detector_engine.call_args_list[1].kwargs, {"roi_id": 1})

    def test_missing_model_is_ng_and_other_regions_still_run(self):
        self.service.get_detector_engine.side_effect = [FileNotFoundError("missing"), self.engines[1]]
        result = self.evaluate_regions()
        self.assertFalse(result.ok)
        self.assertIn('Chưa tạo model PatchCore cho vùng "Region 0"', result.message)
        self.assertEqual(len(result.errors), 1)
        self.engines[1].detect_anomaly_objects_with_heatmap.assert_called_once()

    def test_yolo_detection_identifies_only_failed_region(self):
        self.engines[1].detect_anomaly_objects_with_heatmap.return_value = {
            "score": 0.8, "detections": [{"class_name": "dust"}], "anomaly_boxes": [],
        }
        result = self.evaluate_regions()
        self.assertFalse(result.ok)
        self.assertIn("Region 1", result.errors[0])
        self.assertNotIn("Region 0", result.errors[0])
        self.assertTrue(result.comparison_data["box_comparisons"][0]["ok"])

    def test_high_patchcore_score_without_yolo_is_ok(self):
        self.engines[0].detect_anomaly_objects_with_heatmap.return_value["score"] = 0.95
        self.assertTrue(self.evaluate_regions().ok)

    def test_yolo_below_threshold_is_still_ng(self):
        self.engines[0].detect_anomaly_objects_with_heatmap.return_value["detections"] = [
            {"class_name": "dust"}
        ]
        self.assertFalse(self.evaluate_regions().ok)

    def test_runtime_images_are_saved_only_for_enabled_region(self):
        with patch("app.judger.foreign_object_detector.threading.Thread") as thread:
            self.evaluate_regions([region(0), region(1, saveRuntimeImages=True)])
        self.assertEqual(thread.call_count, 1)
        self.assertEqual(thread.call_args.kwargs["kwargs"], {"roi_id": 1})
        self.assertEqual(thread.call_args.kwargs["args"][3].shape, (30, 30, 3))

    def test_runtime_save_concurrency_is_bounded_and_reports_saturation(self):
        with patch("app.judger.foreign_object_detector.threading.Thread") as thread, \
             self.assertLogs("app.judger.foreign_object_detector", level="WARNING"):
            for _ in range(5):
                self.evaluate_regions([region(0, saveRuntimeImages=True)])
        self.assertEqual(thread.call_count, 4)

    def test_runtime_save_error_is_logged_and_releases_capacity(self):
        self.service.save_runtime_image_for_training.side_effect = OSError("disk full")
        self.detector._runtime_save_slots.acquire()
        with self.assertLogs("app.judger.foreign_object_detector", level="ERROR"):
            self.detector._save_runtime_crop(1, 0, 3, self.image, roi_id=1)
        acquired = [self.detector._runtime_save_slots.acquire(blocking=False) for _ in range(4)]
        self.assertTrue(all(acquired))

    def test_inference_file_errors_are_not_reported_as_missing_models(self):
        self.engines[0].detect_anomaly_objects_with_heatmap.side_effect = FileNotFoundError("YOLO input")
        with self.assertRaisesRegex(FileNotFoundError, "YOLO input"):
            self.evaluate_regions()

    def test_training_input_crops_support_multi_region_and_legacy_calls(self):
        for args, count in [(([region(0), region(1)],), 2), ((10, 10, 40, 40), 1)]:
            with self.subTest(args=args), \
                 patch.object(Judment, "RETRAIN_OUTPUT_DIR", "test-output"), \
                 patch("app.judger.judment.Tool_OpenCv2.save_training_input", return_value=Path("crop.png")) as save:
                paths = Judment._save_training_inputs(self.image, "ForeignObjectInspector", args)
                self.assertEqual(len(paths), count)
                self.assertEqual(save.call_count, count)
                self.assertEqual(save.call_args.args[0].shape, (30, 30, 3))

    def test_legacy_coordinate_and_keyword_calls(self):
        for args, kwargs in [
            ((10, 10, 40, 40), {}),
            ((), {"x1": 10, "y1": 10, "x2": 40, "y2": 40}),
        ]:
            runtime = self.detector.define(self.image, *args, **kwargs, **self.context)
            self.assertEqual(runtime["score"], 0.05)
            self.assertTrue(self.detector.judge(self.detector.compare(0.2, runtime)).ok)

    def test_empty_and_invalid_regions_are_rejected(self):
        with self.assertRaises(ValueError):
            self.detector.define(self.image, [], **self.context)
        for box in (region(0, x2=5), region(0, x1=-1), region(0, x2=500)):
            with self.assertRaises(ValueError):
                self.evaluate_regions([box])

    def test_config_tasks_and_overlay_cover_both_regions(self):
        config = {str(i): config_region(i) for i in range(2)}
        tasks = Judment._tasks_from_config(
            {"ForeignObjectInspector": config},
            {"ForeignObjectInspector": self.detector}, 1.0, self.context,
        )
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].overlay_labels, ("Region 0", "Region 1"))
        self.assertTrue(all("threshold" not in box for box in tasks[0].define_args[0]))
        runtime = self.detector.define(self.image, *tasks[0].define_args, **tasks[0].define_kwargs)
        comparison = self.detector.compare(tasks[0].standard_data, runtime)
        result = self.detector.judge(comparison)
        _, overlay = Judment._render_inspector_overlay(
            self.image, "ForeignObjectInspector", tasks[0].standard_data,
            tasks[0].define_args, runtime, comparison, result, tasks[0].overlay_labels,
        )
        self.assertEqual(overlay["standard"]["labels"], ["Region 0", "Region 1"])

    def test_legacy_config_normalizes_id_zero(self):
        tasks = Judment._tasks_from_config(
            {"ForeignObjectInspector": {**config_region(0), "id": 77}},
            {"ForeignObjectInspector": self.detector}, 1.0, self.context,
        )
        self.assertEqual(tasks[0].define_args[0][0]["id"], 0)

    def test_summary_is_ng_with_missing_region_name(self):
        config = {str(i): config_region(i) for i in range(2)}
        self.service.get_detector_engine.side_effect = [self.engines[0], FileNotFoundError("missing")]
        with patch.object(Judment, "_save_training_inputs", return_value=[]):
            summary = Judment({"ForeignObjectInspector": self.detector}).run_summary(
                self.image, {"ForeignObjectInspector": config}, training_context=self.context,
            )
        self.assertEqual(summary["status"], "NG")
        self.assertIn("Region 1", summary["errors"][0]["message"])
        self.assertEqual(summary["overlay_data"]["ForeignObjectInspector"]["standard"]["labels"],
                         ["Region 0", "Region 1"])


class ModelStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for module in (
            "app.engines.service.foreign_object_patch_core_service",
            "app.engines.service.patchcore_inspection_service",
        ):
            patcher = patch(f"{module}.PATH_FOLDER_MODEL_DETECT_PATCH_CORE", self.root)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.service = ForeignObjectPatchCoreService.__new__(ForeignObjectPatchCoreService)
        self.service.roi_name = "foreign"
        self.service._patchcore_cache = {}
        self.service._cache_lock = threading.Lock()
        self.service.record_repository = PatchCoreTrainRecordRepository(root_dir=self.root)
        self.service.worker = MagicMock(_thread=None, result_queue=Queue())
        self.service._training_context = None
        self.service._training_result = None

    def model(self, roi_id=None, prefix="foreign"):
        root = self.root / "1" / "0" / "3"
        if roi_id is not None:
            root /= f"roi_{roi_id}"
        session = root / f"model_{prefix}_crop_20261031"
        file = session / "the_first" / "patchcore.index"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"test index")
        self.service.record_repository.save_record(None, "test", model_root=session, model_file=file)
        return session

    def cleanup_patches(self):
        from contextlib import ExitStack
        stack = ExitStack()
        for name, value in {
            "PATH_FOLDER_MODEL_DETECT_PATCH_CORE": self.root,
            "PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST": self.service.record_repository.manifest_path,
            "PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST": self.root / "anomaly_manifest.json",
        }.items():
            stack.enter_context(patch(f"app.services.judment_law_product_service.{name}", value))
        return stack

    def test_patchcore_preview_ignores_legacy_threshold_and_has_no_verdict(self):
        module = "app.engines.service.patchcore_inspection_service"
        with patch(f"{module}.PatchCoreInspectionService.run_model", return_value={
            "ok": True, "data": {"score": 0.9, "boxes": [{}], "status": "NG"},
        }) as run:
            result = self.service.run_model(1, 0, 3, {
                "xStart": 0, "yStart": 0, "xEnd": 30, "yEnd": 30, "threshold": "obsolete",
            }, 120, roi_id=7)
        self.assertNotIn("threshold", run.call_args.args[3])
        self.assertEqual(run.call_args.args[-1], 7)
        self.assertNotIn("status", result["data"])
        self.assertEqual(result["data"]["stage"], "anomaly_localization")

    def test_object_api_judges_detections_not_score_or_legacy_threshold(self):
        self.model(0)
        self.service._inference_lock = threading.Lock()
        self.service.point_service = MagicMock()
        self.service.point_service.get_path_img_point.return_value = Result.Ok("test.png")
        self.service.yolo_object_model = MagicMock()
        self.service._save_retrain_input = MagicMock()
        module = "app.engines.service.foreign_object_patch_core_service"
        image = np.zeros((60, 60, 3), dtype=np.uint8)
        for score, detections in [(0.01, [{"class_name": "dust"}]), (0.99, [])]:
            with self.subTest(score=score), \
                 patch(f"{module}.cv2.imread", return_value=image), \
                 patch(f"{module}.faiss.read_index", return_value=SimpleNamespace(nlist=1)), \
                 patch(f"{module}.ModelPatchCore") as model_class, \
                 patch(f"{module}.FrameModelPatchCore"), \
                 patch(f"{module}.FramePatchCoreObjectDetector") as engine:
                model = model_class.return_value
                model.predict.return_value = (score, image)
                model.get_bounding_boxes.return_value = [(2, 2, 20, 20)]
                engine.return_value.detect_anomaly_objects.return_value = detections
                result = self.service.run_model_with_object_detection(
                    1, 0, 3, {"xStart": 0, "yStart": 0, "xEnd": 60, "yEnd": 60,
                              "threshold": "obsolete"}, roi_id=0,
                )
                self.assertTrue(result["ok"])
                self.assertEqual(result["data"]["status"], "NG" if detections else "OK")
                self.assertEqual(model.predict.call_args.kwargs, {})
                engine.return_value.detect_anomaly_objects.assert_called_once()
                model.unload.assert_called_once()
                self.assertFalse(self.service._inference_lock.locked())

    def test_legacy_model_only_visible_to_zero_and_new_writes_are_scoped(self):
        legacy = self.model()
        root = self.service._resolve_model_root(1, 0, 3, 0)
        self.assertEqual(root.name, "roi_0")
        self.assertIsNotNone(self.service._find_latest_model(root))
        self.assertIsNone(self.service._find_latest_model(self.service._resolve_model_root(1, 0, 3, 1)))
        self.assertEqual(self.service._get_record_session_root(1, 0, 3, 0), legacy)

    def test_region_model_preferred_even_when_legacy_exists(self):
        self.model()
        current = self.model(0)
        self.assertTrue(self.service._find_latest_model(
            self.service._resolve_model_root(1, 0, 3, 0)
        ).is_relative_to(current))

    def test_deleting_model_keeps_other_regions_and_inspectors(self):
        target = self.model(0)
        legacy = self.model()
        other = self.model(1)
        anomaly = self.model(0, "anomaly_point")
        self.assertTrue(self.service.delete_model(1, 0, 3, roi_id=0)["ok"])
        self.assertFalse(target.exists())
        self.assertFalse(legacy.exists())
        self.assertTrue(other.exists())
        self.assertTrue(anomaly.exists())
        self.assertEqual(len(self.service.record_repository.load_manifest()), 2)

    def test_invalid_roi_ids_are_rejected(self):
        for value in ("../1", -1, True):
            with self.assertRaises(ValueError):
                self.service._resolve_model_root(1, 0, 3, value)

    def test_cache_invalidation_is_region_scoped(self):
        frames = [MagicMock(), MagicMock()]
        self.service._patchcore_cache = {
            ("1", "0", "3", str(i)): (Path("index"), 1, frame) for i, frame in enumerate(frames)
        }
        self.service.invalidate_cache(1, 0, 3, 0)
        frames[0].model.unload.assert_called_once()
        frames[1].model.unload.assert_not_called()
        self.assertEqual(len(self.service._patchcore_cache), 1)
        self.service.invalidate_cache(1, 0, 3)
        self.assertFalse(self.service._patchcore_cache)

    def test_model_cache_reloads_same_path_after_retraining(self):
        sessions = [self.model(0), self.model(1)]
        module = "app.engines.service.foreign_object_patch_core_service"
        with patch(f"{module}.faiss.read_index"), \
             patch(f"{module}.faiss.extract_index_ivf", return_value=SimpleNamespace(nlist=1)), \
             patch(f"{module}.ModelPatchCore", side_effect=lambda config: MagicMock(spec=ModelPatchCore)) as models:
            first = self.service.get_patchcore_frame(1, 0, 3, 0)
            other = self.service.get_patchcore_frame(1, 0, 3, 1)
            self.assertIs(first, self.service.get_patchcore_frame(1, 0, 3, 0))
            self.assertIsNot(first, other)
            index = sessions[0] / "the_first" / "patchcore.index"
            modified = index.stat().st_mtime_ns + 1000000000
            os.utime(index, ns=(modified, modified))
            self.assertIsNot(first, self.service.get_patchcore_frame(1, 0, 3, 0))
            first.model.unload.assert_called_once()
            other.model.unload.assert_not_called()
            self.assertEqual(models.call_count, 3)

    def test_training_failure_does_not_report_old_model_success(self):
        self.model(0)
        self.service._training_context = ("1", "0", "3", "0")
        self.service.worker.result_queue.put({"ok": False, "error": ValueError("train failed")})
        status = self.service.training_status(1, 0, 3, 0)
        self.assertFalse(status["ok"])
        self.assertIn("train failed", status["message"])

    def test_model_deletion_clears_previous_training_failure(self):
        self.model(0)
        self.service._training_context = ("1", "0", "3", "0")
        self.service._training_result = {"ok": False, "error": ValueError("train failed")}
        self.assertTrue(self.service.delete_model(1, 0, 3, roi_id=0)["ok"])
        self.assertIsNone(self.service._training_context)
        self.assertIsNone(self.service._training_result)
        status = self.service.training_status(1, 0, 3, 0)
        self.assertTrue(status["ok"])
        self.assertFalse(status["data"]["completed"])

    def test_runtime_image_operations_are_region_scoped(self):
        sessions = [self.model(0), self.model(1)]
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        for i in range(2):
            self.service.save_runtime_image_for_training(1, 0, 3, image, roi_id=i)
        images = self.service.get_runtime_images(1, 0, 3, roi_id=0)["data"]["images"]
        self.assertEqual(len(images), 1)
        self.service.delete_runtime_image(1, 0, 3, images[0]["name"], roi_id=0)
        self.assertFalse(list((sessions[0] / "runtime" / "good").glob("*.png")))
        self.assertEqual(len(list((sessions[1] / "runtime" / "good").glob("*.png"))), 1)

    def test_cleanup_keeps_other_inspector_sessions(self):
        foreign = self.model(0)
        anomaly = self.model(0, "anomaly_point")
        retained = self.model(1)
        data = {"1": {"0": {"3": {
            "ForeignObjectInspector": {"1": {"id": 1}},
            "AnomalyPointInspector": {"0": {"id": 0}},
        }}}}
        with self.cleanup_patches():
            JudmentLawProductSevice._cleanup_orphaned_anomaly_point_rois(data)
            JudmentLawProductSevice._cleanup_orphaned_foreign_object_rois(data)
        self.assertFalse(foreign.exists())
        self.assertTrue(anomaly.exists())
        self.assertTrue(retained.exists())

    def test_cleanup_is_deferred_until_master_save(self):
        target = self.model(0)
        repo = MagicMock()
        service = JudmentLawProductSevice(repo)
        data = {"1": {"0": {"3": {}}}}
        self.assertTrue(target.exists())
        with self.cleanup_patches():
            self.assertTrue(service.save_data(data, data).ok)
        repo.update_data.assert_called_once()
        self.assertFalse(target.exists())

    def test_save_failure_never_deletes_models(self):
        target = self.model(0)
        service = JudmentLawProductSevice(MagicMock())
        service.repo.update_data.side_effect = OSError("disk full")
        data = {"1": {"0": {"3": {}}}}
        with self.cleanup_patches():
            self.assertFalse(service.save_data(data, data).ok)
        self.assertTrue(target.exists())

    def test_cleanup_failure_is_reported_instead_of_success(self):
        self.model(0)
        service = JudmentLawProductSevice(MagicMock())
        data = {"1": {"0": {"3": {}}}}
        with self.cleanup_patches(), \
             patch("app.services.judment_law_product_service.shutil.rmtree", side_effect=OSError("locked")):
            result = service.save_data(data, data)
        self.assertFalse(result.ok)
        self.assertIn("Đã lưu master", result.message())

    def test_failed_runtime_image_write_raises(self):
        self.model(0)
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        with patch("app.engines.service.foreign_object_patch_core_service.cv2.imwrite", return_value=False):
            with self.assertRaises(OSError):
                self.service.save_runtime_image_for_training(1, 0, 3, image, roi_id=0)

    def test_cleanup_removes_manifest_records_with_missing_folder(self):
        target = self.model(0)
        shutil.rmtree(target)
        with self.cleanup_patches():
            JudmentLawProductSevice._cleanup_orphaned_foreign_object_rois({"1": {"0": {"3": {}}}})
        self.assertEqual(self.service.record_repository.load_manifest(), [])

    def test_legacy_config_keeps_region_zero_model_during_cleanup(self):
        target = self.model()
        data = {"1": {"0": {"3": {"ForeignObjectInspector": config_region(0)}}}}
        with self.cleanup_patches():
            JudmentLawProductSevice._cleanup_orphaned_anomaly_point_rois(data)
            JudmentLawProductSevice._cleanup_orphaned_foreign_object_rois(data)
        self.assertTrue(target.exists())

    def test_multi_region_coordinates_are_converted_independently(self):
        service = JudmentLawProductSevice(MagicMock())
        point_service = MagicMock()
        point_service.get_path_img_point.return_value = Result.Ok("test.png")
        payload = {"1": {"0": {"3": {"ForeignObjectInspector": {
            str(i): config_region(i) for i in range(2)
        }}}}}
        with patch("app.services.judment_law_product_service.cv2.imread",
                   return_value=np.zeros((200, 400, 3), dtype=np.uint8)):
            result = service.convert_canvas_coordinates(payload, 1, point_service, 200, 100)
        self.assertTrue(result.ok)
        boxes = result.data["1"]["0"]["3"]["ForeignObjectInspector"]
        self.assertEqual(boxes["0"]["xStart"], 20)
        self.assertEqual(boxes["1"]["xStart"], 100)
        self.assertEqual(boxes["1"]["coordinateSpace"], "image")


class RegionApiTests(unittest.TestCase):
    def test_body_endpoints_forward_selected_roi(self):
        endpoints = [
            (api.create_foreign_object_model, "create_model"),
            (api.run_foreign_object_model, "run_model"),
            (api.run_foreign_object_detection_model, "run_model_with_object_detection"),
            (api.delete_foreign_object_model, "delete_model"),
            (api.delete_foreign_object_runtime_image, "delete_runtime_image"),
        ]
        for endpoint, method in endpoints:
            with self.subTest(method=method):
                services = MagicMock()
                data = {"product_id": 1, "frame_id": 0, "item_id": 3, "roi_id": 7,
                        "crop_roi": {}, "image_name": "image.png"}
                asyncio.run(endpoint(data=data, services=services))
                self.assertEqual(
                    getattr(services.obj_foreign_object_patch_core_service, method).call_args.kwargs["roi_id"],
                    7,
                )

    def test_query_endpoints_forward_selected_roi(self):
        for endpoint, method in [
            (api.foreign_object_train_status, "training_status"),
            (api.foreign_object_runtime_images, "get_runtime_images"),
        ]:
            services = MagicMock()
            asyncio.run(endpoint(product_id=1, frame_id=0, face_id=None, item_id=3,
                                 roi_id=9, services=services))
            self.assertEqual(
                getattr(services.obj_foreign_object_patch_core_service, method).call_args.kwargs["roi_id"], 9
            )

    def test_missing_roi_defaults_to_zero(self):
        services = MagicMock()
        asyncio.run(api.delete_foreign_object_model(
            {"product_id": 1, "frame_id": 0, "item_id": 3}, services
        ))
        self.assertEqual(
            services.obj_foreign_object_patch_core_service.delete_model.call_args.kwargs["roi_id"], 0
        )


if __name__ == "__main__":
    unittest.main()
