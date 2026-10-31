"""Chạy thử inference PatchCore từ record train mới nhất."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np

from app.config import PatchCoreAnomalyConfig
from app.engines.model_AI import ModelPatchCore
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordRepository,
)


def _crop_image(image: np.ndarray, crop_roi: dict) -> np.ndarray:
    """Crop ảnh theo tọa độ đã lưu trong training record.

    Args:
        image: Ảnh RGB dạng NumPy.
        crop_roi: Dict có xStart, yStart, xEnd, yEnd.

    Returns:
        np.ndarray: Ảnh crop RGB dùng cho inference.

    Raises:
        ValueError: Nếu crop_roi thiếu tọa độ hoặc vùng crop không hợp lệ.
    """
    left = int(crop_roi["xStart"])
    top = int(crop_roi["yStart"])
    right = int(crop_roi["xEnd"])
    bottom = int(crop_roi["yEnd"])
    if left < 0 or top < 0 or right <= left or bottom <= top:
        raise ValueError("crop_roi không hợp lệ")
    height, width = image.shape[:2]
    if right > width or bottom > height:
        raise ValueError("crop_roi vượt kích thước ảnh inference")
    return image[top:bottom, left:right]


def test_run_patchcore_inference_from_latest_record():
    """Load model PatchCore mới nhất, infer một ảnh train và lưu overlay.

    Returns:
        None: Kết thúc không lỗi khi model và inference hoạt động.

    Raises:
        AssertionError: Nếu thiếu record, model, ảnh hoặc output inference.
        ValueError: Nếu crop_roi trong record không hợp lệ.
    """
    record_service = PatchCoreTrainRecordRepository()
    record = record_service.get_latest_run()
    assert record is not None

    model_file = Path(record["model_file"])
    session_root = Path(record["model_root"])
    original_images = sorted((session_root / "original").glob("*.jpg"))
    assert model_file.exists()
    assert original_images

    image_bgr = cv2.imread(str(original_images[0]))
    assert image_bgr is not None
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    cropped_rgb = _crop_image(image_rgb, record["crop_roi"])

    config = PatchCoreAnomalyConfig(
        index_path=str(model_file),
        nprobe=int(record["train_config"]["n_probe"]),
        img_size=int(record["train_config"]["img_size"]),
        device=str(record["train_config"]["device"]),
    )
    model = ModelPatchCore(config)
    model.load_model()
    score, overlay_bgr = model.predict(cropped_rgb)

    output_path = session_root / "inference_result.jpg"
    assert cv2.imwrite(str(output_path), overlay_bgr)
    assert output_path.exists()
    assert np.isfinite(score)
    assert overlay_bgr.shape[:2] == cropped_rgb.shape[:2]
    model.unload()


def main():
    """Chạy inference test độc lập không cần pytest.

    Returns:
        None: In score và thông báo PASS khi hoàn tất.

    Raises:
        AssertionError: Nếu inference thất bại.
    """
    test_run_patchcore_inference_from_latest_record()
    print("PASS: test_run_patchcore_inference_from_latest_record")


if __name__ == "__main__":
    main()