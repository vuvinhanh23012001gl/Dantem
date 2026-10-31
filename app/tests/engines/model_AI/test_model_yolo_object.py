import cv2
from app.config import YoloDetectObjectConfig
from app.engines.model_AI import ModelYoloObject

def main():
    config = YoloDetectObjectConfig(
        path_model=r"C:\Disk D\Project\Python_Detect_Width_Line\code\app\app\storage\model\yolo\object_target_detect.pt",      # Đường dẫn model
        device="cpu",                   # Hoặc "cpu"
        image_size=640,
        confidence=0.25,
        iou=0.45,
    )
    model = ModelYoloObject(config)
    print("Loading model...")
    model.load_model()
    print("Warmup...")
    model.warmup()
    image = cv2.imread(r"C:\Disk D\Project\Python_Detect_Width_Line\code\app\app\tests\model_AI\img_test_object_detect_1.jpg")
    if image is None:
        raise FileNotFoundError("Cannot read image: C:\Disk D\Project\Python_Detect_Width_Line\code\app\app\tests\model_AI\img_test_object_detect_1.jpg")
    # print("Predicting...")
    # results = model.predict(image)
    # result = results[0]
    # print(f"Detected {len(result.boxes)} objects")
    # for i, box in enumerate(result.boxes):
    #     cls = int(box.cls.item())
    #     conf = float(box.conf.item())
    #     x1, y1, x2, y2 = box.xyxy[0].tolist()
    #     print(
    #         f"{i + 1}: "
    #         f"class={cls}, "
    #         f"conf={conf:.3f}, "
    #         f"box=({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})"
    #     )
    result = model.get_result(image)
    print("result",result)
    # image_result = result.plot()
    # cv2.imshow("Result", image_result)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    print("Unload model...")
    model.unload()


if __name__ == "__main__":
    main()

# python -m app.tests.engines.model_AI.test_model_yolo_object