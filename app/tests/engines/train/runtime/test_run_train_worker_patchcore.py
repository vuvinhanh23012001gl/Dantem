"""Runtime test cho TrainWorkerPatchCore."""
import sys
from pathlib import Path
from queue import Queue
PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from PIL import Image
from app.config import PatchCoreTrainConfig
from app.engines.train.patchcore_train_model import TrainWorkerPatchCore, TrainlerPatchCore

TRAIN_IMAGE_COUNT = 16


def test_run_train_worker_patchcore_runtime():
    """Chạy worker thật, nhận ảnh qua queue và trả kết quả qua queue.
    Returns:
        None: Kết thúc không lỗi khi thread xử lý đủ ảnh.
    Raises:
        AssertionError: Nếu worker không chạy đúng lifecycle hoặc sai kết quả.
        queue.Empty: Nếu worker không trả kết quả trong thời gian chờ.
    """
    image_queue = Queue()
    result_queue = Queue()
    worker = TrainWorkerPatchCore()
    config = PatchCoreTrainConfig(
        img_size=256,
        batch_size=4,
        coreset_ratio=0.2,
        n_list=2,
        n_probe=1,
        num_workers=0,
        device="cpu",
        crop_roi={
            "xStart": 100,
            "yStart": 100,
            "xEnd": 1330,
            "yEnd": 973,
        },
    )
    image_path = PROJECT_ROOT / "img_train_patchcore" / "176.jpg"
    image = Image.open(image_path).convert("RGB")
    images = [image.copy() for _ in range(TRAIN_IMAGE_COUNT)]

    worker.start(
        model_root=PROJECT_ROOT / "model_patch_core",
        roi_name="scratch",
        purpose="runtime train worker",
        image_count=TRAIN_IMAGE_COUNT,
        config=config,
        trainer_factory=TrainlerPatchCore,
        image_queue=image_queue,
        result_queue=result_queue,
    )
    for image in images:
        worker.submit_image(image)
    result = worker.get_result(timeout=600)
    worker.stop()
    assert result["ok"] is True
    record = result["record"]
    model_file = Path(record["model_file"])
    session_root = model_file.parent
    branch_root = session_root
    if session_root.name in {"the_first", "runtime"}:
        branch_root = session_root
        session_root = session_root.parent
    assert model_file.exists()
    assert (branch_root / "memory.npy").exists()
    assert len(list((branch_root / "good").glob("*.png"))) >= TRAIN_IMAGE_COUNT
    if branch_root.name == "the_first":
        assert len(list((branch_root / "original").glob("*.png"))) == TRAIN_IMAGE_COUNT
    assert (branch_root / "inference_result.png").exists()
    assert record["roi_list"] == ["scratch"]
    assert worker._thread is not None
    assert not worker._thread.is_alive()


def main():
    """Chạy runtime test độc lập không cần pytest.a

    Returns:
        None: In thông báo PASS khi test hoàn tất.

    Raises:
        AssertionError: Nếu runtime test thất bại.
    """
    test_run_train_worker_patchcore_runtime()
    print("PASS: test_run_train_worker_patchcore_runtime")


if __name__ == "__main__":
    main()
