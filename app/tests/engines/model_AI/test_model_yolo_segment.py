import cv2
from app.config import YoloSegmentConfig
from app.engines.model_AI import ModelYoloSegment


def main() -> None:
    """Chạy thử ModelYoloSegment.
    Args:
        None
    Returns:
        None
    """
    config = YoloSegmentConfig(
        path_model=r"C:\Disk D\Project\Python_Detect_Width_Line\code\app\app\storage\model\yolo\inner_permeable_membrane.pt",      # Đường dẫn model
        device="cpu",               # Hoặc "cuda:0"
        image_size=640,
        confidence=0.5,
        iou=0.5,
    )

    print("=" * 60)
    print("1. Khởi tạo Model")
    print("=" * 60)

    model = ModelYoloSegment(config)

    print("Hoàn thành.\n")

    print("=" * 60)
    print("2. Load Model")
    print("=" * 60)

    model.load_model()

    print("Load model thành công.\n")

    print("=" * 60)
    print("3. Đọc ảnh")
    print("=" * 60)

    image = cv2.imread(r"C:\Disk D\Project\Python_Detect_Width_Line\code\app\app\tests\model_AI\13.jpg")     # Đường dẫn ảnh

    if image is None:
        print("Không đọc được ảnh.")
        return

    print(f"Kích thước ảnh: {image.shape}\n")

    print("=" * 60)
    print("4. Predict")
    print("=" * 60)

    result = model.predict(image)

    print("Predict thành công.")
    print(f"Image size : {result.orig_shape}")

    if result.boxes is not None:
        print(f"Number of objects : {len(result.boxes)}")

    print()

    print("=" * 60)
    print("5. Get Segments")
    print("=" * 60)

    # segments = model.get_result(image)

    # print(f"Tổng số segment: {len(segments)}\n")

    # for index, segment in enumerate(segments, start=1):
    #     print("-" * 50)
    #     print(f"Segment {index}")
    #     print("-" * 50)
    #     print(f"Class ID     : {segment['class_id']}")
    #     print(f"Class Name   : {segment['class_name']}")
    #     print(f"Confidence   : {segment['confidence']:.4f}")
    #     print(f"Image Width  : {segment['image_width']}")
    #     print(f"Image Height : {segment['image_height']}")
    #     print(f"Polygon Size : {len(segment['polygon'])}")
    #     print(f"Mask Shape   : {segment['mask'].shape}")
    #     print()

    # print("=" * 60)
    # print("6. Unload Model")
    # print("=" * 60)

    image_draw = model.predict_draw(image)
    model.show(image_draw)
    model.unload()

    print("Unload thành công.\n")

    print("=" * 60)
    print("Hoàn thành kiểm tra ModelYoloSegment")
    print("=" * 60)


if __name__ == "__main__":
    main()

#python -m app.tests.engines.model_AI.test_model_yolo_segment