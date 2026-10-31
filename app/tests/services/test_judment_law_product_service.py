import unittest
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from app.services import JudmentLawProductSevice
from app.repository.judment_law_product_reponsitory import JudmentLawProductRepository
from app.routers.api_tool_law_regulations import delete_product
from app.core import Result


class TestJudgmentLawProductService(unittest.TestCase):
    def test_partial_erase_notifies_runtime_of_changed_law_but_returns_failure(self):
        service = MagicMock()
        service.delete_product_data.return_value = Result(
            False, data={"law_deleted": True}, error="Partial cleanup",
        )
        services = SimpleNamespace(
            obj_law_regulation_service=service, notify_config_changed=MagicMock(),
        )
        response = delete_product({"product_id": 1}, services)
        self.assertFalse(response["ok"])
        self.assertEqual(response["message"], "Partial cleanup")
        services.notify_config_changed.assert_called_once_with("law_regulation_delete_product")

    def test_erase_law_write_failure_preserves_disk_and_backend_ram(self):
        with TemporaryDirectory() as directory:
            repo = JudmentLawProductRepository.__new__(JudmentLawProductRepository)
            repo.path = Path(directory) / "law.json"
            repo.data = {"1": {"0": {"3": {"OCRTextInspector": {}}}}, "2": {}}
            repo.save()
            before_disk = repo.path.read_bytes()
            before_ram = copy.deepcopy(repo.data)
            service = JudmentLawProductSevice(repo)
            with patch("app.repository.judment_law_product_reponsitory.os.replace", side_effect=OSError("disk locked")), patch.object(service, "_cleanup_patchcore_product") as cleanup:
                self.assertFalse(service.delete_product_data("1").ok)
                cleanup.assert_not_called()
            self.assertEqual(repo.path.read_bytes(), before_disk)
            self.assertEqual(repo.data, before_ram)
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])

    def test_save_covers_all_four_tools_and_preserves_other_product(self):
        names = ("StampItemInspector", "OCRTextInspector", "AnomalyPointInspector", "ForeignObjectInspector")
        payload = {"1": {"0": {"3": {name: {"0": {"id": 0, "name": name}} for name in names}}}}
        with TemporaryDirectory() as directory:
            repo = JudmentLawProductRepository.__new__(JudmentLawProductRepository)
            repo.path = Path(directory) / "law.json"
            repo.data = {"2": {"0": {"8": {"StampItemInspector": {}}}}}
            other = copy.deepcopy(repo.data["2"])
            service = JudmentLawProductSevice(repo)
            with patch.object(service, "_cleanup_orphaned_anomaly_point_rois"), patch.object(service, "_cleanup_orphaned_foreign_object_rois"):
                result = service.save_data(payload, {"1": {"0": {"3": {}}}})
            self.assertTrue(result.ok)
            saved = json.loads(repo.path.read_text(encoding="utf-8"))
            self.assertEqual(set(saved["1"]["0"]["3"]), set(names))
            self.assertEqual(saved["2"], other)

    def test_erase_removes_backend_law_and_owned_models_only_for_current_product(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repo = JudmentLawProductRepository.__new__(JudmentLawProductRepository)
            repo.path = root / "law.json"
            inspectors = {name: {} for name in ("StampItemInspector", "OCRTextInspector", "AnomalyPointInspector", "ForeignObjectInspector")}
            repo.data = {"1": {"0": {"3": inspectors}}, "2": {"0": {"4": inspectors}}}
            other = copy.deepcopy(repo.data["2"])
            manifests = [root / "anomaly.json", root / "foreign.json"]
            for path in manifests:
                path.write_text(json.dumps([{"product_id": "1"}, {"product_id": "2"}]), encoding="utf-8")
            model_root, output_root = root / "patch_core", root / "output"
            for base in (model_root, output_root):
                for product in ("1", "2"):
                    (base / product).mkdir(parents=True)
                    (base / product / "model.bin").write_bytes(b"keep other product")
            shared = root / "shared.pt"
            shared.write_bytes(b"shared")
            with patch.multiple(
                "app.services.judment_law_product_service",
                PATH_FOLDER_MODEL_DETECT_PATCH_CORE=model_root,
                PATH_FOLDER_IMG_COORDINATE_OUTPUT=output_root,
                PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST=manifests[0],
                PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST=manifests[1],
            ):
                service = JudmentLawProductSevice(repo)
                self.assertTrue(service.delete_product_data("1").ok)
                self.assertTrue(service.delete_product_data("1").ok, "Erasing an empty master is idempotent")
            self.assertEqual(json.loads(repo.path.read_text(encoding="utf-8")), {"2": other})
            for base in (model_root, output_root):
                self.assertFalse((base / "1").exists())
                self.assertEqual((base / "2" / "model.bin").read_bytes(), b"keep other product")
            for path in manifests:
                self.assertEqual(json.loads(path.read_text(encoding="utf-8")), [{"product_id": "2"}])
            self.assertEqual(shared.read_bytes(), b"shared")

    def test_erase_partial_cleanup_is_not_success(self):
        repo = MagicMock()
        repo.delete_product.return_value = True
        service = JudmentLawProductSevice(repo)
        def partial(product, report):
            report["patchcore"]["errors"].append("model locked")
        with patch.object(service, "_cleanup_patchcore_product", side_effect=partial):
            result = service.delete_product_data("1")
        self.assertFalse(result.ok)
        self.assertTrue(result.data["law_deleted"])
        self.assertIn("model locked", result.message())

    def test_erase_invalid_id_or_law_write_error_does_not_clean_models(self):
        repo = MagicMock()
        service = JudmentLawProductSevice(repo)
        with patch.object(service, "_cleanup_patchcore_product") as cleanup:
            self.assertFalse(service.delete_product_data("../2").ok)
            repo.delete_product.assert_not_called()
            repo.delete_product.side_effect = OSError("disk full")
            self.assertFalse(service.delete_product_data("1").ok)
            cleanup.assert_not_called()

    def test_save_data_migrates_legacy_anomaly_inspector_category(self):
        class FakeRepository:
            def update_data(self, data, save):
                self.saved_data = data

        service = JudmentLawProductSevice(FakeRepository())
        payload = {
            "1": {
                "0": {
                    "5": {
                        "EndChippingInspector": {
                            "xStart": 1,
                            "yStart": 2,
                            "xEnd": 30,
                            "yEnd": 40,
                            "thresholdNG": 0.4,
                        }
                    }
                }
            }
        }

        with (
            patch.object(service, "compare_structure", return_value=True),
            patch.object(service, "_cleanup_orphaned_anomaly_point_rois"),
            patch.object(service, "_cleanup_orphaned_foreign_object_rois"),
        ):
            result = service.save_data(payload, {})

        self.assertTrue(result.ok)
        saved_inspectors = service.repo.saved_data["1"]["0"]["5"]
        self.assertNotIn("EndChippingInspector", saved_inspectors)
        self.assertEqual(
            saved_inspectors["AnomalyPointInspector"]["thresholdNG"],
            0.4,
        )

    def test_partial_judgment_tree_is_valid(self):
        """Cho phép lưu các point có inspector mà không yêu cầu mọi point."""
        service = JudmentLawProductSevice(None)
        point_tree = {"1": {"0": {"0": {}, "1": {}, "2": {}}}}
        partial_payload = {
            "1": {
                "0": {
                    "0": {
                        "StampItemInspector": {
                            "0": {
                                "id": 0,
                                "name": "Tem 1",
                                "xStart": 10,
                                "yStart": 20,
                                "xEnd": 110,
                                "yEnd": 120,
                            }
                        }
                    },
                    "1": {"ScratchedPipeItemInspector": {"name": "Vết trầy xước"}},
                }
            }
        }

        self.assertTrue(service.compare_structure(partial_payload, point_tree))
        self.assertFalse(
            service.compare_structure(
                {"1": {"0": {"9": {"StampItemInspector": {}}}}},
                point_tree,
            )
        )


if __name__ == "__main__":
    unittest.main()
