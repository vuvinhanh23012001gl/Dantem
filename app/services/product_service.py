# =========================
# FILE: product_service.py
# =========================

import cv2
import datetime
import json
import shutil
import numpy as np
from pathlib import Path
from app.model import Product
from app.repository import (ProductRepository)
from app.utils import (Tool_OpenCv2,Folder)
from app.core import (Result,ErrorCode)
from app.config import (
    PATH_CONFIG_POINTS,
    PATH_PRODUCT_DATA,
    PATH_PRODUCT_IMG,
    PATH_PRODUCT_ROI_PRODUCT_IMG,
    PATH_FILE_DATA_CONFIG_JUDMENT_LAW,
    PATH_FOLDER_IMG_COORDINATE_PRODUCT,
    PATH_FOLDER_MODEL_DETECT_PATCH_CORE,
    PATH_FOLDER_IMG_COORDINATE_OUTPUT,
    PATH_FOLDER_OUTPUT_JUDGMENT,
    PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST,
    PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST,
)

class ProductService:

    def __init__(
        self,
        repository: ProductRepository,
    ):
        self.repository = repository
        self.products = (
            self._load_products()
        )
    # =========================
    # LOAD
    # =========================

    def _load_products(self):

        data_products = (
            self.repository.load_products()
        )

        products = {}

        for product_id, item in data_products.items():

            sp = Product(
                id=item.get("id"),
                name=item.get("name"),
                description=item.get("description"),
                limit_x_max=int(item.get("limit_x_max", 1)),
                limit_y_max=int(item.get("limit_y_max", 1)),
                limit_z_max=int(item.get("limit_z_max", 1)),
                home_x=float(item.get("home_x", 0)),
                home_y=float(item.get("home_y", 0)),
                home_z=float(item.get("home_z", 0)),
            )

            sp.created_at = item.get(
                "created_at"
            )

            sp.updated_at = item.get(
                "updated_at"
            )

            products[int(product_id)] = sp

        return products

    def reload_products(self):
        """Tải lại danh sách sản phẩm từ file cấu hình products_data.json vào bộ nhớ."""
        self.products = self._load_products()
        return self.products

    # =========================
    # SAVE
    # =========================

    def _save_products(self):

        self.repository.save_products(
            self.products
        )

    # =========================
    # GET PRODUCT
    # =========================

    def get_product_by_id(
        self,
        product_id
    )-> Result:
        # tim doi tuong qua ID Tra ve product ID
        # Tra ve doi tuong co data Product
        product = self.products.get(
            product_id
        )
        if not product:
            return Result.Fail(
                ErrorCode.PRODUCT_NOT_FOUND
            )
        return Result.Ok(product)



    def get_all_products(self):

        return Result.Ok(
            list(self.products.values())
        )

    # =========================
    # ADD PRODUCT
    # =========================\

    def add_product(
        self,
        product: Product,
        img=None
    ):
        result_find = (
            self.get_product_by_id(
                product.id
            )
        )
        if result_find.ok:
            return Result.Fail(
                ErrorCode.PRODUCT_ALREADY_EXISTED
            )
        time_now = str(
            datetime.datetime.now()
        )
        product.created_at = time_now
        product.updated_at = time_now
        path_img = (
            self.repository
            .get_product_image_path(
                product.id
            )
        )
        if isinstance(
            img,
            np.ndarray
        ):
            success = (
                Tool_OpenCv2.save_image(
                    img,
                    str(path_img)
                )
            )
        else:
            img_black = (
                Tool_OpenCv2
                .create_black_image(
                    1920,
                    1200
                )
            )
            success = (
                Tool_OpenCv2.save_image(
                    img_black,
                    str(path_img)
                )
            )

        if not success:

            return Result.Fail(
                ErrorCode.PRODUCT_SAVE_IMAGE_FAIL
            )
        self.repository.create_roi_folder(
            product.id
        )
        self.products[
            product.id
        ] = product
        self._save_products()
        return Result.Ok(product)


    def delete_product(
        self,
        product_id
    ):

        result_find = (
            self.get_product_by_id(
                product_id
            )
        )

        if not result_find.ok:

            return Result.Fail(
                ErrorCode.PRODUCT_NOT_FOUND
            )

        report = self.delete_product_data(product_id)
        if report["failed"]:
            return Result.Fail(report)
        return Result.Ok(report)

    def get_delete_preview(self, product_id: int) -> dict:
        """Liệt kê dữ liệu product sẽ bị xóa trước khi người dùng xác nhận.

        Input: ``product_id`` có thể bằng 0.
        Output: báo cáo gồm các nhóm dữ liệu tồn tại và tổng số mục.
        Errors: không ném lỗi; lỗi đọc file được ghi trong ``failed``.
        """
        product_id = str(product_id)
        paths = self._product_cleanup_paths(product_id)
        existing = [item for item in paths if item["exists"]]
        return {
            "product_id": int(product_id),
            "items": existing,
            "count": len(existing),
            "failed": [],
        }

    def delete_product_data(self, product_id: int) -> dict:
        """Xóa toàn bộ dữ liệu liên quan product và trả báo cáo từng nhóm.

        Input: ``product_id`` có thể bằng 0.
        Output: ``deleted`` và ``failed`` là danh sách thao tác đã thực hiện.
        Errors: lỗi từng thao tác không dừng các thao tác còn lại.
        """
        product_key = str(product_id)
        report = {"product_id": int(product_id), "deleted": [], "failed": []}
        if int(product_id) not in self.products:
            report["failed"].append({
                "label": "products_data.json",
                "error": "Không tìm thấy sản phẩm.",
            })
            return report
        for item in self._product_cleanup_paths(product_key):
            if not item["exists"]:
                continue
            try:
                if item["kind"] == "json_key":
                    self._delete_json_key(item["path"], product_key)
                elif item["kind"] == "products_json":
                    data = self.repository.read_config()
                    data.get("products", {}).pop(product_key, None)
                    self.repository.write_config(data)
                elif item["kind"] == "patchcore_manifest":
                    self._delete_patchcore_manifest_records(item["path"], product_key)
                else:
                    path = Path(item["path"])
                    if path.is_dir():
                        shutil.rmtree(path)
                    elif path.exists():
                        path.unlink()
                report["deleted"].append(item["label"])
            except Exception as error:
                report["failed"].append({
                    "label": item["label"],
                    "error": str(error),
                })
        self.products.pop(int(product_id), None)
        self._save_products()
        return report

    def _product_cleanup_paths(self, product_id: str) -> list[dict]:
        """Tạo danh sách file/thư mục có dữ liệu riêng của product."""
        product_image = self.repository.get_product_image_path(product_id)
        roi_folder = self.repository.get_roi_folder(product_id)
        master_folder = Path(PATH_FOLDER_IMG_COORDINATE_PRODUCT) / product_id
        patchcore_folder = Path(PATH_FOLDER_MODEL_DETECT_PATCH_CORE) / product_id
        patchcore_output = Path(PATH_FOLDER_IMG_COORDINATE_OUTPUT) / product_id
        judgment_root = PATH_FOLDER_OUTPUT_JUDGMENT
        session_judgment = [
            path for path in judgment_root.glob("*/product_" + product_id)
            if path.exists()
        ] if judgment_root.exists() else []
        return [
            {"label": "products_data.json", "path": str(PATH_PRODUCT_DATA), "kind": "products_json", "exists": Path(PATH_PRODUCT_DATA).exists()},
            {"label": "Ảnh sản phẩm chính", "path": str(product_image), "kind": "path", "exists": product_image.exists()},
            {"label": "Thư mục ROI sản phẩm", "path": str(roi_folder), "kind": "path", "exists": roi_folder.exists()},
            {"label": "points.json", "path": str(PATH_CONFIG_POINTS), "kind": "json_key", "exists": self._json_key_exists(PATH_CONFIG_POINTS, product_id)},
            {"label": "config_judgment_law.json", "path": str(PATH_FILE_DATA_CONFIG_JUDMENT_LAW), "kind": "json_key", "exists": self._json_key_exists(PATH_FILE_DATA_CONFIG_JUDMENT_LAW, product_id)},
            {"label": "Ảnh master theo item", "path": str(master_folder), "kind": "path", "exists": master_folder.exists()},
            {"label": "Model PatchCore", "path": str(patchcore_folder), "kind": "path", "exists": patchcore_folder.exists()},
            {"label": "Output PatchCore", "path": str(patchcore_output), "kind": "path", "exists": patchcore_output.exists()},
            {
                "label": "Lịch sử manifest PatchCore Dị vật",
                "path": str(PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST),
                "kind": "patchcore_manifest",
                "exists": self._has_patchcore_records(PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST, product_id),
            },
            {
                "label": "Lịch sử manifest PatchCore Điểm bất thường",
                "path": str(PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST),
                "kind": "patchcore_manifest",
                "exists": self._has_patchcore_records(PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST, product_id),
            },
            *[
                {"label": f"Judgment session: {path.parent.name}", "path": str(path), "kind": "path", "exists": True}
                for path in session_judgment
            ],
        ]

    @staticmethod
    def _has_patchcore_records(manifest_path: str | Path, product_id: str) -> bool:
        """Kiểm tra có bản ghi train thuộc product_id trong file manifest không."""
        path = Path(manifest_path)
        if not path.exists():
            return False
        from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
            PatchCoreTrainRecordRepository,
        )
        return PatchCoreTrainRecordRepository(manifest_path=path).has_records_for_product(product_id)

    @staticmethod
    def _delete_patchcore_manifest_records(manifest_path: str | Path, product_id: str) -> int:
        """Xóa các bản ghi train của product_id trong file manifest PatchCore."""
        path = Path(manifest_path)
        if not path.exists():
            return 0
        from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
            PatchCoreTrainRecordRepository,
        )
        return PatchCoreTrainRecordRepository(manifest_path=path).delete_records_by_product_id(product_id)

    @staticmethod
    def _json_key_exists(path: str, key: str) -> bool:
        try:
            with open(path, "r", encoding="utf-8-sig") as file:
                return key in json.load(file)
        except (OSError, json.JSONDecodeError):
            return False

    @staticmethod
    def _delete_json_key(path: str, key: str) -> None:
        with open(path, "r", encoding="utf-8-sig") as file:
            data = json.load(file)
        data.pop(key, None)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)



    def add_roi_image(
        self,
        product_id,
        img
    ):

        result_find = (
            self.get_product_by_id(
                product_id
            )
        )

        if not result_find.ok:

            return Result.Fail(
                ErrorCode.PRODUCT_NOT_FOUND
            )

        if img is None:

            return Result.Fail(
                ErrorCode.PRODUCT_IMAGE_EMPTY
            )

        product = result_find.data

        folder_roi = (
            self.repository
            .create_roi_folder(
                product.id
            )
        )

        list_file = (
            self.repository
            .get_roi_files(
                product.id
            )
        )

        # =====================
        # CREATE FILE NAME
        # =====================

        new_index = len(list_file)

        path_file = (
            folder_roi /
            f"coordinates_{new_index}.jpg"
        )

        success = cv2.imwrite(
            str(path_file),
            img
        )

        if not success:

            return Result.Fail(
                ErrorCode.PRODUCT_SAVE_IMAGE_FAIL
            )

        return Result.Ok(
            str(path_file)
        )
    
    def update_product(
        self,
        product_id,
        name=None,
        description=None
    ):

        result_find = (
            self.get_product_by_id(
                product_id
            )
        )

        if not result_find.ok:

            return Result.Fail(
                ErrorCode.PRODUCT_NOT_FOUND
            )

        product = result_find.data

        # =====================
        # UPDATE DATA
        # =====================

        if name is not None:

            product.name = name

        if description is not None:

            product.description = description

        # =====================
        # UPDATE TIME
        # =====================

        product.updated_at = str(
            datetime.datetime.now()
        )

        # =====================
        # SAVE
        # =====================

        self._save_products()

        return Result.Ok(product)
    
    def get_arr_path_img_roi_product_by_id(
        self,
        product_id
    ):

        print(
            "---- Vào hàm Lấy danh sách ảnh ROI của sản phẩm ---"
        )

        # =====================
        # CHECK PRODUCT
        # =====================

        result_find = (
            self.get_product_by_id(
                product_id
            )
        )

        if not result_find.ok:

            print("Không tìm thấy ID")

            print(
                "---- Hết hàm lấy danh sách ảnh sp ---"
            )

            return Result.Fail(
                ErrorCode.PRODUCT_NOT_FOUND
            )

        # =====================
        # ROI FOLDER
        # =====================

        path_folder_roi_product = (
            self.repository
            .get_roi_folder(
                product_id
            )
        )

        # =====================
        # GET ROI FILES
        # =====================

        list_name_file = (
            self.repository
            .get_roi_files(
                product_id
            )
        )

        if len(list_name_file) == 0:

            print(
                f"Chưa có ảnh ROI cho sản phẩm id={product_id}"
            )

            print(
                "---- Hết hàm lấy danh sách ảnh sp ---"
            )

            return Result.Ok([])

        # =====================
        # CREATE WEB PATH
        # =====================

        arr_path_img_roi = []

        for file_name in list_name_file:

            full_path = (
                path_folder_roi_product
                / file_name
            )

            # =====================
            # WEB PATH
            # =====================

            path_poxis = (
                Folder
                .get_parts_from_bottom(
                    full_path,
                    levels=4
                )
            )

            arr_path_img_roi.append(
                str(path_poxis)
            )

        print(
            "danh sách ảnh ROI:",
            arr_path_img_roi
        )

        print(
            "---- Hết hàm lấy danh sách ảnh sp ---"
        )

        return Result.Ok(
            arr_path_img_roi
        )
    
    
    def get_to_dict_arr_path_src(
        self
    ):

        """
        Trả về danh sách dict thông tin
        sản phẩm + đường dẫn ảnh web
        """

        arr_product = []

        for product in self.products.values():

            dict_out = (
                product.to_dict()
            )

            # =====================
            # IMAGE PATH
            # =====================

            path_save_img = (
                self.repository
                .get_product_image_path(
                    product.id
                )
            )

            path_poxis = (
                Folder
                .get_parts_from_bottom(
                    path_save_img,
                    levels=3
                )
            )

            dict_out["image_src"] = (
                str(path_poxis)
            )

            arr_product.append(
                dict_out
            )

        return Result.Ok(
            arr_product
        )
    
