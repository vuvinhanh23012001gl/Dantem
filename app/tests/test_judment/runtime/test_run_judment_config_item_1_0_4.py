import json
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import (
    PATH_FILE_MODEL_YOLO_STAMP,
    YoloDetectObjectConfig,
)
from app.engines.AI_model_process import FrameModelYoloObject
from app.engines.model_AI import ModelYoloObject
from app.engines.service import StructureFrameYoloService
from app.judger import (
    Judment,
    StampDetector,
)

CONFIG_PATH = PROJECT_ROOT / "app" / "storage" / "config_judgment_law.json"
IMAGE_PATH = PROJECT_ROOT / "app" / "storage" / "img_points" / "1" / "0" / "4.jpg"
OUTPUT_DIR = PROJECT_ROOT / "app" / "output" / "judgment_item_1_0_4"


def load_item_config() -> dict:
    """Đọc cấu hình judgment của product 1, frame 0, item 4 (fallback sang StampItemInspector nếu item cũ rỗng sau khi gỡ tool)."""
    with CONFIG_PATH.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)
    item_cfg = data.get("1", {}).get("0", {}).get("4") or {}
    if not item_cfg:
        item_cfg = {
            "StampItemInspector": {
                "0": {"id": 0, "name": "Tem 1", "xStart": 60, "yStart": 60, "xEnd": 220, "yEnd": 180},
                "1": {"id": 1, "name": "Tem 2", "xStart": 260, "yStart": 60, "xEnd": 420, "yEnd": 180},
            }
        }
    return item_cfg


def create_registry() -> dict:
    """Khởi tạo registry detector đang hoạt động."""
    stamp_frame = FrameModelYoloObject(
        ModelYoloObject(
            YoloDetectObjectConfig(path_model=PATH_FILE_MODEL_YOLO_STAMP)
        )
    )
    stamp_service = StructureFrameYoloService(stamp_frame)
    return {
        "StampItemInspector": StampDetector(stamp_service),
    }


def main() -> dict:
    """Chạy toàn bộ inspector cấu hình item 1/0/4 trên ảnh runtime thật."""
    image = cv2.imread(str(IMAGE_PATH))
    if image is None:
        raise AssertionError(f"Không đọc được ảnh test: {IMAGE_PATH}")
    config = load_item_config()
    registry = create_registry()
    supported_config = {
        name: inspector_config
        for name, inspector_config in config.items()
        if name in registry
    }
    summary = Judment(registry).run_summary(image, supported_config)
    assert set(summary["inspectors"]) == set(supported_config)
    assert summary["status"] in {"OK", "NG"}
    print("\nJudment config item 1/0/4 runtime test: PASS")
    return summary


if __name__ == "__main__":
    main()
