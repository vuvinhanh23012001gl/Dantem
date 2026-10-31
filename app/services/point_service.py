
from pathlib import Path
from app.model import Point
from app.repository import PointRepository
from app.core import Result, ErrorCode
from app.utils import Folder
from app.utils import Tool_OpenCv2
import numpy as np
from app.config import (BASE_DIR,PATH_FOLDER_IMG_COORDINATE_PRODUCT,PATH_FOLDER_IMG_COORDINATE_OUTPUT,PATH_FOLDER_MODEL_DETECT_PATCH_CORE)
    
class PointService:
    def __init__(self, repository: PointRepository):
        self.repository = repository
        self.path_base_patch_core = PATH_FOLDER_MODEL_DETECT_PATCH_CORE
        self.path_base_img_coordinates = PATH_FOLDER_IMG_COORDINATE_PRODUCT
        self.path_base_img_coordinates_output = PATH_FOLDER_IMG_COORDINATE_OUTPUT
        self.path_base_storage = BASE_DIR
        self.points = self._load_points()

    def _load_points(self) -> dict:
        """
        Chức năng: Tải toàn bộ dữ liệu điểm từ repository vào bộ nhớ RAM.
        Input: None
        Output: dict -> Cấu trúc bộ nhớ dạng phân cấp {product_id: {frame_id: {point_id: Point}}}
        """
        raw_data = self.repository.load_points()
        points = {}
        if not isinstance(raw_data, dict): return {}

        for product_id, frame_dict in raw_data.items():
            product_id = int(product_id)
            points[product_id] = {}
            if not isinstance(frame_dict, dict): continue

            for frame_id, point_dict in frame_dict.items():
                frame_id = int(frame_id)
                points[product_id][frame_id] = {}
                if not isinstance(point_dict, dict): continue

                for point_id, item in point_dict.items():
                    point_id = int(point_id)
                    point = Point(
                        point_id=point_id,
                        x=item.get("x", 0), y=item.get("y", 0), z=item.get("z", 0),
                        rx=item.get("rx", 180.0), ry=item.get("ry", 0.0), rz=item.get("rz", 0.0),
                        path_model_patch_core=item.get("path_model_patch_core"),
                        path_img_point=item.get("path_img_point"),
                        path_img_retrain=item.get("path_img_retrain"),
                        arr_polygon=self._normalize_polygon(item.get("arr_polygon", []))
                    )
                    points[product_id][frame_id][point_id] = point
        return points

    def is_exists_product_face_point_id(self, product_id: int, face_id: int, point_id: int) -> bool:
        if product_id not in self.points: return False
        if face_id not in self.points[product_id]: return False
        return point_id in self.points[product_id][face_id]

    is_exists_product_frame_point_id = is_exists_product_face_point_id

    def _legacy_is_exists_product_frame_point_id(self, product_id: int, frame_id: int, point_id: int) -> bool:
        """
        Chức năng: Kiểm tra sự tồn tại của bộ ba định danh Product, Frame và Point.
        Input: product_id (int), frame_id (int), point_id (int)
        Output: bool -> True nếu tồn tại, ngược lại False
        """
        if product_id not in self.points: return False
        if frame_id not in self.points[product_id]: return False
        return point_id in self.points[product_id][frame_id]

    def _save_points(self) -> None:
        """
        Chức năng: Đồng bộ và lưu toàn bộ dữ liệu từ RAM xuống database hoặc file lưu trữ.
        Input: None
        Output: None
        """
        data = {}
        for product_id, frame_dict in self.points.items():
            data[str(product_id)] = {}
            for frame_id, point_dict in frame_dict.items():
                data[str(product_id)][str(frame_id)] = {}
                for point_id, point in point_dict.items():
                    data[str(product_id)][str(frame_id)][str(point_id)] = point.to_dict()
        self.repository.save_points(data)

    def _generate_point_id(self) -> int:
        """
        Chức năng: Tự động tạo mã định danh Point ID mới dựa trên ID lớn nhất hiện tại.
        Input: None
        Output: int -> Mã point_id tiếp theo (Max ID + 1)
        """
        max_id = 0
        for frame_dict in self.points.values():
            for point_dict in frame_dict.values():
                for point_id in point_dict.keys():
                    if point_id > max_id: max_id = point_id
        return max_id + 1

    def _normalize_polygon(self, arr_polygon) -> list:
        """
        Chức năng: Chuẩn hóa dữ liệu mảng vùng đa giác về dạng danh sách các tuple tọa độ cố định.
        Input: arr_polygon (list/array)
        Output: list[list[tuple]] -> Mảng đa giác đã chuẩn hóa phần tử sang tuple
        """
        output = []
        for polygon in arr_polygon:
            arr_point = []
            for point in polygon:
                arr_point.append(tuple(point))
            output.append(arr_point)
        return output

    def get_points_by_product_id_obj_point(self, product_id: int) -> Result:
        """
        Chức năng: Lấy danh sách gốc dạng đối tượng Point của Product để xử lý trực tiếp trên RAM.
        Input: product_id (int)
        Output: Result.Ok(dict) -> Dictionary chứa các Point object của sản phẩm
        """
        return Result.Ok(self.points.get(product_id, {}))
    
    def get_path_img_point(self, product_id: int, frame_id: int, point_id: int) -> Result:
        """
        Chức năng: Lấy đường dẫn tuyệt đối của ảnh gốc của một Point.
        Input: product_id (int), frame_id (int), point_id (int)
        Output: Result.Ok(Path) nếu tìm thấy, ngược lại Result.Fail(...)
        """
        result = self.get_point_by_id(product_id, frame_id, point_id)
        if not result.ok:
            return Result.Fail(ErrorCode.POINT_NOT_FOUND)

        point: Point = result.data
        if point.path_img_point is None:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND)
        full_path = Path(self.path_base_storage) / point.path_img_point
        if not full_path.exists():
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND)
        return Result.Ok(full_path)
    
    def get_points_by_product_id(self, product_id: int) -> Result:
        """
        Chức năng: Lấy danh sách thông tin cấu trúc điểm của sản phẩm dưới dạng dictionary thuần (đã to_dict).
        Input: product_id (int)
        Output: Result.Ok(dict) nếu thấy sản phẩm, ngược lại Result.Fail(PRODUCT_NOT_FOUND)
        """
        product = self.points.get(product_id)
        if not product: return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        
        data = {}
        for frame_id, frame_dict in product.items():
            data[str(frame_id)] = {}
            for point_id, point in frame_dict.items():
                data[str(frame_id)][str(point_id)] = point.to_dict()
        return Result.Ok(data)

    def get_points_by_face_id(self, product_id: int, face_id: int) -> Result:
        point_dict = self.points.get(product_id, {}).get(face_id, {})
        return Result.Ok(point_dict)

    get_points_by_frame_id = get_points_by_face_id

    def _legacy_get_points_by_frame_id(self, product_id: int, frame_id: int) -> Result:
        """
        Chức năng: Lấy bản đồ các điểm thuộc về một Frame cụ thể của sản phẩm.
        Input: product_id (int), frame_id (int)
        Output: Result.Ok(dict) -> Dictionary các điểm thuộc frame yêu cầu
        """
        point_dict = self.points.get(product_id, {}).get(frame_id, {})
        return Result.Ok(point_dict)

    def get_point_by_id(self, product_id: int, frame_id: int, point_id: int) -> Result:
        """
        Chức năng: Lấy thông tin chi tiết của một điểm cụ thể dựa trên ID.
        Input: product_id (int), frame_id (int), point_id (int)
        Output: Result.Ok(Point) nếu tìm thấy, ngược lại Result.Fail(POINT_NOT_FOUND)
        """
        point = self.points.get(product_id, {}).get(frame_id, {}).get(point_id)
        if point is None: return Result.Fail(ErrorCode.POINT_NOT_FOUND)
        return Result.Ok(point)

    def add_point(self, product_id: int, frame_id: int, point: Point, img: np.ndarray) -> Result:
        """
        Chức năng: Kiểm tra hợp lệ dữ liệu đầu vào, lưu ảnh mẫu Point và tạo mới điểm trong RAM/repository.
        Input: product_id (int/str), frame_id (int/str), point (Point), img (np.ndarray)
        Output: Result.Ok(Point) khi thêm mới thành công, hoặc Result.Fail kèm mã lỗi tương ứng
        """
        if not isinstance(product_id, int):
            if isinstance(product_id, str):
                try: product_id = int(product_id)
                except Exception: return Result.Fail(ErrorCode.PRODUCT_ID_INVALID)
            else: return Result.Fail(ErrorCode.PRODUCT_ID_INVALID)
            
        if not isinstance(frame_id, int):
            if isinstance(frame_id, str):
                try: frame_id = int(frame_id)
                except Exception: return Result.Fail(ErrorCode.FRAME_ID_INVALID)
            else: return Result.Fail(ErrorCode.FRAME_ID_INVALID)
            
        if not isinstance(point.x, int):
            if isinstance(point.x, str):
                try: point.x = int(point.x)
                except Exception: return Result.Fail(ErrorCode.POINT_X_INVALID)
            else: return Result.Fail(ErrorCode.POINT_X_INVALID)
            
        if not isinstance(point.y, int):
            if isinstance(point.y, str):
                try: point.y = int(point.y)
                except Exception: return Result.Fail(ErrorCode.POINT_Y_INVALID)
            else: return Result.Fail(ErrorCode.POINT_Y_INVALID)
            
        if not isinstance(point.z, int):
            if isinstance(point.z, str):
                try: point.z = int(point.z)
                except Exception: return Result.Fail(ErrorCode.POINT_Z_INVALID)
            else: return Result.Fail(ErrorCode.POINT_Z_INVALID)
            
        if img is None or img.size == 0: return Result.Fail(ErrorCode.IMAGE_INVALID)
        if product_id not in self.points: self.points[product_id] = {}
        if frame_id not in self.points[product_id]: self.points[product_id][frame_id] = {}
        
        if point.point_id is None: point.point_id = self._generate_point_id()
        if point.point_id in self.points[product_id][frame_id]: return Result.Fail(ErrorCode.POINT_ALREADY_EXISTS)
        
        product_id_str, frame_id_str, point_id_str = str(product_id), str(frame_id), str(point.point_id)
        path_img_coordinate = Path(self.path_base_img_coordinates) / product_id_str / frame_id_str / f"{point_id_str}.jpg"

        path_img_coordinate.parent.mkdir(parents=True, exist_ok=True)
        
        Tool_OpenCv2.save_image(img, path_img_coordinate)
        point.path_model_patch_core = None
        point.path_img_point = Folder.get_parts_from_bottom(path_img_coordinate, 5)
        point.path_img_retrain = None
        
        self.points[product_id][frame_id][point.point_id] = point
        self._save_points()
        return Result.Ok(point)

    def attach_patchcore_paths(self, product_id: int, frame_id: int, point_id: int) -> Result:
        """
        Chức năng: Gắn đường dẫn PatchCore vào Point khi item thực sự tham gia workflow AnomalyPoint/ForeignObject.
        Input: product_id (int), frame_id (int), point_id (int).
        Output: Result.Ok(Point) khi cập nhật thành công, hoặc Result.Fail(POINT_NOT_FOUND).
        Errors: POINT_NOT_FOUND khi bộ ba định danh không tồn tại trong RAM.
        """
        result_find = self.get_point_by_id(product_id, frame_id, point_id)
        if not result_find.ok:
            return Result.Fail(ErrorCode.POINT_NOT_FOUND)

        point: Point = result_find.data
        product_id_str = str(product_id)
        frame_id_str = str(frame_id)
        point_id_str = str(point_id)
        path_model_folder = Path(self.path_base_patch_core) / product_id_str / frame_id_str / point_id_str
        path_img_retrain_folder = Path(self.path_base_img_coordinates_output) / product_id_str / frame_id_str / point_id_str
        point.path_model_patch_core = Folder.get_parts_from_bottom(path_model_folder, 6)
        point.path_img_retrain = Folder.get_parts_from_bottom(path_img_retrain_folder, 6)
        self._save_points()
        return Result.Ok(point)

    def update_point(self, product_id: int, frame_id: int, point_id: int, x, y, z, img, rx=None, ry=None, rz=None) -> Result:
        """
        Chức năng: Cập nhật các tọa độ X, Y, Z vật lý và/hoặc thay thế tập tin hình ảnh mẫu mới cho điểm.
        Input: product_id (int), frame_id (int), point_id (int), x (int/None), y (int/None), z (int/None), img (np.ndarray/None)
        Output: Result.Ok(Point) khi cập nhật thành công, ngược lại Result.Fail(POINT_NOT_FOUND/IMAGE_INVALID)
        """
        result_find = self.get_point_by_id(product_id, frame_id, point_id)
        if not result_find.ok: return Result.Fail(ErrorCode.POINT_NOT_FOUND)
        point: Point = result_find.data
        
        if x is not None: point.x = x
        if y is not None: point.y = y
        if z is not None: point.z = z
        if rx is not None: point.rx = rx
        if ry is not None: point.ry = ry
        if rz is not None: point.rz = rz
        
        if img is not None:
            if img.size == 0: return Result.Fail(ErrorCode.IMAGE_INVALID)
            full_path = Path(self.path_base_img_coordinates) / str(product_id) / str(frame_id) / f"{str(point_id)}.jpg"
            if full_path.exists(): full_path.unlink()
            full_path.parent.mkdir(parents=True, exist_ok=True)
            Tool_OpenCv2.save_image(img, full_path)
            point.path_img_point = Folder.get_parts_from_bottom(full_path, 5)
            
        self._save_points()
        return Result.Ok(point)

    def update_point_polygon(self, product_id: int, frame_id: int, point_id: int, arr_polygon) -> Result:
        """
        Chức năng: Cập nhật hoặc vẽ lại vùng đa giác (Polygon quy định kiểm tra) của điểm.
        Input: product_id (int), frame_id (int), point_id (int), arr_polygon (list)
        Output: Result.Ok(Point) hoặc Result.Fail(POINT_NOT_FOUND)
        """
        result_find = self.get_point_by_id(product_id, frame_id, point_id)
        if not result_find.ok: return Result.Fail(ErrorCode.POINT_NOT_FOUND)
        
        point: Point = result_find.data
        point.arr_polygon = self._normalize_polygon(arr_polygon)
        self._save_points()
        return Result.Ok(point)

    def delete_point(self, product_id: int, frame_id: int, point_id: int) -> Result:
        """
        Chức năng: Xóa sạch các tài nguyên vật lý liên quan đến điểm trên ổ cứng và loại bỏ điểm khỏi cấu trúc RAM.
        Input: product_id (int), frame_id (int), point_id (int)
        Output: Result.Ok(Point) trả về đối tượng vừa xóa, hoặc Result.Fail(POINT_NOT_FOUND)
        """
        point_delete = self.points.get(product_id, {}).get(frame_id, {}).get(point_id)
        if point_delete is None: return Result.Fail(ErrorCode.POINT_NOT_FOUND)
        
        if point_delete.path_img_point:
            full_path_img = Path(self.path_base_storage) / point_delete.path_img_point
            if full_path_img.exists(): Folder.delete_file(full_path_img)
        if point_delete.path_model_patch_core:
            full_path_model = Path(self.path_base_storage) / point_delete.path_model_patch_core
            if full_path_model.exists(): Folder.delete_folder(full_path_model)
        if point_delete.path_img_retrain:
            full_path_retrain = Path(self.path_base_storage) / point_delete.path_img_retrain
            if full_path_retrain.exists(): Folder.delete_folder(full_path_retrain)
            
        del self.points[product_id][frame_id][point_id]
        if not self.points[product_id][frame_id]: del self.points[product_id][frame_id]
        if not self.points[product_id]: del self.points[product_id]
        
        self._save_points()
        return Result.Ok(point_delete)

    def delete_face(self, product_id: int, face_id: int) -> Result:
        return self.delete_frame(product_id, face_id)

    def delete_frame(self, product_id: int, frame_id: int) -> Result:
        """
        Chức năng: Xóa toàn bộ các thư mục lưu trữ (models, ảnh tọa độ, ảnh retrain) thuộc về một Frame và dọn dẹp RAM.
        Input: product_id (int), frame_id (int)
        Output: Result.Ok(int) mã frame_id vừa xóa thành công, hoặc Result.Fail mã lỗi tương ứng
        """
        product_id, frame_id = int(product_id), int(frame_id)
        product = self.points.get(product_id)
        if not product: return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        frame = product.get(frame_id)
        if not frame: return Result.Fail(ErrorCode.FRAME_NOT_FOUND)
        
        product_id_str, frame_id_str = str(product_id), str(frame_id)
        path_model_folder = Path(self.path_base_patch_core) / product_id_str / frame_id_str
        if path_model_folder.exists(): Folder.delete_folder(path_model_folder)
        
        path_img_folder = Path(self.path_base_img_coordinates) / product_id_str / frame_id_str
        if path_img_folder.exists(): Folder.delete_folder(path_img_folder)
        
        path_retrain_folder = Path(self.path_base_img_coordinates_output) / product_id_str / frame_id_str
        if path_retrain_folder.exists(): Folder.delete_folder(path_retrain_folder)
        
        del self.points[product_id][frame_id]
        if not self.points[product_id]: del self.points[product_id]
        
        self._save_points()
        return Result.Ok(frame_id)

    def delete_product(self, product_id: int) -> Result:
        """
        Chức năng: Xóa toàn bộ dữ liệu frame và point của sản phẩm khỏi bộ nhớ RAM và lưu lại file points.json.
        Input: product_id (int)
        Output: Result.Ok(bool) True nếu đã xóa, ngược lại Result.Fail nếu ID không hợp lệ.
        """
        try:
            product_id = int(product_id)
        except (ValueError, TypeError):
            return Result.Fail(ErrorCode.PRODUCT_ID_INVALID)

        if product_id in self.points:
            del self.points[product_id]
            self._save_points()
            return Result.Ok(True)
        return Result.Ok(False)

    def reload_points(self) -> None:
        """
        Chức năng: Tải lại toàn bộ dữ liệu điểm từ file points.json vào bộ nhớ RAM.
        Input: None
        Output: None
        """
        self.points = self._load_points()

    def get_xyz_by_product_face(self, product_id: int, face_id: int) -> Result:
        if product_id not in self.points: return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        if face_id not in self.points[product_id]: return Result.Fail(ErrorCode.FACE_NOT_FOUND)
        frame_dict = self.points[product_id][face_id]
        data = {}
        for point_id, point in frame_dict.items():
            data[point_id] = {
                "x": point.x, "y": point.y, "z": point.z,
                "rx": getattr(point, "rx", 180.0),
                "ry": getattr(point, "ry", 0.0),
                "rz": getattr(point, "rz", 0.0)
            }
        return Result.Ok(data)

    get_xyz_by_product_frame = get_xyz_by_product_face

    def _legacy_get_xyz_by_product_frame(self, product_id: int, frame_id: int) -> Result:
        """
        Chức năng: Truy xuất nhanh bản đồ tọa độ không gian (x, y, z, rx, ry, rz) của mọi điểm có trong Frame chỉ định.
        Input: product_id (int), frame_id (int)
        Output: Result.Ok(dict) map tọa độ theo point_id, hoặc Result.Fail nếu sai thông tin định danh
        """
        if product_id not in self.points: return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        if frame_id not in self.points[product_id]: return Result.Fail(ErrorCode.FRAME_NOT_FOUND)
        
        frame_dict = self.points[product_id][frame_id]
        data = {}
        for point_id, point in frame_dict.items():
            data[point_id] = {
                "x": point.x, "y": point.y, "z": point.z,
                "rx": getattr(point, "rx", 180.0),
                "ry": getattr(point, "ry", 0.0),
                "rz": getattr(point, "rz", 0.0)
            }
        return Result.Ok(data)

    def get_all_xyz_by_product_id(self, product_id: int) -> Result:
        """
        Chức năng: Thu thập tất cả bộ dữ liệu tọa độ không gian thuộc mọi Frame của sản phẩm.
        Input: product_id (int)
        Output: Result.Ok(dict) danh sách tọa độ gom cụm theo từng frame_id, hoặc Result.Fail(PRODUCT_NOT_FOUND)
        """
        product = self.points.get(product_id)
        if product is None: return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        
        data = {}
        for frame_id, frame_dict in product.items():
            data[frame_id] = []
            for point_id, point in frame_dict.items():
                data[frame_id].append({
                    "point_id": point_id,
                    "x": point.x, "y": point.y, "z": point.z,
                    "rx": getattr(point, "rx", 180.0),
                    "ry": getattr(point, "ry", 0.0),
                    "rz": getattr(point, "rz", 0.0)
                })
        return Result.Ok(data)

    def get_all_retrain_paths_by_product_id(self, product_id: int) -> Result:
        """
        Chức năng: Trích xuất toàn bộ danh sách các đường dẫn tương đối lưu ảnh retrain của sản phẩm.
        Input: product_id (int)
        Output: Result.Ok(list[str]) mảng các đường dẫn ảnh retrain tìm thấy, hoặc Result.Fail(PRODUCT_NOT_FOUND)
        """
        product = self.points.get(product_id)
        if product is None: return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        
        paths = []
        for frame_dict in product.values():
            for point in frame_dict.values():
                if point.path_img_retrain: paths.append(point.path_img_retrain)
        return Result.Ok(paths)

    def get_retrain_paths_by_product_face(self, product_id: int, face_id: int) -> Result:
        product = self.points.get(product_id)
        if product is None: return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        face = product.get(face_id)
        if face is None: return Result.Fail(ErrorCode.FACE_NOT_FOUND)
        
        paths = []
        for point in face.values():
            if not point.path_img_retrain: continue
            full_path = Path(self.path_base_storage) / point.path_img_retrain
            paths.append(str(full_path))
        return Result.Ok(paths)

    get_retrain_paths_by_product_frame = get_retrain_paths_by_product_face

    def _legacy_get_retrain_paths_by_product_frame(self, product_id: int, frame_id: int) -> Result:
        """
        Chức năng: Xây dựng danh sách các đường dẫn vật lý tuyệt đối đến thư mục chứa ảnh phục vụ retrain của một Frame.
        Input: product_id (int), frame_id (int)
        Output: Result.Ok(list[str]) tập hợp các đường dẫn thư mục tuyệt đối, hoặc Result.Fail tương ứng
        """
        product = self.points.get(product_id)
        if product is None: return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        frame = product.get(frame_id)
        if frame is None: return Result.Fail(ErrorCode.FRAME_NOT_FOUND)
        
        paths = []
        for point in frame.values():
            if not point.path_img_retrain: continue
            full_path = Path(self.path_base_storage) / point.path_img_retrain
            paths.append(str(full_path))
        return Result.Ok(paths)


    def get_product_face_id_tree(self) -> Result:
        id_tree = {}
        for product_id, frame_dict in self.points.items():
            product_id_str = str(product_id)
            id_tree[product_id_str] = {}
            for face_id in frame_dict.keys():
                face_id_str = str(face_id)
                id_tree[product_id_str][face_id_str] = {}
        return id_tree

    get_product_frame_id_tree = get_product_face_id_tree

    def _legacy_get_product_frame_id_tree(self) -> Result:
        """
        Chức năng: Lấy cây định danh dừng lại ở cấp Frame ID (Product ID -> Frame ID).
        Input: None
        Output: Result.Ok(dict) -> Cấu trúc dạng chuỗi: {"product_id": {"frame_id": {}}}
        """
        id_tree = {}
        for product_id, frame_dict in self.points.items():
            product_id_str = str(product_id)
            id_tree[product_id_str] = {}
            for frame_id in frame_dict.keys():
                frame_id_str = str(frame_id)
                # Dừng lại ở đây, tạo dictionary rỗng cho frame_id
                id_tree[product_id_str][frame_id_str] = {}
        return id_tree
    

    def get_point_tree_by_product_id(self, product_id: int) -> Result:
            """
            Chức năng: Lấy cây cấu trúc 3 cấp gồm Product ID -> Frame ID -> Point ID (để rỗng).
            Input: product_id (int/str)
            Output: Result.Ok(dict) -> Cấu trúc dạng chuỗi: {"product_id": {"frame_id": {"point_id": {}}}}
                    hoặc Result.Fail nếu không tìm thấy sản phẩm.
            """
            # Tự ép kiểu và kiểm tra tính hợp lệ không qua hàm helper _parse_id
            if not isinstance(product_id, int):
                if isinstance(product_id, str):
                    try: 
                        product_id = int(product_id)
                    except Exception: 
                        return Result.Fail(ErrorCode.PRODUCT_ID_INVALID)
                else: 
                    return Result.Fail(ErrorCode.PRODUCT_ID_INVALID)

            # Kiểm tra xem sản phẩm có tồn tại trong bộ nhớ RAM không
            product = self.points.get(product_id)
            if not product:
                return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)

            # Dựng cấu trúc cây
            id_tree = {
                str(product_id): {
                    str(frame_id): {
                        str(point_id): {}
                        for point_id in point_dict.keys()
                    }
                    for frame_id, point_dict in product.items()
                }
            }
            
            return Result.Ok(id_tree)
    
    def is_exists_product_face(self, product_id: int, face_id: int) -> Result:
        if not isinstance(product_id, int):
            if isinstance(product_id, str):
                try: product_id = int(product_id)
                except Exception: return Result.Fail(ErrorCode.PRODUCT_ID_INVALID)
            else: return Result.Fail(ErrorCode.PRODUCT_ID_INVALID)
            
        if not isinstance(face_id, int):
            if isinstance(face_id, str):
                try: face_id = int(face_id)
                except Exception: return Result.Fail(ErrorCode.FACE_ID_INVALID)
            else: return Result.Fail(ErrorCode.FACE_ID_INVALID)
        if product_id not in self.points: 
            return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        if face_id not in self.points[product_id]: 
            return Result.Fail(ErrorCode.FACE_NOT_FOUND)
        return Result.Ok(True)

    is_exists_product_frame = is_exists_product_face

    def _legacy_is_exists_product_frame(self, product_id: int, frame_id: int) -> Result:
        """
        Chức năng: Kiểm tra cặp định danh Product ID và Frame ID hiện tại có đang tồn tại không.
        Input: product_id (int), frame_id (int)
        Output: Result.Ok(bool) True nếu tồn tại cặp ID, ngược lại Result.Fail kèm mã lỗi tương ứng
        """
        # 1. Kiểm tra ép kiểu dữ liệu đầu vào nếu là chuỗi (tương tự logic hàm add_point)
        if not isinstance(product_id, int):
            if isinstance(product_id, str):
                try: product_id = int(product_id)
                except Exception: return Result.Fail(ErrorCode.PRODUCT_ID_INVALID)
            else: return Result.Fail(ErrorCode.PRODUCT_ID_INVALID)
            
        if not isinstance(frame_id, int):
            if isinstance(frame_id, str):
                try: frame_id = int(frame_id)
                except Exception: return Result.Fail(ErrorCode.FRAME_ID_INVALID)
            else: return Result.Fail(ErrorCode.FRAME_ID_INVALID)
        # 2. Kiểm tra sự tồn tại trong bộ nhớ RAM self.points
        if product_id not in self.points: 
            return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        if frame_id not in self.points[product_id]: 
            return Result.Fail(ErrorCode.FRAME_NOT_FOUND)
        return Result.Ok(True)