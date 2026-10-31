import csv
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from app.routers.api_tool_law_regulations import router
from app.services.judment_law_product_service import JudmentLawProductSevice
from app.services.capture_item_delete_service import CaptureItemDeleteService
from app.core import Result
from app.services.log.log_csv import Log_CSV, SESSION_DETAIL_HEADER
from app.services.retired_inspectors_migration import (
    RETIRED_INSPECTORS, RETIRED_WEIGHTS, migrate_retired_inspectors,
)


class RetirementTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "workspace"
        self.storage = self.root / "app" / "storage"
        self.storage.mkdir(parents=True)
        self.backup = self.base / "backup"
        self.law_path = self.storage / "config_judgment_law.json"
        self.law = {"1": {"0": {"3": {
            "ForeignObjectInspector": {"0": {"id": 0, "name": "Foreign"}},
            "AnomalyPointInspector": {"1": {"id": 1}},
            "StampItemInspector": {"2": {"id": 2}},
            **{name: {"0": {"id": 0}} for name in RETIRED_INSPECTORS},
        }}}}
        self.law_path.write_text(json.dumps(self.law), encoding="utf-8")
        for weight in RETIRED_WEIGHTS:
            path = self.root / "app" / "input" / "model" / weight
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"retired model")
        self.kept = self.root / "app" / "input" / "model" / "yolo" / "object_foreign_object.pt"
        self.kept.write_bytes(b"kept model")
        for name in (*RETIRED_INSPECTORS, "AnomalyPointInspector"):
            directory = self.root / "app" / "output" / "retrain" / name
            directory.mkdir(parents=True)
            (directory / "sample.png").write_bytes(b"sample")

    def test_dry_run_changes_nothing(self):
        before = self.law_path.read_bytes()
        report = migrate_retired_inspectors(self.root, self.backup)
        self.assertFalse(report["applied"])
        self.assertEqual(len(report["removed_config"]), 3)
        self.assertEqual(before, self.law_path.read_bytes())
        self.assertFalse(self.backup.exists())

    def test_apply_requires_stopped_app_confirmation(self):
        with self.assertRaisesRegex(ValueError, "Stop the application"):
            migrate_retired_inspectors(self.root, self.backup, apply=True)
        self.assertTrue(self.law_path.exists())

    def test_apply_preserves_shared_assets_and_verified_backup(self):
        report = migrate_retired_inspectors(self.root, self.backup, apply=True, app_stopped=True)
        self.assertTrue(report["applied"])
        inspectors = json.loads(self.law_path.read_text())["1"]["0"]["3"]
        self.assertEqual(set(inspectors), {"StampItemInspector", "AnomalyPointInspector", "ForeignObjectInspector"})
        self.assertEqual(self.kept.read_bytes(), b"kept model")
        self.assertTrue((self.root / "app" / "output" / "retrain" / "AnomalyPointInspector" / "sample.png").exists())
        manifest_path = Path(report["backup"]) / "manifest.json"
        for entry in json.loads(manifest_path.read_text())["files"]:
            saved = manifest_path.parent / entry["copy"]
            self.assertEqual(hashlib.sha256(saved.read_bytes()).hexdigest(), entry["sha256"])
        second = migrate_retired_inspectors(self.root, self.backup, apply=True, app_stopped=True)
        self.assertFalse(second["applied"])
        self.assertEqual(second["remove"], [])
        self.assertEqual(second["rewrite"], [])

    def test_failed_backup_does_not_remove_or_rewrite(self):
        before = self.law_path.read_bytes()
        with patch("app.services.retired_inspectors_migration._atomic_json", side_effect=OSError("backup full")):
            with self.assertRaisesRegex(OSError, "backup full"):
                migrate_retired_inspectors(self.root, self.backup, apply=True, app_stopped=True)
        self.assertEqual(before, self.law_path.read_bytes())
        self.assertTrue((self.root / "app" / "input" / "model" / RETIRED_WEIGHTS[0]).exists())

    def test_stale_master_save_is_rejected(self):
        repository = MagicMock()
        service = JudmentLawProductSevice(repository)
        result = service.save_data(self.law, self.law)
        self.assertFalse(result.ok)
        repository.update_data.assert_not_called()

    def test_retired_routes_are_absent_and_kept_routes_remain(self):
        paths = {route.path for route in router.routes}
        self.assertFalse(any("/air_bubbles/" in path or "/permeable_membrane/" in path or "/scratched_pipe/" in path for path in paths))
        self.assertIn("/law_regulation/stamp/run_model", paths)
        self.assertIn("/law_regulation/foreign_object/run_model", paths)
        self.assertIn("/law_regulation/anomaly_point/run_model", paths)

    def test_csv_new_schema_does_not_modify_legacy_csv(self):
        legacy = self.base / "session.csv"
        legacy.write_text("timestamp,status_air_bubble\nold,OK\n", encoding="utf-8-sig")
        before = legacy.read_bytes()
        logger = Log_CSV(self.base)
        target = logger.write_session_item("test", {"stamp_status": "OK"}, custom_file_path=legacy)
        self.assertNotEqual(target, legacy)
        self.assertEqual(legacy.read_bytes(), before)
        self.assertNotIn("status_air_bubble", SESSION_DETAIL_HEADER)
        with target.open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.reader(stream))
        self.assertEqual(rows[0], SESSION_DETAIL_HEADER)
        self.assertEqual(len(rows[0]), len(rows[1]))
        self.assertEqual(logger.write_session_item("test", {}, custom_file_path=legacy), target)

    def test_capture_delete_commit_and_rollback_preserve_other_inspectors(self):
        for failure_stage in (None, "persist", "cleanup"):
            with self.subTest(failure_stage=failure_stage):
                fail = failure_stage is not None
                app_dir = self.root / f"capture-{failure_stage or 'success'}"
                image = app_dir / "storage" / "img_points" / "1" / "0" / "3.jpg"
                image.parent.mkdir(parents=True)
                image.write_bytes(b"capture image")
                point = SimpleNamespace(
                    path_img_point=str(image.relative_to(app_dir)),
                    path_model_patch_core=None, path_img_retrain=None,
                )
                point_service = SimpleNamespace(points={1: {0: {3: point, 4: "other point"}}}, _save_points=MagicMock())
                repo = MagicMock()
                repo.data = {"1": {"0": {"3": {"ForeignObjectInspector": {}}, "4": {"StampItemInspector": {}}}}}
                calibration = SimpleNamespace(
                    calibrations={"1": {"0": SimpleNamespace(id_tems=3)}},
                    _sync_to_repository=MagicMock(),
                )
                manifests = [app_dir / "anomaly.json", app_dir / "foreign.json"]
                for manifest in manifests:
                    manifest.write_text(json.dumps([
                        {"id": item, "model_root": str(app_dir / "patch_core" / "1" / "0" / str(item))}
                        for item in (3, 4)
                    ]), encoding="utf-8")
                if failure_stage == "persist":
                    repo.save.side_effect = [OSError("disk full"), None]
                with patch.multiple(
                    "app.services.capture_item_delete_service",
                    BASE_DIR=app_dir,
                    PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST=str(app_dir / "anomaly.json"),
                    PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST=str(app_dir / "foreign.json"),
                ):
                    service = CaptureItemDeleteService(point_service, SimpleNamespace(repo=repo), calibration)
                    cleanup_result = Result.Fail("cleanup failed") if failure_stage == "cleanup" else Result.Ok({"technical_report": []})
                    service.cleanup_empty_frame_structure = MagicMock(return_value=cleanup_result)
                    result = service.delete_capture_item(1, 0, 3)
                self.assertEqual(result.ok, not fail)
                self.assertEqual(image.exists(), fail)
                self.assertEqual(3 in point_service.points[1][0], fail)
                self.assertEqual("3" in repo.data["1"]["0"], fail)
                self.assertEqual(repo.data["1"]["0"]["4"], {"StampItemInspector": {}})
                self.assertEqual(point_service.points[1][0][4], "other point")
                self.assertEqual("1" in calibration.calibrations, fail)
                for manifest in manifests:
                    self.assertEqual(
                        [record["id"] for record in json.loads(manifest.read_text(encoding="utf-8"))],
                        [3, 4] if fail else [4],
                    )


if __name__ == "__main__":
    unittest.main()
