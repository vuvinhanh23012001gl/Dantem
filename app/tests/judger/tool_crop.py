import os
import glob
import cv2
import time
import numpy as np
from shapely.geometry import box as ShapelyBox
from shapely.geometry import Polygon as ShapelyPolygon
from app.engines.model_AI import ModelUnet, ModelPatchCore
from app.config import PatchCoreAnomalyConfig, UnetConfig

# ==================== CẤU HÌNH THƯ MỤC ĐẦU VÀO / ĐẦU RA ====================
INPUT_IMG_DIR = r"C:\Users\anhuv\Desktop\train\patch_core_bot_khi\botkhi\img"
OUTPUT_CROP_DIR = r"C:\Users\anhuv\Desktop\train\patch_core_bot_khi\botkhi\img_Crop"

# Hậu tố tên model để phân biệt nguồn gốc ảnh crop
MODEL_SUFFIX = "PatchCoreV1" 

# Cấu hình kích thước cạnh dài nhất sau khi Scale (Đơn vị: Pixel)
# Ảnh sẽ tự động giữ nguyên tỷ lệ (Aspect Ratio) mà không lo bị méo, biến dạng.
# Nếu muốn giữ nguyên kích thước gốc của vùng cắt, hãy đặt MAX_SIZE = None
MAX_SIZE = 2048  
# =========================================================================
def get_touching_boundary_boxes(polygon_weld: np.ndarray, bounding_box_abnormal: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    """
    Lọc ra các Bounding Box chạm hoặc cắt qua đường viền (boundary) của Polygon.
    """
    if polygon_weld is None or len(polygon_weld) < 3:
        return [] 
        
    # Chuẩn hóa dữ liệu Polygon đầu vào về dạng các điểm (x, y) để truyền vào Shapely
    poly_points = polygon_weld.reshape(-1, 2)
    poly_geom = ShapelyPolygon(poly_points)
    
    # Lấy riêng đường viền (Boundary) của Polygon để kiểm tra va chạm
    poly_boundary = poly_geom.boundary
    touching_boxes = []
    
    # Duyệt qua từng Bounding Box để kiểm tra mối quan hệ không gian
    for bbox in bounding_box_abnormal:
        x, y, w, h = bbox
        # Tạo đối tượng hình chữ nhật từ tọa độ (xmin, ymin, xmax, ymax)
        box_geom = ShapelyBox(x, y, x + w, y + h)
        
        # Kiểm tra nếu Box giao cắt hoặc chạm trực tiếp với đường biên
        if box_geom.intersects(poly_boundary):
            touching_boxes.append(bbox)
            
    return touching_boxes

def crop_img(img: np.ndarray, touching_boxes: list[tuple[int, int, int, int]]) -> list[np.ndarray]:
    """
    Cắt các phân vùng ảnh nhỏ (sub-images) từ ảnh gốc dựa trên danh sách Bounding Box.
    """
    cropped_images = []
    if img is None or not touching_boxes:
        return cropped_images
        
    # Lấy kích thước ảnh gốc để giới hạn vùng cắt (boundary check)
    img_h, img_w = img.shape[:2]
    for bbox in touching_boxes:
        x, y, w, h = bbox
        
        # Tính toán tọa độ pixel hợp lệ (ymin:ymax, xmin:xmax) cho ma trận numpy slice
        ymin = max(0, int(y))
        ymax = min(img_h, int(y + h))
        xmin = max(0, int(x))
        xmax = min(img_w, int(x + w))
        
        # Kiểm tra tính hợp lệ của phân vùng trước khi cắt
        if ymax > ymin and xmax > xmin:
            crop = img[ymin:ymax, xmin:xmax]
            cropped_images.append(crop)
            
    return cropped_images

def main():
    # 1. Đảm bảo thư mục đầu ra tồn tại
    os.makedirs(OUTPUT_CROP_DIR, exist_ok=True)

    # 2. Khởi tạo và cấu hình Model UNET & PatchCore
    obj_unet_config = UnetConfig()
    obj_unet = ModelUnet(obj_unet_config)

    patchcore_config = PatchCoreAnomalyConfig(
        index_path=r"C:\Disk D\Project\Python_Detect_Width_Line\code\app\model_patch_core\patchcore_ivf.index",
        nprobe=10,
        img_size=256
    )
    model_patchcore = ModelPatchCore(config=patchcore_config)
    model_patchcore.load_model()
    model_patchcore.warmup()

    # 3. Lấy danh sách tất cả các file ảnh trong thư mục input
    extensions = ('*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG')
    img_paths = []
    for ext in extensions:
        img_paths.extend(glob.glob(os.path.join(INPUT_IMG_DIR, ext)))

    print(f"Tìm thấy {len(img_paths)} ảnh cần xử lý trong thư mục: {INPUT_IMG_DIR}")

    # 4. Duyệt qua từng bức ảnh để xử lý theo Pipeline
    for img_path in img_paths:
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        print(f"\nĐang xử lý ảnh: {os.path.basename(img_path)} ...")

        raw_img = cv2.imread(img_path)
        if raw_img is None:
            print(f"[CẢNH BÁO] Không thể đọc ảnh: {img_path}")
            continue

        try:
            # Bước 1: Trích xuất thông tin đa giác đường hàn (Unet)
            polygons = obj_unet.get_polygon(raw_img, UnetConfig.epsilon_ratio, UnetConfig.min_area)
            
            # Bước 2: Chuẩn hóa hệ màu về RGB phục vụ mô hình PatchCore và lấy bounding boxes
            rgb_img = cv2.cvtColor(raw_img, cv2.COLOR_BGR2RGB)
            _, bounding_boxes = model_patchcore.get_bounding_boxes(rgb_img)
            
            # Bước 3: Lọc các bounding box chạm đường biên đường hàn
            touching_boxes = get_touching_boundary_boxes(polygons, bounding_boxes)
            
            if touching_boxes:
                # Bước 4: Tự động cắt ảnh từ ảnh gốc dựa trên các box đã lọc (Thay thế hoàn toàn Judger)
                cropped_images = crop_img(raw_img, touching_boxes)
                print(f"-> Phát hiện {len(cropped_images)} vùng bất thường nằm trên biên đường hàn.")
                
                # Tạo chuỗi thời gian độc nhất chống trùng lặp file (YYYYMMDD_HHMMSS)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                
                for idx, crop_img_data in enumerate(cropped_images):
                    # Tiến hành SCALE GIỮ NGUYÊN TỶ LỆ nếu có cấu hình MAX_SIZE
                    if MAX_SIZE is not None:
                        h, w = crop_img_data.shape[:2]
                        
                        # Tính toán scale_ratio dựa trên cạnh dài nhất
                        if w > h:
                            scale_ratio = MAX_SIZE / float(w)
                            new_w = MAX_SIZE
                            new_h = int(h * scale_ratio)
                        else:
                            scale_ratio = MAX_SIZE / float(h)
                            new_h = MAX_SIZE
                            new_w = int(w * scale_ratio)
                        
                        # Tránh lỗi nếu kích thước mới tính toán ra bằng 0
                        if new_w > 0 and new_h > 0:
                            final_img = cv2.resize(
                                crop_img_data, 
                                (new_w, new_h), 
                                interpolation=cv2.INTER_AREA if scale_ratio < 1 else cv2.INTER_CUBIC
                            )
                        else:
                            final_img = crop_img_data
                    else:
                        final_img = crop_img_data

                    # Cấu hình tên file chuẩn hóa không trùng lặp
                    output_filename = f"{base_name}_{MODEL_SUFFIX}_{timestamp}_{idx}.jpg"
                    output_path = os.path.join(OUTPUT_CROP_DIR, output_filename)
                    
                    # Lưu ảnh đã được scale đúng tỷ lệ
                    cv2.imwrite(output_path, final_img)
            else:
                print("-> Không phát hiện bất thường chạm đường biên đường hàn.")

        except Exception as e:
            print(f"[LỖI] Đã xảy ra lỗi khi xử lý ảnh {base_name}: {str(e)}")

    print(f"\nHoàn thành! Toàn bộ ảnh kết quả được lưu tại: {OUTPUT_CROP_DIR}")

if __name__ == "__main__":
    main()