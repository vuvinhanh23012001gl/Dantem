"""Runtime test TrainlerPatchCore tren du lieu truc tiep trong workspace."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
from PIL import Image

from app.config import PatchCoreAnomalyConfig
from app.config import PatchCoreTrainConfig
from app.engines.model_AI import ModelPatchCore
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordRepository,
)
from app.engines.train.patchcore_train_model.trainler import TrainlerPatchCore


def _crop_image(image: np.ndarray, crop_roi: dict) -> np.ndarray:
    """Crop ảnh inference theo cùng tọa độ đã dùng khi train.

    Args:
        image: Ảnh BGR đọc bằng OpenCV.
        crop_roi: Tọa độ xStart, yStart, xEnd, yEnd.

    Returns:
        np.ndarray: Ảnh crop BGR.

    Raises:
        ValueError: Nếu tọa độ không hợp lệ hoặc vượt kích thước ảnh.
    """
    left = int(crop_roi["xStart"])
    top = int(crop_roi["yStart"])
    right = int(crop_roi["xEnd"])
    bottom = int(crop_roi["yEnd"])
    height, width = image.shape[:2]
    if left < 0 or top < 0 or right <= left or bottom <= top:
        raise ValueError("crop_roi không hợp lệ")
    if right > width or bottom > height:
        raise ValueError("crop_roi vượt kích thước ảnh")
    return image[top:bottom, left:right]


def test_trainler_patchcore_runtime_with_workspace_images():
    """Train anh that trong workspace va ghi record trong workspace.

    Returns:
        None: Ket thuc khong loi khi train va ghi record thanh cong.

    Raises:
        AssertionError: Neu thieu anh, artifact model hoac metadata train.
        FileNotFoundError: Neu folder img_train_patchcore khong ton tai.
    """
    data_root = PROJECT_ROOT / "img_train_patchcore"
    model_root = PROJECT_ROOT / "model_patch_core" 
    crop_roi = {
        "xStart": 100,
        "yStart": 100,
        "xEnd": 1330,
        "yEnd": 973,
    }

    if not data_root.exists():
        raise FileNotFoundError(f"Khong tim thay folder anh: {data_root}")

    config = PatchCoreTrainConfig(
        img_size=256,
        batch_size=4,
        coreset_ratio=0.2,
        n_list=2,
        n_probe=1,
        num_workers=0,
        crop_roi=crop_roi,
    )
    trainer = TrainlerPatchCore(config=config)
    trainer.record_manager = PatchCoreTrainRecordRepository()

    images = [
        Image.open(path).convert("RGB")
        for path in sorted(data_root.glob("*.jpg"))
    ]
    record = trainer.run_from_folder(
        images,
        model_root,
        roi_name="scratch",
    )
    assert Path(record["model_file"]).exists()
    assert Path(record["model_file"]).with_name("memory.npy").exists()
    session_root = Path(record["model_file"]).parent.parent
    assert session_root.name.startswith("model_scratch_crop_")
    assert record["run_id"] == session_root.name
    first_root = session_root / "the_first"
    runtime_root = session_root / "runtime"
    original_root = first_root / "original"
    cropped_root = first_root / "good"
    assert original_root.exists()
    assert cropped_root.exists()
    assert (runtime_root / "good").exists()
    assert len(list(original_root.glob("*.png"))) == 24
    assert len(list(cropped_root.glob("*.png"))) == 24
    assert not (session_root / "images").exists()
    assert not (session_root / "models").exists()

    manifest = trainer.record_manager.load_manifest()
    assert manifest
    record = manifest[0]
    assert record["status"] == "completed"
    assert record["roi_list"] == ["scratch"]
    assert record["crop_roi"] == crop_roi
    same_roi_records = [
        item for item in manifest
        if [str(roi).lower() for roi in item.get("roi_list", [])] == ["scratch"]
    ]
    assert len(same_roi_records) == 1

    assert record["train_config"]["img_size"] == 256
    assert "crop_roi" not in record["train_config"]

    original_image_path = sorted(original_root.glob("*.png"))[0]
    original_image = cv2.imread(str(original_image_path))
    assert original_image is not None
    cropped_image_bgr = _crop_image(original_image, record["crop_roi"])
    cropped_image_rgb = cv2.cvtColor(cropped_image_bgr, cv2.COLOR_BGR2RGB)

    inference_config = PatchCoreAnomalyConfig(
        index_path=record["model_file"],
        nprobe=record["train_config"]["n_probe"],
        img_size=record["train_config"]["img_size"],
        device=record["train_config"]["device"],
    )
    inference_model = ModelPatchCore(inference_config)
    inference_model.load_model()
    score, overlay = inference_model.predict(cropped_image_rgb)
    inference_output = first_root / "inference_result.jpg"
    assert cv2.imwrite(str(inference_output), overlay)
    assert inference_output.exists()
    assert np.isfinite(score)
    assert overlay.shape[:2] == cropped_image_rgb.shape[:2]
    inference_model.unload()


def main():
    """Chay runtime test doc lap khong can pytest.

    Returns:
        None: In thong bao PASS khi test hoan tat.

    Raises:
        AssertionError: Neu test runtime that bai.
    """
    test_trainler_patchcore_runtime_with_workspace_images()
    print("PASS: test_trainler_patchcore_runtime_with_workspace_images")


if __name__ == "__main__":
    main()
