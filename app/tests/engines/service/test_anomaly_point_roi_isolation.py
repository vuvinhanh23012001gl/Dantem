import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.engines.service.anomaly_point_patch_core_service import AnomalyPointPatchCoreService
from app.engines.service.patchcore_inspection_service import PatchCoreInspectionService
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordRepository,
)


class _FakeWorker:
    _thread = None


def _make_model(root: Path) -> Path:
    session = root / "model_anomaly_point_crop_20260101_000000_000001"
    (session / "the_first").mkdir(parents=True)
    (session / "runtime" / "good").mkdir(parents=True)
    index = session / "the_first" / "patchcore.index"
    index.write_bytes(b"x")
    (session / "runtime" / "good" / "a.png").write_bytes(b"png")
    return session


class TestAnomalyPointRoiIsolation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name) / "patch_core"
        self.manifest = Path(self.temp.name) / "manifest.json"
        patcher = patch(
            "app.engines.service.patchcore_inspection_service.PATH_FOLDER_MODEL_DETECT_PATCH_CORE",
            str(self.base),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        repo = PatchCoreTrainRecordRepository(manifest_path=self.manifest)
        with patch.object(
            AnomalyPointPatchCoreService, "__init__", lambda s, point_service: None
        ):
            self.service = AnomalyPointPatchCoreService(None)
        self.service.point_service = None
        self.service.roi_name = "anomaly_point"
        self.service.record_repository = repo
        self.service.worker = _FakeWorker()
        import threading
        self.service._cache_lock = threading.Lock()
        self.service._patchcore_cache = {}
        self.repo = repo

    def _add_roi(self, roi_id):
        root = self.base / "1" / "0" / "5" / f"roi_{roi_id}"
        session = _make_model(root)
        records = self.repo.load_manifest()
        records.append({"run_id": f"r{roi_id}", "model_root": str(session)})
        self.repo.save_manifest(records)
        return root, session

    def test_resolve_model_root_per_roi_and_legacy(self):
        resolve = PatchCoreInspectionService._resolve_model_root
        self.assertEqual(resolve(1, 0, 5), self.base / "1" / "0" / "5")
        self.assertEqual(resolve(1, 0, 5, 2).name, "roi_2")
        self.assertEqual(resolve(1, 0, 5, 2).parent, resolve(1, 0, 5))

    def test_models_are_isolated_per_roi(self):
        root0, _ = self._add_roi(0)
        root1, _ = self._add_roi(1)
        self.assertIsNotNone(self.service._find_latest_model(root0))
        self.assertIsNotNone(self.service._find_latest_model(root1))
        self.assertTrue(self.service.training_status(1, 0, 5, roi_id=0)["data"]["completed"])
        self.assertFalse(self.service.training_status(1, 0, 5, roi_id=2)["data"]["completed"])

        imgs0 = self.service.get_runtime_images(1, 0, 5, roi_id=0)
        self.assertEqual(len(imgs0["data"]["images"]), 1)

    def test_delete_model_roi0_keeps_roi1(self):
        root0, _ = self._add_roi(0)
        root1, _ = self._add_roi(1)
        result = self.service.delete_model(1, 0, 5, roi_id=0)
        self.assertTrue(result["ok"], result)
        self.assertFalse(root0.exists())
        self.assertTrue(root1.exists())
        remaining = self.repo.load_manifest()
        self.assertEqual([r["run_id"] for r in remaining], ["r1"])

    def test_delete_model_without_model_fails_cleanly(self):
        result = self.service.delete_model(1, 0, 5, roi_id=3)
        self.assertFalse(result["ok"])

    def test_get_patchcore_frame_missing_model_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.service.get_patchcore_frame(1, 0, 5, roi_id=7)


if __name__ == "__main__":
    unittest.main()
