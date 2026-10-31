from app.utils import Folder

from app.config import (
    PATH_PRODUCT_CHOOSE_PRODUCT
)

class ChooseProductRepository:

    def __init__(self  ):
        self.path_file_config = (
            PATH_PRODUCT_CHOOSE_PRODUCT
        )
        self.key_name = "product"
    # =========================
    # READ
    # =========================
    def read(self):

        data = (
            Folder
            .read_json_from_file(
                self.path_file_config
            )
        )
        if not data:

            return {}

        return data

    # =========================
    # WRITE
    # =========================

    def write(
        self,
        product_id
    ):

        data = {
            self.key_name: product_id
        }

        
        Folder.write_json_in_file(
            self.path_file_config,
            data
        )