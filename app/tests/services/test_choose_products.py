from app.repository import (
    ChooseProductRepository,
    ProductRepository
)

from app.services import (
    ChooseProductService,
    ProductService
)

from app.utils import (
    Folder,
    Tool_OpenCv2
)

from app.core import (
    Result
)


# =========================
# INIT
# =========================

obj_folder = Folder()

obj_cv2 = Tool_OpenCv2()

# =========================
# PRODUCT
# =========================

product_repository = (
    ProductRepository(
       
    )
)

product_service = (
    ProductService(
        repository=product_repository,
    )
)

# =========================
# CHOOSE PRODUCT
# =========================

choose_repository = (
    ChooseProductRepository(
      
    )
)

choose_service = (
    ChooseProductService(
        repository=choose_repository,
        product_service=product_service
    )
)


# =========================
# HELPER
# =========================

def print_result(
    result: Result
):

    print(f"ok         : {result.ok}")

    print(f"error      : {result.error}")

    print(f"message    : {result.message()}")

    print(f"data       : {result.data}")


# =========================
# TEST GET
# =========================

def test_get_choose_product():

    print(
        "\n===== TEST GET CHOOSE PRODUCT ====="
    )

    result = (
        choose_service
        .get_choose_product()
    )

    print_result(result)


# =========================
# TEST SET VALID
# =========================

def test_set_choose_product_valid():

    print(
        "\n===== TEST SET VALID PRODUCT ====="
    )

    result = (
        choose_service
        .set_choose_product(
            2
        )
    )

    print_result(result)


# =========================
# TEST SET INVALID
# =========================

# def test_set_choose_product_invalid():

#     print(
#         "\n===== TEST SET INVALID PRODUCT ====="
#     )

#     result = (
#         choose_service
#         .set_choose_product(
#             2
#         )
#     )

#     print_result(result)


# =========================
# TEST RESET
# =========================
# def test_is_choose_product_true():
#     result = (
#         choose_service
#         .is_choose_product(
#             2
#         )
#     )
#     print(
#         f"is_choose_product(2): "
#         f"{result}"
#     )

def test_reset_choose_product():

    print(
        "\n===== TEST RESET CHOOSE PRODUCT ====="
    )

    result = (
        choose_service
        .reset_choose_product()
    )

    print_result(result)


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    #test_get_choose_product()

    # test_is_choose_product_true()

    # test_set_choose_product_valid()

    # test_get_choose_product()

    # test_set_choose_product_invalid()

    #test_get_choose_product()

    # test_reset_choose_product()

    # test_get_choose_product()

    pass


# python -m app.tests.test_choose_products