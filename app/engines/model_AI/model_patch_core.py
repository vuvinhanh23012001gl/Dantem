import threading
from pathlib import Path
from app.model import BaseAI
from app.config import PatchCoreAnomalyConfig
from app.config.path_config import PATH_FILE_RESNET18_BACKBONE
# pyrefly: ignore [missing-import]
import torch
# pyrefly: ignore [missing-import]
import torchvision.transforms as T
# pyrefly: ignore [missing-import]
from torchvision.models import resnet18, ResNet18_Weights
# pyrefly: ignore [missing-import]
import torch.nn.functional as F
import numpy as np
import faiss
import cv2
from PIL import Image

class ModelPatchCore(BaseAI):
    """Lớp thực hiện khởi tạo, dự đoán bất thường và trích xuất vùng lỗi (Bounding Box) bằng thuật toán PatchCore.
    Kế thừa từ BaseAI, hỗ trợ trích xuất đặc trưng phân vùng đa cấp từ ResNet18, tìm kiếm láng giềng gần nhất 
    qua thư viện FAISS tăng tốc, sinh bản đồ nhiệt (Heatmap) và khoanh vùng đối tượng lỗi.
    """
    def __init__(self, config: PatchCoreAnomalyConfig):
        """Khởi tạo cấu hình tham số cho mô hình PatchCore.
        Args:
            config (PatchCoreAnomalyConfig): Đối tượng chứa toàn bộ tham số cấu hình của mô hình.
        """
        self.config = config
        self.index = None
        self.resnet = None
        self.layer2 = None
        self.layer3 = None
        self.layer4 = None
        self.transform = None
        self._predict_lock = threading.Lock()

    def load_model(self):
        """Khởi tạo bộ chuyển đổi dữ liệu, nạp cơ sở dữ liệu vector FAISS (Index) 
        và trích xuất các tầng mạng (layer2, layer3, layer4) từ kiến trúc ResNet18 pre-trained.
        """
        self.transform = T.Compose([
            T.Resize((self.config.img_size, self.config.img_size)),
            T.ToTensor(),
            T.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])
        self.index = faiss.read_index(self.config.index_path)
        self.index.nprobe = self.config.nprobe

        self.resnet = resnet18(weights=None)
        backbone_path = Path(PATH_FILE_RESNET18_BACKBONE)
        if backbone_path.exists():
            state_dict = torch.load(str(backbone_path), map_location=self.config.device)
            self.resnet.load_state_dict(state_dict)
        else:
            hub_cache = Path(torch.hub.get_dir()) / "checkpoints" / "resnet18-f37072fd.pth"
            if hub_cache.exists():
                state_dict = torch.load(str(hub_cache), map_location=self.config.device)
                self.resnet.load_state_dict(state_dict)
            else:
                self.resnet = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        self.resnet.to(self.config.device)
        self.resnet.eval()

        self.layer2 = torch.nn.Sequential(*list(self.resnet.children())[:5])
        self.layer3 = torch.nn.Sequential(*list(self.resnet.children())[5:6])
        self.layer4 = torch.nn.Sequential(*list(self.resnet.children())[6:7])

    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """Tiền xử lý ảnh thô từ mảng NumPy sang dạng Tensor chuẩn hóa chuẩn bị đưa vào mô hình backbone.
        Args:
            image (np.ndarray): Ảnh đầu vào dạng mảng NumPy hệ màu RGB.
        Returns:
            torch.Tensor: Tensor đã định dạng lại kích thước, thêm chiều batch dạng (1, C, H, W).
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        return self.transform(image).unsqueeze(0).to(self.config.device)

    def _extract_features(self, img_tensor: torch.Tensor) -> np.ndarray:
        """Hàm nội bộ thực hiện trích xuất, gom cụm (pooling) và ghép nối các đặc trưng phân vùng (Patches) đa cấp.
        Args:
            img_tensor (torch.Tensor): Tensor ảnh đầu vào đã qua tiền xử lý dạng (1, C, H, W).
        Returns:
            np.ndarray: Mảng đặc trưng đã làm phẳng không gian và chuẩn hóa L2, dạng (HW, C).
        """
        with torch.no_grad():
            f2 = self.layer2(img_tensor)
            f3 = self.layer3(f2)
            f4 = self.layer4(f3)

            f2 = F.adaptive_avg_pool2d(f2, (14, 14))
            f3 = F.adaptive_avg_pool2d(f3, (14, 14))
            f4 = F.adaptive_avg_pool2d(f4, (14, 14))

            f2 = f2.flatten(2).transpose(1, 2)
            f3 = f3.flatten(2).transpose(1, 2)
            f4 = f4.flatten(2).transpose(1, 2)

            feat = torch.cat([f2, f3, f4], dim=-1)
            feat = F.normalize(feat, dim=-1)

        return feat.squeeze(0).cpu().numpy()

    def _generate_threshold_heatmap(
        self,
        anomaly_map: np.ndarray,
        target_shape: tuple[int, int],
        threshold: float | None = None,
    ) -> np.ndarray:
        """Sinh ảnh bản đồ nhiệt màu JET chuẩn hóa theo ngưỡng phát hiện bất thường (Threshold-anchored).

        Nguyên lý trực quan công nghiệp:
        - Vùng có điểm < threshold (bình thường/OK): Ánh xạ vào dải màu lạnh (Cool: Xanh dương -> Lục lam, uint8 0..120).
          Tránh hiện tượng Relative Min-Max thổi phồng điểm nhiễu cực nhỏ (ví dụ 0.013) thành màu đỏ rực.
        - Vùng có điểm >= threshold (bất thường/NG): Ánh xạ vào dải màu nóng (Hot: Vàng -> Cam -> Đỏ, uint8 120..255).

        Args:
            anomaly_map (np.ndarray): Bản đồ bất thường thô (14x14) từ FAISS.
            target_shape (tuple[int, int]): Kích thước (height, width) ảnh đích cần resize.
            threshold (float | None): Ngưỡng phán định bất thường. Nếu None, mặc định là 0.1.

        Returns:
            np.ndarray: Ảnh heatmap màu JET hệ màu BGR kích thước target_shape.
        """
        th = float(threshold) if threshold is not None and threshold > 0 else 0.1
        norm_map = np.zeros_like(anomaly_map, dtype=np.float32)

        under_thresh = anomaly_map < th
        over_thresh = ~under_thresh

        # Điểm dưới ngưỡng th: ánh xạ 0..th vào dải màu lạnh 0..120 (Cool: Blue -> Cyan -> Green)
        norm_map[under_thresh] = (anomaly_map[under_thresh] / max(th, 1e-6)) * 120.0

        # Điểm vượt ngưỡng th: ánh xạ th..max vào dải màu nóng 120..255 (Hot: Yellow -> Orange -> Red)
        max_val = max(th * 1.5, float(anomaly_map.max()), 1e-6)
        if max_val > th:
            norm_map[over_thresh] = 120.0 + ((anomaly_map[over_thresh] - th) / (max_val - th)) * 135.0
        else:
            norm_map[over_thresh] = 120.0

        norm_map = np.clip(norm_map, 0, 255).astype(np.uint8)
        norm_map_resized = cv2.resize(norm_map, (target_shape[1], target_shape[0]))
        return cv2.applyColorMap(norm_map_resized, cv2.COLORMAP_JET)

    def predict(
        self,
        image: np.ndarray,
        threshold: float | None = None,
    ) -> tuple[float, np.ndarray]:
        """Thực hiện tính toán độ bất thường tổng thể và sinh bản đồ nhiệt (Heatmap Overlay) đổ màu JET lên ảnh gốc.
        Args:
            image (np.ndarray): Ảnh gốc đầu vào hệ màu RGB.
            threshold (float | None): Ngưỡng bất thường dùng để neo dải màu heatmap (mặc định 0.1).
        Returns:
            tuple[float, np.ndarray]: Cặp giá trị gồm điểm bất thường tối đa (score) 
                và ảnh kết quả đã đè bản đồ nhiệt (overlay_heatmap) hệ màu BGR.
        Raises:
            RuntimeError: Nếu mô hình hoặc bộ chỉ mục FAISS chưa được tải.
        """
        if self.index is None or self.resnet is None:
            raise RuntimeError("Mô hình chưa được load. Vui lòng gọi hàm load_model() trước khi predict.")
        
        with self._predict_lock:
            img_tensor = self.preprocess(image)
            feats = self._extract_features(img_tensor)
            
            D, _ = self.index.search(feats.astype(np.float32), 1)
            anomaly_map = D.reshape(14, 14)
            score = float(anomaly_map.max())
            
            heatmap_color = self._generate_threshold_heatmap(
                anomaly_map,
                (image.shape[0], image.shape[1]),
                threshold=threshold,
            )
            
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if image.ndim == 3 else image
            overlay = cv2.addWeighted(image_bgr, self.config.overlay_alpha, heatmap_color, 1 - self.config.overlay_alpha, 0)
            return score, overlay

    def predict_with_anomaly_boxes(
        self,
        image: np.ndarray,
        threshold: float,
        min_area: int = 50,
    ) -> tuple[float, np.ndarray, list[tuple[int, int, int, int]]]:
        """Dự đoán anomaly score, tạo heatmap overlay và trích xuất bounding boxes theo ngưỡng bất thường thực tế.

        Args:
            image (np.ndarray): Ảnh ROI đầu vào (RGB hoặc BGR).
            threshold (float): Ngưỡng điểm bất thường dùng để trích xuất các vùng heatmap bất thường.
            min_area (int): Diện tích tối thiểu (pixel) của vùng bất thường để tạo bounding box.

        Returns:
            tuple[float, np.ndarray, list[tuple[int, int, int, int]]]:
                - score (float): Điểm bất thường cao nhất trên ảnh ROI.
                - overlay (np.ndarray): Ảnh overlay heatmap trực quan.
                - bounding_boxes (list[tuple[int, int, int, int]]): Danh sách các box (x, y, w, h) của vùng bất thường.
        """
        if self.index is None or self.resnet is None:
            raise RuntimeError("Mô hình chưa được load. Vui lòng gọi hàm load_model() trước khi predict.")

        with self._predict_lock:
            img_tensor = self.preprocess(image)
            feats = self._extract_features(img_tensor)

            D, _ = self.index.search(feats.astype(np.float32), 1)
            anomaly_map = D.reshape(14, 14)
            score = float(anomaly_map.max())

            heatmap_color = self._generate_threshold_heatmap(
                anomaly_map,
                (image.shape[0], image.shape[1]),
                threshold=threshold,
            )

            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if image.ndim == 3 else image
            overlay = cv2.addWeighted(
                image_bgr,
                self.config.overlay_alpha,
                heatmap_color,
                1 - self.config.overlay_alpha,
                0,
            )

            bounding_boxes: list[tuple[int, int, int, int]] = []
            if score > threshold:
                anomaly_map_resized = cv2.resize(anomaly_map, (image.shape[1], image.shape[0]))
                binary_mask = (anomaly_map_resized >= threshold).astype(np.uint8) * 255
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)

                contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                raw_boxes = []
                for contour in contours:
                    if cv2.contourArea(contour) >= min_area:
                        bx, by, bw, bh = cv2.boundingRect(contour)
                        raw_boxes.append((bx, by, bw, bh))

                if raw_boxes:
                    bounding_boxes = self._merge_overlapping_boxes(raw_boxes)

            return score, overlay, bounding_boxes


    def warmup(self):
        """Chạy thử nghiệm mô hình (Warmup) với một ảnh đen (dummy image) giúp khởi tạo cấu trúc bộ nhớ thiết bị."""
        if self.resnet is None:
            return
        dummy_img = np.zeros((self.config.img_size, self.config.img_size, 3), dtype=np.uint8)
        _ = self.predict(dummy_img)

    def unload(self):
        """Giải phóng hoàn toàn các tài nguyên nặng của mô hình, dọn dẹp RAM của FAISS Index và VRAM của CUDA GPU."""
        self.index = None
        self.resnet = None
        self.layer2 = None
        self.layer3 = None
        self.layer4 = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def get_bounding_boxes(self, image: np.ndarray) -> np.ndarray:
        """Dự đoán và trích xuất trực tiếp ảnh gốc được vẽ đè các khung bao quanh vùng bất thường (Bounding Box).
        Args:
            image (np.ndarray): Ảnh gốc đầu vào cần xử lý phát hiện lỗi (RGB).
        Returns:
            np.ndarray: Ảnh mới đã được vẽ kèm khung hình chữ nhật và nhãn thông tin vùng lỗi.
        Raises:
            RuntimeError: Nếu mô hình hoặc bộ chỉ mục FAISS chưa được tải.
        """
        if self.index is None or self.resnet is None:
            raise RuntimeError("Mô hình chưa được load. Vui lòng gọi hàm load_model() trước khi predict.")
        img_tensor = self.preprocess(image)
        feats = self._extract_features(img_tensor)
        D, _ = self.index.search(feats.astype(np.float32), 1)
        anomaly_map = D.reshape(14, 14)
        bounding_boxes, _ = self.get_bounding_box(anomaly_map, image.shape)
        # img = self.draw_bounding_boxes(image, bounding_boxes)
        return bounding_boxes


    def get_bounding_box(self, anomaly_map: np.ndarray, img_shape: tuple[int, int], threshold_ratio: float = 0.3, min_area: int = 100) -> tuple[list[tuple[int, int, int, int]], np.ndarray]:
        """Tính toán phân ngưỡng động bản đồ bất thường, lọc nhiễu hạt và trích xuất danh sách tọa độ các khung bao lỗi.

        Phiên bản này dùng nhiều ngưỡng và xử lý morphology nhẹ để giảm hiện tượng gộp
        nhiều vùng bất thường thành 1 bounding box khi các hotspot ở gần nhau.
        """
        h_max, h_min = anomaly_map.max(), anomaly_map.min()
        if h_max - h_min < 1e-6:
            return [], np.zeros(img_shape[:2], dtype=np.uint8)

        heatmap = (anomaly_map - h_min) / (h_max - h_min + 1e-6)
        heatmap = cv2.resize(heatmap, (img_shape[1], img_shape[0]))
        heatmap = np.uint8(255 * heatmap)

        thresholds = [
            max(20, int(threshold_ratio * 255)),
            max(15, int(threshold_ratio * 255 * 0.7)),
        ]

        bounding_boxes: list[tuple[int, int, int, int]] = []
        final_mask = np.zeros(img_shape[:2], dtype=np.uint8)

        for thresh_value in thresholds:
            _, thresh = cv2.threshold(heatmap, thresh_value, 255, cv2.THRESH_BINARY)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            final_mask = cv2.bitwise_or(final_mask, thresh)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    bounding_boxes.append((x, y, w, h))

        if not bounding_boxes:
            return [], final_mask

        return self._merge_overlapping_boxes(bounding_boxes), final_mask

    @staticmethod
    def _merge_overlapping_boxes(
        boxes: list[tuple[int, int, int, int]],
    ) -> list[tuple[int, int, int, int]]:
        """Gộp các box bất thường giao nhau hoặc nằm trong cùng một vùng.

        Args:
            boxes: Danh sách box dạng ``(x, y, width, height)``.

        Returns:
            list[tuple[int, int, int, int]]: Box đã gộp, không còn các vùng
                giao nhau. Các box tách biệt vẫn được giữ riêng.

        Raises:
            ValueError: Nếu một box không có đủ bốn giá trị.
        """
        merged = []
        for raw_box in sorted(boxes, key=lambda item: (item[0], item[1])):
            if len(raw_box) != 4:
                raise ValueError("bounding box phải có dạng (x, y, width, height)")
            candidate = tuple(int(value) for value in raw_box)
            index = 0
            while index < len(merged):
                current = merged[index]
                if not ModelPatchCore._boxes_overlap(current, candidate):
                    index += 1
                    continue
                candidate = ModelPatchCore._union_boxes(current, candidate)
                merged.pop(index)
                index = 0
            merged.append(candidate)
        return sorted(merged, key=lambda item: (item[0], item[1]))

    @staticmethod
    def _boxes_overlap(
        first: tuple[int, int, int, int],
        second: tuple[int, int, int, int],
    ) -> bool:
        """Kiểm tra hai box có giao nhau với diện tích dương hay không."""
        first_x, first_y, first_width, first_height = first
        second_x, second_y, second_width, second_height = second
        return (
            max(first_x, second_x) < min(first_x + first_width, second_x + second_width)
            and max(first_y, second_y) < min(first_y + first_height, second_y + second_height)
        )

    @staticmethod
    def _union_boxes(
        first: tuple[int, int, int, int],
        second: tuple[int, int, int, int],
    ) -> tuple[int, int, int, int]:
        """Trả box nhỏ nhất bao phủ toàn bộ hai box đầu vào."""
        left = min(first[0], second[0])
        top = min(first[1], second[1])
        right = max(first[0] + first[2], second[0] + second[2])
        bottom = max(first[1] + first[3], second[1] + second[3])
        return left, top, right - left, bottom - top

    def draw_bounding_boxes(self, image: np.ndarray, boxes: list[tuple[int, int, int, int]], color: tuple[int, int, int] = (0, 255, 0), thickness: int = 2, label: str = "Anomaly") -> np.ndarray:
        """Thực hiện vẽ các hộp chữ nhật bao quanh vùng lỗi kèm nhãn nền màu tương ứng lên bản sao của ảnh gốc.
        Args:
            image (np.ndarray): Ảnh gốc NumPy array (hỗ trợ cả hệ màu RGB và BGR).
            boxes (list): Danh sách chứa tọa độ các khung bao lỗi cần vẽ.
            color (tuple, optional): Cấu trúc màu sắc đại diện cho nét vẽ. Mặc định là màu Xanh lá (0, 255, 0).
            thickness (int, optional): Độ dày nét của đường khung chữ nhật. Mặc định là 2.
            label (str, optional): Chuỗi văn bản hiển thị phía trên hộp. Mặc định là "Anomaly". Nếu là None sẽ bỏ qua nhãn.
        Returns:
            np.ndarray: Ảnh đầu ra mới có chứa đầy đủ thông tin các Bounding Box đã vẽ đè.
        """
        output_image = image.copy()
        for x, y, w, h in boxes:
            start_point = (x, y)
            end_point = (x + w, y + h)
            cv2.rectangle(output_image, start_point, end_point, color, thickness)
            if label:
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                font_thickness = 1
                (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
                text_y = y - 5 if y - text_h - 5 > 0 else y + text_h + 5
                text_x = x
                bg_start = (text_x, text_y - text_h - baseline)
                bg_end = (text_x + text_w, text_y + baseline)
                cv2.rectangle(output_image, bg_start, bg_end, color, -1)
                
                cv2.putText(
                    output_image,
                    label,
                    (text_x, text_y),
                    font,
                    font_scale,
                    (255, 255, 255),
                    font_thickness,
                    lineType=cv2.LINE_AA,
                )
        return output_image