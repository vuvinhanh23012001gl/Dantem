from app.engines.model_AI import ModelYoloObject
from app.engines.AI_model_process import FrameModelYoloObject
from app.engines.service import StructureFrameYoloService
from app.config import (
    YoloDetectObjectConfig,
    ClassNameObjectStructureDetectConfig,
    PATH_FILE_MODEL_YOLO_STAMP,
)
import numpy as np


def main():
    config = YoloDetectObjectConfig(
        path_model=str(PATH_FILE_MODEL_YOLO_STAMP),
        device="cpu",
        image_size=640,
        confidence=0.25,
        iou=0.45,
    )
    model = ModelYoloObject(config)
    frame_model = FrameModelYoloObject(model)
    service = StructureFrameYoloService(frame_model)

    image = np.zeros((768, 1024, 3), dtype=np.uint8)
    result = service.inspect_stamp_boxes(
        image=image,
        boxes=[
            {"id": 0, "name": "Tem 1", "xStart": 100, "yStart": 100, "xEnd": 300, "yEnd": 250},
            {"id": 1, "name": "Tem 2", "xStart": 400, "yStart": 100, "xEnd": 600, "yEnd": 250},
        ],
        label=ClassNameObjectStructureDetectConfig.STAMP.value,
        width_canvas=1024,
    )
    assert result.ok
    assert "is_mock" not in result.data
    print("inspect_stamp_boxes REAL YOLO OK")
    print("boxes=", len(result.data["boxes"]), "objects=", len(result.data["objects"]))


if __name__ == "__main__":
    main()
