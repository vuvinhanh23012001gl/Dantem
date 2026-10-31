import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app.engines.AI_model_process import FrameModelPatchCore
from app.engines.model_AI import ModelPatchCore


def test_get_bounding_boxes_crops_roi_and_restores_coordinates() -> None:
    """Kiểm tra box PatchCore được dịch từ ROI về ảnh gốc."""
    model = ModelPatchCore.__new__(ModelPatchCore)
    captured_images = []

    def get_boxes(image: np.ndarray) -> list[tuple[int, int, int, int]]:
        captured_images.append(image)
        return [(2, 3, 10, 20)]

    model.get_bounding_boxes = get_boxes
    frame = FrameModelPatchCore(model)
    image = np.zeros((100, 120, 3), dtype=np.uint8)

    boxes = frame.get_bounding_boxes(image, 20, 30, 80, 90)

    assert captured_images[0].shape == (60, 60, 3)
    assert boxes == [(22, 33, 10, 20)]


def test_predict_crops_roi_before_model_call() -> None:
    """Kiểm tra predict trả score/overlay của đúng ROI."""
    model = ModelPatchCore.__new__(ModelPatchCore)
    captured_images = []
    expected_overlay = np.ones((40, 50, 3), dtype=np.uint8)

    def predict(image: np.ndarray) -> tuple[float, np.ndarray]:
        captured_images.append(image)
        return 0.8, expected_overlay

    model.predict = predict
    frame = FrameModelPatchCore(model)
    image = np.zeros((100, 120, 3), dtype=np.uint8)

    score, overlay = frame.predict(image, 10, 15, 60, 55)

    assert captured_images[0].shape == (40, 50, 3)
    assert score == 0.8
    assert overlay is expected_overlay


def test_rejects_invalid_roi() -> None:
    """Kiểm tra ROI vượt ảnh bị từ chối trước khi gọi model."""
    model = ModelPatchCore.__new__(ModelPatchCore)
    frame = FrameModelPatchCore(model)

    try:
        frame.get_bounding_boxes(np.zeros((10, 10, 3), dtype=np.uint8), 0, 0, 11, 10)
    except ValueError as error:
        assert "vượt quá" in str(error)
    else:
        raise AssertionError("ROI vượt ảnh phải phát sinh ValueError")


def main() -> None:
    """Chạy test FrameModelPatchCore độc lập bằng Python."""
    tests = [
        test_get_bounding_boxes_crops_roi_and_restores_coordinates,
        test_predict_crops_roi_before_model_call,
        test_rejects_invalid_roi,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print(f"Đã chạy {len(tests)} test FrameModelPatchCore: PASS")


if __name__ == "__main__":
    main()