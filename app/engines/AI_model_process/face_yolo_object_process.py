from app.engines.model_AI import ModelYoloObject
import numpy as np
from app.utils import Tool_OpenCv2
import cv2
from typing import Tuple, Optional,Union

class FaceModelYoloObject:
    def __init__(self, model: ModelYoloObject, limit_number_object: Optional[int] = None):
        self.model = model
        self.limit_number_object = limit_number_object

    def get_objects(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> tuple[list[dict], np.ndarray]:
        """Lấy danh sách các đối tượng detect được trên ảnh gốc (bằng cách infer trên vùng crop).

        Args:
            image: Ảnh gốc đầu vào.
            x1, y1: Tọa độ góc trái trên của vùng crop.
            x2, y2: Tọa độ góc phải dưới của vùng crop.

        Returns:
            tuple[list[dict], np.ndarray]: Danh sách object đã quy đổi về ảnh gốc
                và ảnh crop dùng để inference.

        Raises:
            Lỗi crop hoặc inference được truyền tiếp từ OpenCV và model.
        """
        # Crop ảnh sử dụng công cụ OpenCV có sẵn của hệ thống
        image_crop, left, top = Tool_OpenCv2.crop_image(
            image, x1, y1, x2, y2
        )
        # Thực hiện gọi mô hình YOLO Object để nhận diện trên vùng ảnh nhỏ
        objects = self.model.get_result(image_crop)
        # Chuyển đổi toàn bộ tọa độ các hộp bao tìm được về lại hệ tọa độ ảnh gốc
        list_coordinate_object = self.convert_objects_to_original_image(
            objects,
            left,
            top,
            image.shape[1],  # image_width
            image.shape[0]   # image_height
        )
        return list_coordinate_object,image_crop


    def convert_objects_to_original_image(
        self,
        objects: list[dict],
        left: int,
        top: int,
        image_width: int,
        image_height: int
    ) -> list[dict]:
        """Dịch chuyển tọa độ bbox từ vùng crop về hệ tọa độ của ảnh gốc.
        Args:
            objects: Danh sách kết quả từ model (hệ tọa độ crop).
            left: Độ lệch X (offset) của vùng crop.
            top: Độ lệch Y (offset) của vùng crop.
            image_width: Chiều rộng ảnh gốc.
            image_height: Chiều cao ảnh gốc.
            
        Returns:
            list[dict]: Danh sách kết quả với tọa độ bbox chuẩn ảnh gốc.
        """
        for obj in objects:
            bbox = obj["bbox"]
            
            # Tịnh tiến các tọa độ hộp bao theo độ lệch left, top của vùng crop
            obj["bbox"] = {
                "x1": bbox["x1"] + left,
                "y1": bbox["y1"] + top,
                "x2": bbox["x2"] + left,
                "y2": bbox["y2"] + top,
            }

            # Cập nhật lại thông tin kích thước của bức ảnh cha (ảnh gốc)
            obj["image_width"] = image_width
            obj["image_height"] = image_height

        return objects


    def filter_objects_by_class_name(
        self, 
        list_coordinate_object: list[dict], 
        class_name: str
    ) -> tuple[list[dict], bool]:
        """Lọc danh sách đối tượng dựa vào một class_name cụ thể và kiểm tra trạng thái tồn tại.
        Args:
            list_coordinate_object: Danh sách dict kết quả (trả về từ get_objects hoặc get_result).
            class_name: Tên class đơn lẻ cần lọc (Ví dụ: "hole").
        Returns:
            tuple:
                - list[dict]: Danh sách các đối tượng khớp với class_name truyền vào.
                - bool: Trạng thái tồn tại của class đó (True nếu có ít nhất 1 object, False nếu không).
        """
        # 1. Chuẩn hóa tên class cần tìm
        target_name = class_name.strip().lower()
        filtered_objects = []
        is_exist = False
        # 2. Duyệt mảng và gom kết quả
        for obj in list_coordinate_object:
            obj_class_name = obj.get("class_name", "").strip().lower()
            
            if obj_class_name == target_name:
                filtered_objects.append(obj)
                is_exist = True  # Đánh dấu đã tìm thấy ít nhất 1 đối tượng thuộc class này
        return filtered_objects, is_exist
    def draw_rectangle(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int] = (0, 255, 0), thickness: int = 2) -> np.ndarray:
        """Vẽ khung chữ nhật lên ảnh."""
        image_draw = image.copy()
        cv2.rectangle(image_draw, (x1, y1), (x2, y2), color, thickness)
        return image_draw
    
    
    def search(self, img: np.ndarray, x1: int, y1: int, x2: int, y2: int, target_class_value: str) -> Tuple[bool, list[str], np.ndarray, list[dict]]:
        """Nhận diện và kiểm tra đối tượng của một class trong vùng ảnh chỉ định.
        Args:
            img (np.ndarray): Ảnh đầu vào.
            x1 (int): Tọa độ X góc trên trái.
            y1 (int): Tọa độ Y góc trên trái.
            x2 (int): Tọa độ X góc dưới phải.
            y2 (int): Tọa độ Y góc dưới phải.
            target_class_value (str): Tên class cần kiểm tra.

        Returns:
            Tuple[bool, list[str], np.ndarray, list[dict]]:
                - bool: True nếu đạt yêu cầu, False nếu phát hiện lỗi.
                - list[str]: Danh sách thông báo.
                - np.ndarray: Ảnh kết quả.
                - list[dict]: Danh sách đối tượng sau khi lọc.
        """
        messages = []
        objects,img_crop= self.get_objects(img, x1, y1, x2, y2)
        print("objects",objects)
        filtered_objects, _ = self.filter_objects_by_class_name(objects, target_class_value)
        img_result = self.draw_rectangle(img, x1, y1, x2, y2)
        img_result = self.draw(img_result, filtered_objects)
        # self.show(img_result, filtered_objects, window_name="Detection Result")
        if not filtered_objects:
            messages.append(f"LỖI: Không tìm thấy đối tượng '{target_class_value}'.")
            return False, messages, img_result, []
        if isinstance(self.limit_number_object, int) and len(filtered_objects) > self.limit_number_object:
            messages.append(f"LỖI: Phát hiện {len(filtered_objects)} đối tượng '{target_class_value}', vượt giới hạn {self.limit_number_object}.")
        for index, obj in enumerate(filtered_objects, start=1):
            if obj.get("touch_x") or obj.get("touch_y"):
                messages.append(f"LỖI: Đối tượng '{target_class_value}' thứ {index} bị chạm biên ảnh.")
        if messages:
            return False, messages, img_result, filtered_objects
        messages.append(f"OK: Phát hiện {len(filtered_objects)} đối tượng '{target_class_value}' hợp lệ.")
        return True, messages, img_result, filtered_objects
    
    
    def search_negative(self, img: np.ndarray, x1: int, y1: int, x2: int, y2: int, target_class_value: str) -> Tuple[bool, list[str], np.ndarray]: # ham nay nguoc voi ham search
        """Kiểm tra xem vùng chỉ định có SẠCH/TRỐNG (không chứa vật thể mục tiêu) hay không.
        Hàm này thực hiện nhận diện đối tượng trên vùng ảnh được cắt (crop). 
        Ngược lại với hàm search, hàm này kỳ vọng KHÔNG tìm thấy vật thể nào thuộc class mục tiêu.
        Nếu phát hiện thấy vật thể mục tiêu -> CÓ LỖI (Trả về False).
        Nếu vùng ảnh trống sạch, không có vật thể mục tiêu -> ĐẠT CHUẨN (Trả về True).
        Args:
            img (np.ndarray): Ảnh gốc đầu vào cần kiểm tra.
            x1, y1: Tọa độ góc trái trên của vùng kiểm tra (vùng crop).
            x2, y2: Tọa độ góc phải dưới của vùng kiểm tra (vùng crop).
            target_class_value (str): Tên class mục tiêu KHÔNG ĐƯỢC PHÉP xuất hiện (Ví dụ: "foreign_object", "hole").
        Returns:
            Tuple[bool, list[str], np.ndarray]:
                - bool: Trạng thái đánh giá tổng (True nếu TRỐNG/ĐẠT CHUẨN, False nếu CÓ VẬT THỂ/LỖI).
                - list[str]: Danh sách các chuỗi tin nhắn thông báo lỗi hoặc thông báo thành công.
                - np.ndarray: Ảnh kết quả. Trả về ảnh gốc chưa vẽ nếu đạt chuẩn, 
                             hoặc ảnh đã vẽ bounding box của các vật thể lỗi nếu phát hiện vi phạm.
        """    
        messages = []
        # 1. Lấy tất cả các đối tượng trong vùng crop
        all_objects, _ = self.get_objects(img, x1, y1, x2, y2)
        # 2. Lọc ra danh sách chứa class_name mục tiêu cấm xuất hiện
        filtered_objects, is_exist = self.filter_objects_by_class_name(all_objects, target_class_value)
        # 3. Tiến hành vẽ các đối tượng vi phạm lên ảnh (nếu có)
        img_visualized = self.draw(img, filtered_objects)
        cv2.rectangle(
            img_visualized,
            (int(x1), int(y1)),
            (int(x2), int(y2)),
            (255, 0, 0),
            2,
        )
        # --- Logic kiểm tra ngược (Negative Check) ---
        # Nếu tìm thấy bất kỳ đối tượng nào thuộc class cấm -> BÁO LỖI
        if is_exist:
            messages.append(f"LỖI: Phát hiện thấy {len(filtered_objects)} đối tượng '{target_class_value}' xuất hiện trong vùng cấm.")
            # Kiểm tra thêm xem đối tượng vi phạm có bị lỗi khuyết hình/chạm biên hay không
            for idx, obj in enumerate(filtered_objects):
                if obj.get("touch_x", False) or obj.get("touch_y", False):
                    messages.append(f"CẢNH BÁO: Đối tượng vi phạm thứ {idx + 1} đang bị chạm biên ảnh.")
            return False, messages, img_visualized
        # Nếu không tìm thấy đối tượng nào -> ĐẠT CHUẨN
        success_msg = f"OK: Vùng kiểm tra đạt chuẩn. Không phát hiện đối tượng '{target_class_value}' nào."
        return True, [success_msg], img_visualized
    
    def search_all_negative(self, img: np.ndarray, x1: int, y1: int, x2: int, y2: int, color=(255, 0, 0)) -> Tuple[bool, list[str], np.ndarray]:
            """Kiểm tra xem vùng chỉ định có HOÀN TOÀN TRỐNG (không chứa bất kỳ vật thể nào) hay không.
            Hàm này thực hiện nhận diện đối tượng trên vùng ảnh được cắt (crop).
            Nếu phát hiện BẤT KỲ vật thể nào thuộc BẤT KỲ class nào -> CÓ LỖI (Trả về False).
            Nếu vùng ảnh hoàn toàn sạch, không có vật thể nào -> ĐẠT CHUẨN (Trả về True).
            
            Args:
                img (np.ndarray): Ảnh gốc đầu vào cần kiểm tra.
                x1, y1: Tọa độ góc trái trên của vùng kiểm tra (vùng cấm/vùng crop).
                x2, y2: Tọa độ góc phải dưới của vùng kiểm tra (vùng cấm/vùng crop).
                color (tuple): Màu sắc dùng để vẽ khung vùng kiểm tra và các vật thể lỗi bên trong (mặc định là Xanh Dương/Đỏ tùy hệ BGR).
                
            Returns:
                Tuple[bool, list[str], np.ndarray]:
                    - bool: Trạng thái đánh giá tổng (True nếu TRỐNG/ĐẠT CHUẨN, False nếu CÓ VẬT THỂ/LỖI).
                    - list[str]: Danh sách các chuỗi tin nhắn thông báo lỗi hoặc thông báo thành công.
                    - np.ndarray: Ảnh kết quả có vẽ khung kiểm tra và các vật thể lỗi nếu có.
            """
            messages = []
            
            # 1. Lấy tất cả các đối tượng trong vùng crop (không lọc theo class)
            all_objects = self.get_objects(img, x1, y1, x2, y2)
            
            # 2. Tiến hành vẽ tất cả các đối tượng lỗi phát hiện được lên ảnh (nếu có)
            img_visualized = self.draw(img, all_objects, color)
            
            # 3. VẼ KHUNG CỦA VÙNG KIỂM TRA (x1, y1, x2, y2)
            # Vẽ một khung chữ nhật bao quanh toàn bộ vùng cấm để người vận hành máy dễ quan sát
            # Độ dày nét vẽ = 2, bạn có thể tăng lên nếu muốn nhìn rõ hơn
            cv2.rectangle(img_visualized, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            
            # Ghi nhãn tên vùng kiểm tra ngay phía trên khung
            text_y = max(20, int(y1) - 8)
            cv2.putText(img_visualized, "SCAN ZONE", (int(x1), text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

            # --- Logic kiểm tra trống hoàn toàn (Absolute Negative Check) ---
            # Nếu danh sách đối tượng không trống -> CÓ LỖI (Phát hiện dị vật/linh kiện thừa)
            if all_objects:
                messages.append(f"LỖI: Phát hiện thấy {len(all_objects)} vật thể lạ xuất hiện trong vùng cấm.")    
                # Liệt kê chi tiết các class và vị trí bị vi phạm để dễ track log
                for idx, obj in enumerate(all_objects):
                    class_name = obj.get("class_name", "Unknown")
                    confidence = obj.get("confidence", 0.0)
                    msg_detail = f" - Vật thể {idx + 1}: Class '{class_name}' (Độ tin cậy: {confidence:.2f})"
                    if obj.get("touch_x", False) or obj.get("touch_y", False):
                        msg_detail += " [Bị chạm biên]"
                    messages.append(msg_detail)
                return False, messages, img_visualized 
                
            # Nếu không tìm thấy bất kỳ đối tượng nào -> ĐẠT CHUẨN
            success_msg = "OK: Vùng kiểm tra đạt chuẩn. Không phát hiện bất kỳ vật thể nào."
            
            # Lưu ý: Ngay cả khi OK (Đạt chuẩn), ta vẫn trả về `img_visualized` để hiển thị 
            # cái khung chữ nhật vùng quét lên màn hình monitor cho trực quan.
            return True, [success_msg], img_visualized

    def draw(self, image: np.ndarray, objects: list[dict], color_config: Union[tuple, dict, None] = None) -> np.ndarray:
            """Vẽ bounding box và nhãn của danh sách đối tượng lên một bản sao của ảnh.

            Args:
                image (np.ndarray): Ảnh gốc đầu vào cần vẽ.
                objects (list[dict]): Danh sách các đối tượng cần vẽ (mỗi đối tượng chứa bbox, class_id, class_name, confidence).
                color_config (tuple | dict | None): Cấu hình màu sắc truyền vào:
                    - Nếu là tuple (B, G, R): Áp dụng một màu duy nhất này cho tất cả đối tượng.
                    - Nếu là dict: Định nghĩa màu riêng theo class_id hoặc class_name, ví dụ: {0: (0, 0, 255)} hoặc {"bubble": (0, 255, 0)}.
                    - Nếu là None: Tự động sinh màu ngẫu nhiên theo class_id như cũ.
                    
            Returns:
                np.ndarray: Một bản sao của ảnh gốc đã được vẽ đè các bounding box và thông tin nhãn.
            """
            image_draw = image.copy()
            
            for obj in objects:
                bbox = obj["bbox"]
                class_id = obj["class_id"]
                class_name = obj.get("class_name", "Unknown")
                x1, y1, x2, y2 = int(bbox["x1"]), int(bbox["y1"]), int(bbox["x2"]), int(bbox["y2"])
                
                # --- Logic xác định màu sắc (Color Resolution) ---
                if isinstance(color_config, tuple) and len(color_config) == 3:
                    # Cách 1: Sử dụng một màu duy nhất cố định cho tất cả
                    color = tuple(int(c) for c in color_config)
                elif isinstance(color_config, dict):
                    # Cách 2: Lấy màu từ dictionary cấu hình (ưu tiên theo class_id trước, class_name sau)
                    if class_id in color_config:
                        color = tuple(int(c) for c in color_config[class_id])
                    elif class_name in color_config:
                        color = tuple(int(c) for c in color_config[class_name])
                    else:
                        # Fallback nếu class không nằm trong dict cấu hình màu
                        np.random.seed(class_id)
                        color = tuple(int(c) for c in np.random.randint(0, 255, size=3))
                else:
                    # Cách 3: color_config là None -> Tự động sinh màu ngẫu nhiên theo class_id như cũ
                    np.random.seed(class_id)
                    color = tuple(int(c) for c in np.random.randint(0, 255, size=3))
                
                # Vẽ hộp bao (Bounding Box)
                cv2.rectangle(image_draw, (x1, y1), (x2, y2), color, 2)
                
                # Tính toán vị trí và vẽ chữ nhãn thông tin
                text_y = max(20, y1 - 5)
                label = f'{class_name} {obj["confidence"]:.2f}'
                cv2.putText(image_draw, label, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
            return image_draw


    def show(
        self,
        image: np.ndarray,
        objects: Optional[list[dict]] = None,
        window_name: str = "Result Detection"
    ) -> None:
        """Hiển thị ảnh kết quả detection bằng cửa sổ OpenCV.

        Args:
            image: Ảnh gốc hoặc ảnh đã được vẽ kết quả.
            objects: Danh sách object cần vẽ lên ảnh gốc. Nếu là ``None``,
                ảnh được hiển thị nguyên trạng.
            window_name: Tên cửa sổ OpenCV.
        Returns:
            None.
        Raises:
            cv2.error: Nếu môi trường không hỗ trợ cửa sổ GUI của OpenCV.
        """
        if image is None or image.size == 0:
            raise ValueError("Ảnh cần hiển thị không được rỗng")
        image_to_display = self.draw(image, objects) if objects is not None else image
        try:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            height, width = image_to_display.shape[:2]
            max_width = 1200
            if width > max_width:
                scale = max_width / width
                cv2.resizeWindow(window_name, int(width * scale), int(height * scale))
            else:
                cv2.resizeWindow(window_name, width, height)
            cv2.imshow(window_name, image_to_display)
            cv2.waitKey(0)
        except cv2.error as error:
            raise RuntimeError(
                "Không thể hiển thị ảnh bằng OpenCV. "
                "Hãy chạy trong môi trường có GUI hoặc lưu image_to_display ra file."
            ) from error
        finally:
            try:
                cv2.destroyWindow(window_name)
            except cv2.error:
                pass

FrameModelYoloObject = FaceModelYoloObject