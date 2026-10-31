from pathlib import Path
from app.utils import Folder
from app.config import (
    PATH_PRODUCT_DATA,
    PATH_PRODUCT_IMG,
    PATH_PRODUCT_ROI_PRODUCT_IMG
)

class ProductRepository:
    def __init__( self ):
        self.path_file_config = (
            PATH_PRODUCT_DATA
        )
        self.name_manager = "products"

    # =========================
    # CONFIG
    # =========================

    def read_config(self) -> dict:
        data = (
            Folder
            .read_json_from_file(
                self.path_file_config
            )
        )
        if not data:
            return {}
        return data

    def write_config(
        self,
        data: dict
    ):
        Folder.write_json_in_file(
            self.path_file_config,
            data
        )


    def load_products(self) -> dict:
        data = self.read_config()
        return data.get(
            self.name_manager,
            {}
        )
    
    def save_products(
        self,
        products: dict
    ):
        data_out = {}
        for product_id, product in products.items():

            data_out[str(product_id)] = (
                product.to_dict()
            )
        self.write_config({
            self.name_manager: data_out
        })
    # =========================
    # IMAGE
    # =========================

    def get_product_image_path(
        self,
        product_id
    ):
        return (
            Path(PATH_PRODUCT_IMG)
            / f"{product_id}.jpg"
        )
    def get_roi_folder(
        self,
        product_id
    ):
        return (
            Path(PATH_PRODUCT_ROI_PRODUCT_IMG)
            / str(product_id)
        )

    def create_roi_folder(
        self,
        product_id
    ):
        path = self.get_roi_folder(
            product_id
        )
        path.mkdir(
            parents=True,
            exist_ok=True
        )
        return path

    def delete_roi_folder(
        self,
        product_id
    ):
        path = self.get_roi_folder(
            product_id
        )
        Folder.delete_folder(path)


    def get_roi_files(
        self,
        product_id
    ):
        path = self.get_roi_folder(
            product_id
        )
        return Folder.get_list_files(
            path
        )