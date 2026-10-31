import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from PIL import Image

from app.config import PatchCoreTrainConfig
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import PatchCoreTrainRecordRepository
from app.engines.train.patchcore_train_model.trainler import TrainlerPatchCore


def _create_roi_dataset(base_dir: Path):
    roi_dir = base_dir / "roi_demo"
    class_dir = roi_dir / "class_1"
    class_dir.mkdir(parents=True, exist_ok=True)

    for idx in range(2):
        image = Image.new("RGB", (8, 8), color=(idx * 50 + 20, idx * 20 + 10, 200))
        image.save(class_dir / f"sample_{idx}.png")

    return roi_dir


def test_trainler_patchcore_logic(tmp_path: Path):
    data_root = tmp_path / "train_data"
    record_root = tmp_path / "train_records"

    _create_roi_dataset(data_root)

    config = PatchCoreTrainConfig(
        img_size=8,
        batch_size=2,
        coreset_ratio=1.0,
        n_list=2,
        n_probe=1,
        num_workers=0,
        seed=42,
        crop_roi={"xStart": 2, "yStart": 2, "xEnd": 6, "yEnd": 6},
    )

    trainer = TrainlerPatchCore(config=config)
    trainer.record_manager = PatchCoreTrainRecordRepository(root_dir=record_root)

    trainer._build_backbone = lambda: (None, None, None, None)
    trainer._extract_features = staticmethod(
        lambda batch, device, layer2, layer3, layer4: np.ones((batch.shape[0], 4, 3), dtype=np.float32)
    )

    images = [
        Image.open(path).convert("RGB")
        for path in sorted((data_root / "roi_demo" / "class_1").glob("*.png"))
    ]
    record = trainer.run_from_folder(
        images,
        tmp_path / "model_output",
        roi_name="roi_demo",
    )

    assert Path(record["model_file"]).exists()
    assert Path(record["model_file"]).with_name("memory.npy").exists()
    manifest = trainer.record_manager.load_manifest()
    assert manifest
    assert manifest[0]["crop_roi"] == config.crop_roi


def main():
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as temp_dir:
        test_trainler_patchcore_logic(Path(temp_dir))
    print("PASS: test_logic_trainler_patchcore")


if __name__ == "__main__":
    main()
