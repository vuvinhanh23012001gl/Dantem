from app.core import Result, ErrorCode
from app.repository import JudmentLawProductRepository
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordRepository,
)
from app.config import (
    PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST,
    PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST,
    PATH_FOLDER_MODEL_DETECT_PATCH_CORE,
    PATH_FOLDER_IMG_COORDINATE_OUTPUT,
)
from pathlib import Path
from app.config.path_config import WORKSPACE_DIR
import logging
import shutil
import copy
import cv2
logger = logging.getLogger(__name__)
class JudmentLawProductSevice:
    def __init__(self,repo:JudmentLawProductRepository):
        self.repo =  repo

    def save_data(self,data:dict,data_frame:dict):
        if self.compare_structure(data=data,data_frame=data_frame):
            print("So sánh thuộc cấu trúc cây tiến hành lưu")
            cleaned_data = copy.deepcopy(data)
            for prod_id, frames in cleaned_data.items():
                if not isinstance(frames, dict):
                    continue
                for frame_id, items in frames.items():
                    if not isinstance(items, dict):
                        continue
                    for item_id, inspectors in items.items():
                        if not isinstance(inspectors, dict):
                            continue
                        legacy_anomaly_config = inspectors.pop("EndChippingInspector", None)
                        if (
                            "AnomalyPointInspector" not in inspectors
                            and legacy_anomaly_config is not None
                        ):
                            inspectors["AnomalyPointInspector"] = legacy_anomaly_config
                        removed = {"MembraneInspector", "ScratchedPipeItemInspector", "AirBubblesItemInspector"}.intersection(inspectors)
                        if removed:
                            message = f"Hạng mục đã gỡ, cần chuyển đổi master: {', '.join(sorted(removed))}"
                            logger.warning(message)
                            return Result.Fail(message)
            try:
                self.repo.update_data(cleaned_data,False)
            except OSError:
                logger.exception("Không lưu được cấu hình master")
                return Result.Fail("Không lưu được master; chưa dọn dữ liệu model.")
            try:
                self._cleanup_orphaned_anomaly_point_rois(cleaned_data)
                self._cleanup_orphaned_foreign_object_rois(cleaned_data)
            except OSError:
                logger.exception("Đã lưu master nhưng không dọn hết model mồ côi")
                return Result.Fail("Đã lưu master nhưng không dọn hết model mồ côi; kiểm tra nhật ký.")
            return Result.Ok()
        else:
            return Result.Fail(ErrorCode.DATA_IS_NOT_CORRECT_FROMAT)
            
    def delete_product_data(self, product_id: str) -> Result:
        """Xóa dữ liệu master của product trong law và PatchCore.

        Input: ``product_id`` là ID sản phẩm cần reset dữ liệu master.
        Output: ``Result.Ok`` khi đã dọn xong, kể cả khi sản phẩm đã rỗng.
        Errors: Kết quả thất bại chứa báo cáo nếu không xóa hết dữ liệu.
        """
        product_key = str(product_id)
        if not product_key.isdecimal():
            return Result.Fail(ErrorCode.INVALID_INPUT)
        report = {
            "product_id": product_key,
            "law_deleted": False,
            "patchcore": {
                "deleted_paths": [],
                "deleted_manifest_records": {},
                "errors": [],
            },
        }

        try:
            report["law_deleted"] = bool(self.repo.delete_product(product_key))
        except OSError:
            logger.exception("Không xóa được luật master của sản phẩm %s", product_key)
            return Result.Fail("Không xóa được luật master; RAM được giữ nguyên.")
        self._cleanup_patchcore_product(product_key, report)
        has_errors = bool(report["patchcore"]["errors"])
        if has_errors:
            logger.error("Tẩy master chưa hoàn tất: %s", report)
            return Result(
                False, data=report,
                error="Backend đã xóa một phần nhưng chưa dọn hết model: " + "; ".join(report["patchcore"]["errors"]),
            )
        return Result.Ok(report)

    @staticmethod
    def _cleanup_patchcore_product(product_id: str, report: dict) -> None:
        """Dọn thư mục model/output PatchCore và manifest của một product.

        Input: ``product_id`` và ``report`` để ghi nhận thao tác dọn dẹp.
        Output: Không trả về; kết quả được ghi vào ``report['patchcore']``.
        Errors: Không ném lỗi; lỗi file hệ thống được append vào ``errors``.
        """
        patch_report = report["patchcore"]
        target_paths = [
            Path(PATH_FOLDER_MODEL_DETECT_PATCH_CORE) / product_id,
            Path(PATH_FOLDER_IMG_COORDINATE_OUTPUT) / product_id,
        ]
        for path in target_paths:
            try:
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    patch_report["deleted_paths"].append(str(path).replace("\\", "/"))
            except OSError as error:
                patch_report["errors"].append(f"{path}: {error}")

        manifest_paths = {
            "anomaly_point": Path(PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST),
            "foreign_object": Path(PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST),
        }
        for key, manifest_path in manifest_paths.items():
            try:
                repo = PatchCoreTrainRecordRepository(manifest_path=manifest_path)
                deleted_count = repo.delete_records_by_product_id(product_id)
                patch_report["deleted_manifest_records"][key] = int(deleted_count)
            except OSError as error:
                patch_report["errors"].append(f"{manifest_path}: {error}")

    @staticmethod
    def _cleanup_orphaned_anomaly_point_rois(cleaned_data: dict) -> None:
        JudmentLawProductSevice._cleanup_orphaned_patchcore_rois(
            cleaned_data, "AnomalyPointInspector", "anomaly_point",
            PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST,
        )

    @staticmethod
    def _cleanup_orphaned_foreign_object_rois(cleaned_data: dict) -> None:
        JudmentLawProductSevice._cleanup_orphaned_patchcore_rois(
            cleaned_data, "ForeignObjectInspector", "foreign",
            PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST,
        )

    @staticmethod
    def _cleanup_orphaned_patchcore_rois(
        cleaned_data: dict, inspector_name: str, roi_name: str, manifest_path: str | Path,
    ) -> None:
        """Chỉ dọn session đúng loại, không xóa cả thư mục ROI dùng chung."""
        if not isinstance(cleaned_data, dict):
            return
        repo = PatchCoreTrainRecordRepository(manifest_path=manifest_path)
        base_patchcore = Path(PATH_FOLDER_MODEL_DETECT_PATCH_CORE)
        for prod_id, frames in cleaned_data.items():
            if not isinstance(frames, dict):
                continue
            for frame_id, items in frames.items():
                if not isinstance(items, dict):
                    continue
                for item_id, inspectors in items.items():
                    item_dir = base_patchcore / str(prod_id) / str(frame_id) / str(item_id)
                    config = inspectors.get(inspector_name) if isinstance(inspectors, dict) else None
                    active_roi_dirs = set()
                    if isinstance(config, dict):
                        if {"xStart", "yStart", "xEnd", "yEnd"}.issubset(config):
                            active_roi_dirs.add("roi_0")
                        else:
                            for key, region in config.items():
                                if isinstance(region, dict):
                                    roi_id = region.get("id", key)
                                    active_roi_dirs.add(f"roi_{roi_id}")
                    for child in list(item_dir.iterdir()) if item_dir.is_dir() else []:
                        if child.is_dir() and child.name.startswith("roi_") and child.name not in active_roi_dirs:
                            for session in child.glob(f"model_{roi_name}_crop_*"):
                                if session.is_dir():
                                    shutil.rmtree(session)
                                    repo.delete_records_under_dir(session)
                            if not any(child.iterdir()):
                                child.rmdir()
                    if roi_name == "foreign" and "roi_0" not in active_roi_dirs:
                        for session in item_dir.glob("model_foreign_crop_*"):
                            if session.is_dir():
                                shutil.rmtree(session)
                                repo.delete_records_under_dir(session)
                    for record in repo.load_manifest():
                        raw_path = record.get("model_root")
                        if not raw_path:
                            continue
                        session = Path(raw_path)
                        if not session.is_absolute():
                            session = WORKSPACE_DIR / session
                        session = session.resolve()
                        if not session.name.startswith(f"model_{roi_name}_crop_"):
                            continue
                        parent = session.parent
                        removed_roi = (
                            parent.parent == item_dir.resolve()
                            and parent.name.startswith("roi_") and parent.name not in active_roi_dirs
                        )
                        removed_legacy = (
                            roi_name == "foreign" and parent == item_dir.resolve()
                            and "roi_0" not in active_roi_dirs
                        )
                        if removed_roi or removed_legacy:
                            repo.delete_records_under_dir(session)



    def convert_canvas_coordinates(
        self,
        data: dict,
        product_id: int,
        point_service,
        canvas_width: int,
        canvas_height: int,
    ) -> Result:
        """Chuyển tọa độ mọi inspector từ canvas sang pixel ảnh master.

        Input: ``data`` là cây judgment từ client; ``product_id`` là sản phẩm
            hiện tại; ``point_service`` dùng để lấy ảnh master; canvas có kích
            thước ``canvas_width`` x ``canvas_height``.
        Output: ``Result.Ok`` chứa bản sao dữ liệu đã chuyển đổi và đánh dấu
            ``coordinateSpace: image`` cho các inspector có tọa độ.
        Errors: ``Result.Fail`` nếu canvas không hợp lệ, thiếu ảnh master hoặc
            dữ liệu inspector hoặc tọa độ không đúng cấu trúc.
        """
        if canvas_width <= 0 or canvas_height <= 0:
            return Result.Fail(ErrorCode.INVALID_INPUT)
        converted = copy.deepcopy(data)
        product_data = converted.get(str(product_id), converted.get(product_id))
        if not isinstance(product_data, dict):
            return Result.Fail(ErrorCode.DATA_INVALID)
        for frame_id, frame_data in product_data.items():
            if not isinstance(frame_data, dict):
                continue
            for point_id, item_data in frame_data.items():
                if not isinstance(item_data, dict):
                    continue
                # Nếu điểm này không có inspector nào cấu hình (dict rỗng), bỏ qua để tránh nghẽn I/O đọc ảnh
                if not item_data:
                    continue
                try:
                    f_id_int = int(frame_id)
                    p_id_int = int(point_id)
                    prod_id_int = int(product_id)
                except (ValueError, TypeError):
                    continue
                image_result = point_service.get_path_img_point(
                    prod_id_int, f_id_int, p_id_int
                )
                if not image_result.ok:
                    return Result.Fail(ErrorCode.IMAGE_NOT_FOUND)
                image = cv2.imread(str(image_result.data))
                if image is None:
                    return Result.Fail(ErrorCode.IMAGE_NOT_FOUND)
                image_height, image_width = image.shape[:2]
                scale_x = image_width / canvas_width
                scale_y = image_height / canvas_height
                for inspector in item_data.values():
                    if not isinstance(inspector, dict):
                        continue
                    coordinate_items = (
                        inspector.values()
                        if self._is_collection_inspector(inspector)
                        else (inspector,)
                    )
                    for coordinate_item in coordinate_items:
                        if not isinstance(coordinate_item, dict):
                            continue
                        if coordinate_item.get("coordinateSpace") == "image":
                            continue
                        if not all(
                            key in coordinate_item
                            for key in ("xStart", "yStart", "xEnd", "yEnd")
                        ):
                            continue
                        try:
                            coordinate_item["xStart"] = int(
                                round(float(coordinate_item["xStart"]) * scale_x)
                            )
                            coordinate_item["yStart"] = int(
                                round(float(coordinate_item["yStart"]) * scale_y)
                            )
                            coordinate_item["xEnd"] = int(
                                round(float(coordinate_item["xEnd"]) * scale_x)
                            )
                            coordinate_item["yEnd"] = int(
                                round(float(coordinate_item["yEnd"]) * scale_y)
                            )
                        except (TypeError, ValueError):
                            return Result.Fail(ErrorCode.DATA_INVALID)
                        coordinate_item["coordinateSpace"] = "image"
        return Result.Ok(converted)

    def convert_canvas_border_coordinates(
        self,
        data: dict,
        product_id: int,
        point_service,
        canvas_width: int,
        canvas_height: int,
    ) -> Result:
        """Tên tương thích cũ của ``convert_canvas_coordinates``.

        Input, output và lỗi: Giống ``convert_canvas_coordinates``.
        """
        return self.convert_canvas_coordinates(
            data,
            product_id,
            point_service,
            canvas_width,
            canvas_height,
        )

    @staticmethod
    def _is_collection_inspector(inspector: dict) -> bool:
        """Xác định inspector chứa nhiều line/rectangle con.

        Input: Dict cấu hình của một inspector.
        Output: ``True`` nếu các value là các dict tọa độ con.
        Errors: Không phát sinh.
        """
        coordinate_keys = {"xStart", "yStart", "xEnd", "yEnd"}
        return not coordinate_keys.issubset(inspector)

    def get_product_data(self, product_id: str) -> Result:
            """Lấy toàn bộ dữ liệu của một Product dựa trên product_id.
            Args:
                product_id: ID của sản phẩm cần lấy.
            Returns:
                Result: Chứa dict dữ liệu nếu tìm thấy, hoặc lỗi PRODUCT_NOT_FOUND.
            """
            product_data = self.repo.get_product(product_id)
            if not product_data:
                return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
            return Result.Ok({
            str(product_id):product_data
        })

    def get_frame_data(self, product_id: str, frame_id: str) -> Result:
        """Lấy dữ liệu của một Frame cụ thể thuộc Product.
        
        Args:
            product_id: ID sản phẩm.
            frame_id: ID Frame cần lấy.
        Returns:
            Result: Chứa dict dữ liệu Frame hoặc lỗi tương ứng.
        """
        # Kiểm tra sản phẩm trước
        if not self.repo.get_product(product_id):
            return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        frame_data = self.repo.get_frame(product_id, frame_id)
        if not frame_data:
            return Result.Fail(ErrorCode.FRAME_NOT_FOUND)
        return Result.Ok(frame_data)

    def get_item_data(self, product_id: str, frame_id: str, item_id: str) -> Result:
        """Lấy chi tiết dữ liệu của một Item cụ thể từ Product và Frame.
        
        Args:
            product_id: ID sản phẩm.
            frame_id: ID Frame.
            item_id: ID Item cần lấy.
        Returns:
            Result: Chứa dict dữ liệu Item hoặc lỗi nếu không tồn tại.
        """
        # Kiểm tra tuần tự từ gốc tới ngọn để trả về lỗi chính xác
        if not self.repo.get_product(product_id):
            return Result.Fail(ErrorCode.PRODUCT_NOT_FOUND)
        if not self.repo.get_frame(product_id, frame_id):
            return Result.Fail(ErrorCode.FRAME_NOT_FOUND)
        item_data = self.repo.get(product_id, frame_id, item_id)
        if item_data is None:
            # Vì trong Enum chưa có ITEM_NOT_FOUND, sử dụng tạm DATA_INVALID
            return Result.Fail(ErrorCode.DATA_INVALID) 
        return Result.Ok(item_data)



    def compare_structure(self, data: dict, data_frame: dict) -> bool:
        """Kiểm tra payload judgment là một phần hợp lệ của cây point/frame.

        Args:
            data: Payload chỉ chứa các point đã cấu hình inspector.
            data_frame: Cây định danh đầy đủ product/frame/point.
        Returns:
            bool: True nếu mọi khóa payload tồn tại trong cây định danh.
        Errors: Không phát sinh; cấu trúc sai trả về False.
        """
        if not isinstance(data, dict) or not isinstance(data_frame, dict):
            return False
        for key, value in data.items():
            if key not in data_frame:
                return False
            if isinstance(value, dict):
                expected = data_frame[key]
                if not isinstance(expected, dict):
                    return False
                if expected and not self.compare_structure(value, expected):
                    return False
        return True