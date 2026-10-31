from app.repository import (
    ChooseProductRepository
)

from app.services import (
    ProductService
)

from app.core import (
    Result,
    ErrorCode
)


class ChooseProductService:

    DEFAULT_PRODUCT_ID = -1

    def __init__(
        self,
        repository: ChooseProductRepository,
        product_service: ProductService
    ):

        self.repository = repository

        self.product_service = (
            product_service
        )

        self.choose = (
            self._load_choose_product()
        )

    # =========================
    # LOAD
    # =========================

    def _load_choose_product(self):

        data = self.repository.read()

        if not data:

            self.repository.write(
                self.DEFAULT_PRODUCT_ID
            )

            return self.DEFAULT_PRODUCT_ID

        product_id = data.get(
            "product",
            self.DEFAULT_PRODUCT_ID
        )

        # =====================
        # CHECK PRODUCT EXIST
        # =====================

        result_product = (
            self.product_service
            .get_product_by_id(
                product_id
            )
        )

        if not result_product.ok:

            self.repository.write(
                self.DEFAULT_PRODUCT_ID
            )

            return self.DEFAULT_PRODUCT_ID

        return product_id

    # =========================
    # GET
    # =========================

    def get_choose_product(self):

        return Result.Ok(
            self.choose
        )

    # =========================
    # SET
    # =========================

    def set_choose_product(
        self,
        product_id
    ):

        # =====================
        # CHECK TYPE
        # =====================

        if not isinstance(
            product_id,
            int
        ):

            self.reset_choose_product()

            return Result.Fail(
                ErrorCode.DATA_INVALID
            )

        # =====================
        # CHECK PRODUCT EXIST
        # =====================

        result_product = (
            self.product_service
            .get_product_by_id(
                product_id
            )
        )
        print("result_product",result_product)
        if not result_product.ok:
            print("tim khong dung")
            self.reset_choose_product()

            return Result.Fail(
                ErrorCode.PRODUCT_NOT_FOUND
            )

        # =====================
        # SAVE
        # =====================
        
        print("tim dung")
        self.choose = product_id

        self.repository.write(
            product_id
        )

        return Result.Ok(
            product_id
        )

    # =========================
    # RESET
    # =========================

    def reset_choose_product(self):

        self.choose = (
            self.DEFAULT_PRODUCT_ID
        )

        self.repository.write(
            self.DEFAULT_PRODUCT_ID
        )

        return Result.Ok(
            self.choose
        )

    # =========================
    # REPR
    # =========================

    def __repr__(self):

        return (
            f"ChooseProductService("
            f"choose={self.choose}"
            f")"
        )
    
    def is_choose_product(
        self,
        product_id: int
    ) -> bool:
        # ham nay kiem tra 1 gia tri id co duoc chon khong ?
        return (
            self.choose == product_id
        )
