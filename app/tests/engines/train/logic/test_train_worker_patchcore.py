"""Kiểm thử worker queue của PatchCore."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.engines.train.patchcore_train_model.train_worker import TrainWorkerPatchCore


class FakeTrainer:
    """Trainer giả để kiểm tra giao tiếp queue mà không chạy model thật."""

    calls = []

    def __init__(self, config):
        self.config = config

    def run_from_folder(self, images, model_root, roi_name, purpose, model_variant="the_first"):
        self.__class__.calls.append(
            {
                "images": images,
                "model_root": model_root,
                "roi_name": roi_name,
                "purpose": purpose,
                "model_variant": model_variant,
            }
        )
        return {"run_id": "model_scratch_crop_test"}


def test_train_worker_waits_for_required_images():
    """Worker chỉ train sau khi nhận đủ image_count ảnh.

    Returns:
        None: Kết thúc không lỗi khi queue truyền đúng dữ liệu.

    Raises:
        AssertionError: Nếu worker train thiếu ảnh hoặc sai tham số.
    """
    FakeTrainer.calls.clear()
    worker = TrainWorkerPatchCore()
    worker.start(
        model_root="model_patch_core",
        roi_name="scratch",
        purpose="runtime worker test",
        image_count=2,
        trainer_factory=FakeTrainer,
    )
    worker.submit_image("image-1")
    assert FakeTrainer.calls == []
    worker.submit_image("image-2")

    result = worker.get_result(timeout=2)
    worker.stop()

    assert result == {"ok": True, "record": {"run_id": "model_scratch_crop_test"}}
    assert FakeTrainer.calls == [
        {
            "images": ["image-1", "image-2"],
            "model_root": "model_patch_core",
            "roi_name": "scratch",
            "purpose": "runtime worker test",
            "model_variant": "the_first",
        }
    ]


def main():
    """Chạy test worker độc lập không cần pytest."""
    test_train_worker_waits_for_required_images()
    print("PASS: test_train_worker_waits_for_required_images")


if __name__ == "__main__":
    main()
