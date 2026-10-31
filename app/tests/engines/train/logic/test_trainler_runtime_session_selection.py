"""Kiểm thử chọn và bảo toàn session có ảnh runtime."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import PatchCoreTrainConfig
from app.engines.train.patchcore_train_model.trainler import TrainlerPatchCore


def test_find_runtime_session_preserves_existing_session(tmp_path: Path):
    """Tìm đúng session có runtime/good và không chọn session the_first cũ.

    Returns:
        None: Kết thúc không lỗi khi session runtime được nhận diện.

    Raises:
        AssertionError: Nếu không tìm thấy đúng session runtime.
    """
    model_root = tmp_path / "model_patch_core"
    old_session = model_root / "model_scratch_crop_old"
    runtime_image = old_session / "runtime" / "good" / "image_0001.png"
    runtime_image.parent.mkdir(parents=True, exist_ok=True)
    runtime_image.write_bytes(b"runtime-image")

    trainer = TrainlerPatchCore(PatchCoreTrainConfig(device="cpu"))
    selected = trainer._find_runtime_session(model_root, "scratch")

    assert selected == old_session


def main():
    """Chạy test độc lập không cần pytest."""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as temp_dir:
        test_find_runtime_session_preserves_existing_session(Path(temp_dir))
    print("PASS: test_find_runtime_session_preserves_existing_session")


if __name__ == "__main__":
    main()
