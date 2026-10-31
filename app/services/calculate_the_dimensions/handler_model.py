import cv2
import torch
import numpy as np
import segmentation_models_pytorch as smp
import app.services.calculate_the_dimensions.config_detect as config_detect

class ModelHandler:
    def __init__(
        self,
        model_path,
        encoder="resnet34",
        device=None,
        img_size=512,
        threshold=0.5
           
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.img_size = img_size
        self.threshold = threshold

        # Load model
        self.model = smp.UnetPlusPlus(
            encoder_name=encoder,
            encoder_weights=None,
            in_channels=3,
            classes=1,
            activation=None
        ).to(self.device)

        self.model.load_state_dict(
            torch.load(model_path, map_location=self.device)
        )
        self.model.eval()
        
    def preprocess(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (self.img_size, self.img_size))
        # cv2.imshow("Mask", image)   resize giong voi luc train
        # cv2.waitKey(0)
        image = image.astype(np.float32) / 255.0  # chuyen tu anh 0-255 chuyen sang float de vao mo hinh
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        image = (image - mean) / std
        image = np.transpose(image, (2, 0, 1))  #  (H, W, C) sang (C, H, W)
        image = np.expand_dims(image, axis=0)
        return torch.from_numpy(image).to(self.device)
        
    def predict(self, image):
        h, w = image.shape[:2]
        x = self.preprocess(image)

        with torch.no_grad():
            logits = self.model(x)
            probs = torch.sigmoid(logits)

        print("Probs min/max:", probs.min().item(), probs.max().item())

        mask = (probs > self.threshold).to(torch.uint8)
        print("Mask unique:", torch.unique(mask))

        mask = mask.squeeze().cpu().numpy() * 255
        mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
        mask = mask.astype(np.uint8)
        return mask
    def clean_mask_opening(self,mask, kernel_size=3, iterations=1):
            """
            Làm sạch mask bằng phép Morphology Opening (Erosion + Dilation)

            Parameters:
                mask (np.ndarray): Ảnh mask nhị phân (0 hoặc 255)
                kernel_size (int): Kích thước kernel (ví dụ: 3 → kernel 3x3)
                iterations (int): Số lần lặp phép morphology

            Returns:
                np.ndarray: Mask đã được làm sạch
            """
            # Đảm bảo mask là uint8
            mask = mask.astype(np.uint8)

            # Tạo kernel
            kernel = np.ones((kernel_size, kernel_size), np.uint8)

            # Morphology Opening
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
    

                                
    def draw_contours(self,image, contours, color=(0, 255, 0), thickness=2):
        """
        Vẽ contours lên ảnh

        Parameters:
            image (np.ndarray): Ảnh gốc (BGR)
            contours (list): Danh sách contours
            color (tuple): Màu vẽ contour (B, G, R)
            thickness (int): Độ dày nét

        Returns:
            np.ndarray: Ảnh đã vẽ contour
        """
        img_draw = image.copy()

        if len(contours) > 0:
            cv2.drawContours(
                img_draw,
                contours,
                -1,
                color,
                thickness
            )

        return img_draw
    
    def find_external_contours_by_area(self, mask, min_area=100):
            """
            Tìm contour ngoài cùng và lọc theo diện tích

            Parameters:
                mask (np.ndarray): Mask nhị phân (0 hoặc 255)
                min_area (int): Diện tích tối thiểu để giữ contour

            Returns:
                list: Danh sách contours hợp lệ
            """
            mask = mask.astype(np.uint8)

            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            valid_contours = [
                cnt for cnt in contours
                if cv2.contourArea(cnt) >= min_area
            ]

            return valid_contours
    
    def get_polygon(self,img):
        mask  = self.predict(img) # Loc nhieu ảnh
        if mask:
            mask_clean= self.clean_mask_opening(mask,config_detect.Kernel) # Loc nhieu xung quanh
            polygon  = self.find_largest_external_polygon(mask_clean,config_detect.epsilon_ratio,config_detect.min_area)
            return polygon
        return None








# predictor = ModelHandler(
#     model_path=r"C:\Disk D\Project\Python_Detect_Width_Line\code\app\app\services\calculate_the_dimensions\unetpp.pth",
#     encoder="resnet34"
# )
# img = cv2.imread(r"C:\Disk D\Uset++\tool-train-Unet-\test.jpg")
# mask = predictor.predict(img)
# mask_clearn_7 = predictor.clean_mask_opening(mask,7)
# polygon_200= predictor.find_largest_external_polygon(mask_clearn_7,0.002)
# polygon_100= predictor.find_largest_external_polygon(mask_clearn_7,0.0017)
# polygon_500= predictor.find_largest_external_polygon(mask_clearn_7,0.003)  #cai nay chay on 
# contours = predictor.find_external_contours_by_area(mask_clearn_7)
# img_draw_polygon_100= predictor.draw_polygon(img,polygon_100)
# img_draw_polygon_200= predictor.draw_polygon(img,polygon_200)
# img_draw_polygon_500= predictor.draw_polygon(img,polygon_500)
# img_draw_contours = predictor.draw_contours(img,contours)
# cv2.imshow("img_draw_polygon_100", img_draw_polygon_100)
# cv2.imshow("img_draw_polygon_200", img_draw_polygon_200)
# cv2.imshow("img_draw_polygon_500", img_draw_polygon_500)
# cv2.imshow("contours", img_draw_contours)
# # img_draw_contours = predictor.draw_contours(img,contours)
# # cv2.imshow("contours", img_draw_contours)
# # cv2.imshow("Mask", mask)
# # cv2.imshow("mask_clearn_7", mask_clearn_7)
# cv2.waitKey(0)