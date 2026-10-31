import json
import sys
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from app.judger import BaseJudgerAI, JudgmentResult, Judment

CONFIG_PATH = PROJECT_ROOT / "app" / "storage" / "config_judgment_law.json"
IMAGE_PATH = PROJECT_ROOT / "app" / "storage" / "img_points" / "1" / "0" / "4.jpg"


def create_recording_inspector(name: str):
    """Tạo detector giả có tên đúng với key trong cấu hình."""
    def define(self, image, *args, **kwargs):
        self.image = image
        self.define_args = args
        self.define_kwargs = kwargs
        return {"called": True, "args": args}

    def compare(self, standard_data, runtime_data, **kwargs):
        self.standard_data = standard_data
        self.compare_kwargs = kwargs
        return {"standard": standard_data, "runtime": runtime_data}

    def judge(self, comparison_data):
        return JudgmentResult(
            ok=True,
            status="OK",
            standard_data=comparison_data["standard"],
            runtime_data=comparison_data["runtime"],
            comparison_data=comparison_data,
            message="Detector giả chạy thành công",
        )

    return type(
        f"{name}RecordingInspector",
        (BaseJudgerAI,),
        {
            "INSPECTOR_NAME": name,
            "define": define,
            "compare": compare,
            "judge": judge,
        },
    )


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


def test_stamp_roi_overlay() -> None:
    """Kiểm tra overlay StampItemInspector vẽ đúng đa khung xanh [OK] / đỏ [NG]."""
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    boxes = [
        {"id": 0, "name": "Tem 1", "x1": 20, "y1": 30, "x2": 120, "y2": 100},
        {"id": 1, "name": "Tem 2", "x1": 160, "y1": 30, "x2": 260, "y2": 100},
    ]
    runtime_data = {
        "boxes": [
            {"id": 0, "name": "Tem 1", "bbox_roi": [20, 30, 120, 100], "ok": True},
            {"id": 1, "name": "Tem 2", "bbox_roi": [160, 30, 260, 100], "ok": False},
        ],
        "objects": [],
    }
    result = JudgmentResult(ok=False, status="NG", runtime_data=runtime_data)
    overlay_image, overlay_data = Judment._render_inspector_overlay(
        image,
        "StampItemInspector",
        {"StampItemInspector": {}},
        (boxes,),
        runtime_data,
        {},
        result,
    )

    assert overlay_data["standard"]["boxes"] == [[20, 30, 120, 100], [160, 30, 260, 100]]
    assert overlay_data["standard"]["labels"] == ["Tem 1", "Tem 2"]
    assert tuple(overlay_image[60, 20]) == (0, 255, 0)
    assert tuple(overlay_image[60, 160]) == (0, 0, 255)


def test_later_roi_does_not_fade_previous_roi() -> None:
    """Kiểm tra overlay inspector sau không làm nhạt box đã vẽ trước."""
    source = np.zeros((32, 32, 3), dtype=np.uint8)
    first_overlay = source.copy()
    first_overlay[8, 8] = (255, 0, 0)
    judgment = Judment._blend_overlay_image(
        source.copy(), first_overlay, 0.85, source
    )
    first_roi_pixel = judgment[8, 8].copy()

    later_overlay = source.copy()
    later_overlay[20, 20] = (0, 0, 255)
    judgment = Judment._blend_overlay_image(
        judgment, later_overlay, 0.85, source
    )

    assert np.array_equal(judgment[8, 8], first_roi_pixel)
    assert tuple(judgment[20, 20]) == (0, 0, 217)


def main() -> None:
    """Kiểm tra Judment điều phối đúng config item 1/0/4 trên một ảnh."""
    image = cv2.imread(str(IMAGE_PATH))
    if image is None:
        raise AssertionError(f"Không đọc được ảnh test: {IMAGE_PATH}")

    config = load_item_config()
    registry = {
        name: create_recording_inspector(name)()
        for name in config
    }
    summary = Judment(registry).run_summary(image, config)

    assert summary["overall"] is True
    assert summary["status"] == "OK"
    assert set(summary["inspectors"]) == set(config)
    assert len(summary["errors"]) == 0
    assert summary["image"] == {
        "height": image.shape[0],
        "width": image.shape[1],
        "channels": image.shape[2],
    }
    test_stamp_roi_overlay()
    test_later_roi_does_not_fade_previous_roi()
    print("Judment config item 1/0/4 logic test: PASS")
    print(f"Inspectors: {list(config)}")


if __name__ == "__main__":
    main()
