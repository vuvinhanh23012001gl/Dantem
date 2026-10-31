import sys
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import PatchCoreTrainConfig
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import PatchCoreTrainRecordRepository


def test_run_patchcore_train_record_service():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        service = PatchCoreTrainRecordRepository(root_dir=temp_path / "records")
        config = PatchCoreTrainConfig(
            img_size=32,
            batch_size=8,
            coreset_ratio=0.2,
        )

        metadata = service.save_record(
            config=config,
            purpose="runtime check",
            roi_list=["air_bubble", "scratch"],
            model_file=temp_path / "model_patch_core" / "air_bubble" / "patchcore.index",
            status="completed",
        )

        assert metadata["status"] == "completed"
        assert metadata["roi_list"] == ["air_bubble", "scratch"]
        assert not (service.manifest_path.parent / metadata["run_id"]).exists()
        assert service.get_latest_run()["run_id"] == metadata["run_id"]


def main():
    test_run_patchcore_train_record_service()
    print("PASS: test_run_patchcore_train_record_service")


if __name__ == "__main__":
    main()
