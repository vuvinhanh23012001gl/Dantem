from app.engines.model_AI import ModelYoloObject
from app.engines.AI_model_process import FrameModelYoloObject
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
    print("Model loaded, classes:", model.model.names)
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    obj_target = FrameModelYoloObject(model)
    status, messages, _, objects = obj_target.search(
        image, 30, 30, 300, 300, ClassNameObjectStructureDetectConfig.STAMP.value
    )
    print("status, messages, count:", status, messages, len(objects))


if __name__ == "__main__":
    main()
