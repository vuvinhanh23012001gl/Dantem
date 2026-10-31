import threading
from app.model import BaseAI
from app.config import UnetConfig
from app.utils import Folder
import segmentation_models_pytorch as smp
# pyrefly: ignore [missing-import]
import torch
import gc
import  numpy as np 
import os
import cv2

class ModelUnet(BaseAI):
    """Lớp thực hiện khởi tạo, dự đoán và xử lý hậu kỳ cho mô hình Unet++.
    Kế thừa từ BaseAI, hỗ trợ tự động tải trọng số, tối ưu hóa bộ nhớ,
    tiền xử lý ảnh đầu vào và trích xuất đa giác (polygon) từ kết quả phân đoạn.
    """
    def __init__(self,config:UnetConfig = None):
        """Khởi tạo cấu hình, kiểm tra file trọng số và tải mô hình lên thiết bị phần cứng.
        Args:
            config (UnetConfig, optional): Đối tượng chứa toàn bộ tham số cấu hình của mô hình.
                Mặc định là None.
        Raises:
            ValueError: Nếu đường dẫn file trọng số (`config.path`) không tồn tại.
        """
        self.config = config
        self.device =  None
        self.model = None
        self._predict_lock = threading.Lock()
        print("config.path",config.path)
        if not os.path.exists(config.path):
            Folder.create_file_path(config.path)
            raise ValueError("No_Model_Unet")
        self.load_model()
        self.warmup()
        

    def load_model(self):
        """Khởi tạo kiến trúc mạng Unet++, nạp trọng số pre-trained từ file cấu hình
        và chuyển mô hình sang chế độ đánh giá (evaluation mode).
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Nạp offline 100%: Khi file checkpoint đã có sẵn, không tải encoder weights từ internet
        encoder_weights = None if os.path.exists(self.config.path) else self.config.encoder_weights
        self.model = smp.UnetPlusPlus(
            encoder_name = self.config.encoder,
            encoder_weights = encoder_weights,
            in_channels = self.config.in_channels,
            classes = self.config.classes,
            activation= self.config.activation
        ).to(self.device)
        self.model.load_state_dict(torch.load(self.config.path, map_location = self.device))
        self.model.eval()
    
    
    def preprocess(self,image):
        """Tiền xử lý ảnh thô trước khi đưa vào mô hình Deep Learning.
        Các bước bao gồm: Chuyển hệ màu BGR sang RGB, thay đổi kích thước, chuẩn hóa 
        về khoảng [0, 1], chuẩn hóa chuẩn Z-score (theo ImageNet mean/std), tráo đổi 
        trục sang dạng (C, H, W) và thêm chiều batch.
        Args:
            image (np.ndarray): Ảnh đầu vào từ OpenCV có dạng (H, W, C) và hệ màu BGR.
        Returns:
            torch.Tensor: Tensor đã xử lý, sẵn sàng đưa vào mô hình, dạng (1, C, H, W).
        """
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (self.config.img_size, self.config.img_size))
        # cv2.imshow("Mask", image)  
        # cv2.waitKey(0)
        image = image.astype(np.float32) / 255.0  # chuyen tu anh 0-255 chuyen sang float de vao mo hinh
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        image = (image - mean) / std
        image = np.transpose(image, (2, 0, 1))  #  (H, W, C) sang (C, H, W)
        image = np.expand_dims(image, axis=0)
        return torch.from_numpy(image).to(self.device)
    

    def get_mask(self,img):
        """Dự đoán mask và làm sạch các đốm nhiễu nhỏ xung quanh bằng toán tử Opening.
        Args:
            img (np.ndarray): Ảnh gốc đầu vào cần lấy mask.
        Returns:
            np.ndarray: Mask nhị phân sạch sau khi đã lọc nhiễu hạt.
        """
        mask_raw = self.predict(img)   # Lấy mask
        mask_clean = self.clean_mask_opening(mask_raw,self.config.kernel) # Loc nhieu xung quanh, lam sach mask
        return mask_clean
 
    def get_polygon(self,img, Approx_value, min_area:None|int):
        """Trích xuất tọa độ đa giác xấp xỉ của vùng đối tượng lớn nhất từ ảnh đầu vào.
        Args:
            img (np.ndarray): Ảnh gốc đầu vào.
            Approx_value (float): Hệ số xấp xỉ khoảng cách (epsilon factor) cho hàm `cv2.approxPolyDP`.
            min_area (int, optional): Diện tích tối thiểu của contour để được xử lý.
        Returns:
            np.ndarray | None: Mảng chứa các tọa độ đỉnh của đa giác xấp xỉ (Polygon), 
                hoặc None nếu không tìm thấy vùng hợp lệ.
        """
        mask = self.get_mask(img)
        polygons = self.find_largest_external_polygon(mask, Approx_value ,min_area)
        return polygons
    
    
    def draw_polygon(self, image, polygon, color=(0, 255, 0), thickness=2):
        """Vẽ đa giác xấp xỉ lên ảnh gốc.

        Args:
            image (np.ndarray): Ảnh gốc (BGR) cần vẽ lên.
            polygon (np.ndarray | None): Tọa độ các đỉnh đa giác (từ hàm get_polygon).
            color (tuple, optional): Màu sắc của nét vẽ dạng BGR. Mặc định là (0, 255, 0) - Màu xanh lá.
            thickness (int, optional): Độ dày của nét vẽ. Mặc định là 2. Nếu set -1 sẽ tô kín đa giác.

        Returns:
            np.ndarray: Ảnh đã được vẽ đa giác lên (bản sao hoặc vẽ trực tiếp tùy thuộc vào việc clone ảnh).
        """
        if polygon is None:
            print("Warning: No polygon provided to draw.")
            return image.copy()    
        # Tạo một bản sao của ảnh để tránh ghi đè trực tiếp lên ảnh gốc nếu không muốn
        annotated_image = image.copy()
        # cv2.polylines yêu cầu một list các cụm polygon [poly1, poly2,...]
        # Tham số True xác định đây là đa giác khép kín
        cv2.polylines(
            annotated_image, 
            [polygon], 
            isClosed=True, 
            color=color, 
            thickness=thickness
        )
        return annotated_image
    
    def predict(self,image):

        """Thực hiện feed-forward ảnh qua mô hình để lấy mặt nạ phân đoạn (binary mask).
        Hàm sẽ tự động áp dụng hàm sigmoid, lọc ngưỡng threshold, khôi phục kích thước 
        về ảnh gốc và chuyển đổi định dạng về mask nhị phân (0 hoặc 255).
        Args:
            image (np.ndarray): Ảnh gốc đầu vào (BGR).
        Returns:
            np.ndarray: Mặt nạ phân đoạn nhị phân (0 hoặc 255) có cùng kích thước (H, W) với ảnh gốc.
        """
        h, w = image.shape[:2]
        x = self.preprocess(image)
        with self._predict_lock:
            with torch.no_grad():
                logits = self.model(x)
                probs = torch.sigmoid(logits)
            mask = (probs > self.config.threshold).to(torch.uint8)
            mask = mask.squeeze().cpu().numpy() * 255
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
        mask = mask.astype(np.uint8)
        return mask
    

    def unload(self):
        """Giải phóng mô hình khỏi bộ nhớ RAM và VRAM (GPU).
        Chuyển trọng số về CPU, xóa đối tượng, xóa cache của CUDA 
        và kích hoạt bộ thu gom rác tự động `gc.collect()`.
        """
        if self.model is not None:
            try:
                self.model.to("cpu")
            except Exception:
                pass
            del self.model
            self.model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        gc.collect()
        print("Model unloaded")


    def warmup(self):
        """Chạy thử nghiệm mô hình (Warmup) với một ảnh đen (dummy image).
        Mục đích giúp khởi tạo bộ nhớ GPU trước, tránh bị delay (trễ thời gian) 
        ở lượt infer đầu tiên khi hệ thống thực tế chạy.
        """
        print("Warmup: Running model with dummy image")
        dummy_image = np.zeros((224, 224, 3), dtype=np.uint8)  # Ảnh đen
        self.predict(dummy_image)
        print("RunOne Unet Compelete")



    def clean_mask_opening(self, mask, kernel_size=3, iterations=1):
        """
            Làm sạch mask bằng phép Morphology Opening (Erosion + Dilation)
            Parameters:
                mask (np.ndarray): Ảnh mask nhị phân (0 hoặc 255)
                kernel_size (int): Kích thước kernel (ví dụ: 3 → kernel 3x3)
                iterations (int): Số lần lặp phép morphology
            Returns:
                np.ndarray: Mask đã được làm sạch
        """
        mask = mask.astype(np.uint8)
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        mask_clean = cv2.morphologyEx(
                mask,
                cv2.MORPH_OPEN,
                kernel,
                iterations=iterations
            )
        return mask_clean
    
    def find_largest_external_polygon(self, mask, Approx_value,min_area=100):
        """
        Tìm contour ngoài cùng, lọc theo diện tích và xấp xỉ polygon
        Parameters:
            mask (np.ndarray): Mask nhị phân (0 hoặc 255)
            min_area (int): Diện tích tối thiểu để giữ contour
        Returns:
            poly (np.ndarray | None): Polygon xấp xỉ contour lớn nhất
        """
        mask = mask.astype(np.uint8)
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return None
        # 🔹 Lọc contour theo diện tích
        valid_contours = [
            cnt for cnt in contours
            if cv2.contourArea(cnt) >= min_area
        ]
        if not valid_contours:
            return None
        # 🔹 Lấy contour lớn nhất
        cnt = max(valid_contours, key=cv2.contourArea)
        # 🔹 Approx polygon (chuẩn hình học)
        epsilon = Approx_value * cv2.arcLength(cnt, True)
        #         epsilon = 0.002 * cv2.arcLength(cnt, True)   cung ok
        poly = cv2.approxPolyDP(cnt, epsilon, True)
        return poly
    