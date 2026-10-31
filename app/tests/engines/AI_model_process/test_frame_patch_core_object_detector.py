import sys
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import PatchCoreAnomalyConfig, YoloDetectObjectConfig
from app.engines.AI_model_process import FrameModelPatchCore, FramePatchCoreObjectDetector
from app.engines.model_AI import ModelPatchCore, ModelYoloObject

PATCHCORE_INDEX_PATH = (
    PROJECT_ROOT
    / "app"
    / "input"
    / "model"
    / "patch_core"
    / "1"
    / "1"
    / "4"
    / "model_end_chipping_crop_20260909_044556_163917"
    / "the_first"
    / "patchcore.index"
)
YOLO_MODEL_PATH = (
    PROJECT_ROOT
    / "model_air_bubble"
    / "train16"
    / "weights"
    / "best.pt"
)
IMAGE_PATH = PROJECT_ROOT / "app" / "storage" / "img_points" / "1" / "0" / "4.jpg"

ROI = {
    "x1": 1078,
    "y1": 62,
    "x2": 1654,
    "y2": 622,
    "class_id": 0,
}


def build_patchcore_model() -> ModelPatchCore:
    """Tạo model PatchCore theo mã tỉnh đầu vào thật."""
    config = PatchCoreAnomalyConfig(
        index_path=str(PATCHCORE_INDEX_PATH),
        nprobe=10,
        img_size=256,
        device="cpu",
    )
    model = ModelPatchCore(config)
    model.load_model()
    model.warmup()
    return model


def build_yolo_model() -> ModelYoloObject:
    """Tạo model YOLO object dùng class 0."""
    config = YoloDetectObjectConfig(
        path_model=str(YOLO_MODEL_PATH),
        device="cpu",
        image_size=640,
        confidence=0.25,
        iou=0.45,
    )
    model = ModelYoloObject(config)
    model.load_model()
    model.warmup()
    return model


def draw_heatmap(image: np.ndarray, patchcore_box: tuple[int, int, int, int] | None = None) -> np.ndarray:
    """Tạo heatmap PatchCore từ ảnh ROI và vẽ box bất thường lên trên cùng một ảnh."""
    base = image.copy()

    if patchcore_box is None:
        return base

    x, y, w, h = patchcore_box
    roi = base[y : y + h, x : x + w]
    if roi.size == 0:
        return base

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    heat = cv2.applyColorMap(cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(roi, 0.5, heat, 0.5, 0)
    base[y : y + h, x : x + w] = overlay

    cv2.rectangle(base, (x, y), (x + w, y + h), (255, 0, 0), 3)
    cv2.putText(
        base,
        "PatchCore heatmap",
        (x, max(20, y - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 0, 0),
        2,
    )
    return base


def draw_results(
    image: np.ndarray,
    detections: list[dict],
    roi: dict | None = None,
    patchcore_boxes: list[tuple[int, int, int, int]] | None = None,
) -> np.ndarray:
    """Vẽ vùng phán định, tất cả vùng bất thường PatchCore và box YOLO trên cùng ảnh."""
    output = image.copy()

    if roi is not None:
        cv2.rectangle(
            output,
            (int(roi["x1"]), int(roi["y1"])),
            (int(roi["x2"]), int(roi["y2"])),
            (0, 0, 255),
            3,
        )
        cv2.putText(
            output,
            "Judgment ROI",
            (int(roi["x1"]), max(20, int(roi["y1"]) - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

    if patchcore_boxes:
        for index, patchcore_box in enumerate(patchcore_boxes, start=1):
            x, y, w, h = patchcore_box
            cv2.rectangle(output, (x, y), (x + w, y + h), (255, 0, 0), 3)
            cv2.putText(
                output,
                f"PatchCore anomaly {index}",
                (x, max(20, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2,
            )

    for detection in detections:
        bbox = detection.get("bbox", {})
        x1 = int(float(bbox.get("x1", 0)))
        y1 = int(float(bbox.get("y1", 0)))
        x2 = int(float(bbox.get("x2", 0)))
        y2 = int(float(bbox.get("y2", 0)))
        class_name = str(detection.get("class_name", "unknown"))
        score = float(detection.get("confidence", 0.0))

        cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            output,
            f"{class_name}:{score:.2f}",
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )
    return output


def test_real_patchcore_and_yolo_object_inference() -> None:
    """Chạy end-to-end với model PatchCore thật và YOLO object thật trên ROI EndChipping."""
    image = cv2.imread(str(IMAGE_PATH), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Không tìm thấy ảnh đầu vào: {IMAGE_PATH}")
    if not PATCHCORE_INDEX_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy index PatchCore: {PATCHCORE_INDEX_PATH}")
    if not YOLO_MODEL_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy model YOLO: {YOLO_MODEL_PATH}")

    patchcore_model = build_patchcore_model()
    patchcore_frame = FrameModelPatchCore(patchcore_model)
    yolo_model = build_yolo_model()
    detector = FramePatchCoreObjectDetector(patchcore_frame, yolo_model)

    detections = detector.detect_anomaly_objects(
        image,
        ROI["x1"],
        ROI["y1"],
        ROI["x2"],
        ROI["y2"],
    )

    class_zero_detections = [
        item for item in detections if item.get("class_id") == ROI["class_id"]
    ]

    if not class_zero_detections:
        raise AssertionError(
            "Không có đối tượng nào được phát hiện với class_id=0 trong ROI EndChipping."
        )

    patchcore_boxes = [
        item["patchcore_box"]
        for item in class_zero_detections
        if "patchcore_box" in item
    ]
    unique_patchcore_boxes = list(dict.fromkeys(patchcore_boxes))

    output_vis = draw_results(image, class_zero_detections, ROI, unique_patchcore_boxes)
    heatmap_vis = draw_heatmap(image, unique_patchcore_boxes[0] if unique_patchcore_boxes else None)

    output_dir = PROJECT_ROOT / "app" / "output" / "test_patchcore_object_detector"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "result_end_chipping_detector.png"
    heatmap_path = output_dir / "heatmap_end_chipping_detector.png"
    cv2.imwrite(str(output_path), output_vis)
    cv2.imwrite(str(heatmap_path), heatmap_vis)

    print(f"ROI: {ROI}")
    print(f"Số detection class 0: {len(class_zero_detections)}")
    for idx, item in enumerate(class_zero_detections, start=1):
        print(f"Detection {idx}: {item['class_name']} score={item['confidence']:.3f} bbox={item['bbox']}")
    print(f"Đã lưu ảnh kết quả: {output_path}")

    assert len(class_zero_detections) >= 1


if __name__ == "__main__":
    test_real_patchcore_and_yolo_object_inference()
