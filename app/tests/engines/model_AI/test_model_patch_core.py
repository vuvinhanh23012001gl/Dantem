
from app.config import PatchCoreAnomalyConfig
from app.engines.model_AI import ModelPatchCore
import cv2

if __name__ == "__main__":
    # 1. Khởi tạo cấu hình hệ thống
    config = PatchCoreAnomalyConfig(
        index_path= r"C:\Disk D\Project\Python_Detect_Width_Line\code\app\model_patch_core\patchcore_ivf.index",
        nprobe=10,
        img_size=256
    )
    # 2. Khởi tạo đối tượng Model
    model = ModelPatchCore(config=config)
    # 3. Load model và chạy warmup (Thực hiện khi khởi động API / Ứng dụng)
    model.load_model()
    model.warmup()
    # 4. Đọc ảnh đầu vào thực tế (Ví dụ từ camera hoặc file)
    raw_img = cv2.imread(r"C:\Users\anhuv\Desktop\train\patch_core_bot_khi\test\2.jpg")
    if raw_img is not None:
        # Chuẩn hóa hệ màu về RGB trước khi truyền vào pipeline của Model PatchCore
        rgb_img = cv2.cvtColor(raw_img, cv2.COLOR_BGR2RGB)
        # 5. Chạy Inference
        # anomaly_score, visual_result = model.predict(rgb_img)
        # print(f"--> [HỆ THỐNG] Anomaly Score thu được: {anomaly_score}")
        img,bounding_boxes = model.get_bounding_boxes(rgb_img)
        # 6. Hiển thị kết quả kiểm tra ngoại quan
        cv2.imshow("Kiem tra Ink Frame - PatchCore", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    # 7. Giải phóng bộ nhớ khi tắt module/hệ thống
    model.unload()


# python -m app.tests.engines.model_AI.test_model_patch_core