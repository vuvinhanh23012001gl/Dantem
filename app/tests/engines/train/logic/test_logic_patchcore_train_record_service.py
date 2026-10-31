import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import PatchCoreTrainConfig
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import PatchCoreTrainRecordRepository


def test_patchcore_train_record_service_logic(tmp_path: Path):
    record_root = tmp_path / "patchcore_train_records"
    service = PatchCoreTrainRecordRepository(root_dir=record_root)

    config = PatchCoreTrainConfig(
        img_size=32,
        batch_size=4,
        coreset_ratio=0.5,
        n_list=8,
        n_probe=2,
    )

    metadata = service.save_record(
        config=config,
        purpose="train patchcore roi demo",
        roi_list=["roi_demo"],
        model_file=tmp_path / "model_patch_core" / "roi_demo" / "patchcore.index",
        status="completed",
    )

    assert metadata["run_id"].startswith("patchcore_")
    assert metadata["train_config"]["batch_size"] == 4
    assert metadata["model_file"].endswith("patchcore.index")

    manifest = service.load_manifest()
    assert len(manifest) == 1
    assert manifest[0]["run_id"] == metadata["run_id"]

    assert manifest[0]["train_config"]["img_size"] == 32
    assert manifest[0]["train_config"]["n_probe"] == 2


def main():
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as temp_dir:
        test_patchcore_train_record_service_logic(Path(temp_dir))
    print("PASS: test_logic_patchcore_train_record_service")


if __name__ == "__main__":
    main()
