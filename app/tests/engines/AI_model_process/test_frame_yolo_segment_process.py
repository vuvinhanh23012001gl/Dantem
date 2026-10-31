from app.config import YoloSegmentConfig
from app.engines.model_AI import ModelYoloSegment
from app.engines.AI_model_process import FrameModelYoloSegment
import cv2
   
def main() -> None:
    """Kiểm tra SemipermeableMembraneYoloSegmentService.
    Args:
        None
    Returns:
        None
    """

    config = YoloSegmentConfig(
        path_model=r"C:\Disk D\Project\Python_Detect_Width_Line\code\app\app\storage\model\yolo\inner_permeable_membrane.pt",
        device="cpu",
        image_size=640,
        confidence=0.5,
        iou=0.5,
    )

    print("=" * 60)
    print("Khởi tạo Model")
    print("=" * 60)

    model = ModelYoloSegment(config)  # tien hanh load model luon
    print("Model loaded.\n")
    print("=" * 60)
    print("Khởi tạo Service")
    print("=" * 60)
    service = FrameModelYoloSegment(model)
    print("Service created.\n")
    image = cv2.imread(
        r"C:\Users\anhuv\Desktop\train\yolo_object_hinh_vuong_iner_hinh_vuong\img_train\0_copy (29).jpg"
    )

    if image is None:
        print("Không đọc được ảnh.")
        return

    print("=" * 60)
    print("Detect")
    print("=" * 60)
    segments = service.get_segments(image, 500 ,600, 1600, 1600)
    service.show(image,segments)

    print("Done.")


if __name__ == "__main__":
    main()

#  python -m app.tests.test_AI_model_service.test_semipermeable_membrane_border_yolo_segment_service  