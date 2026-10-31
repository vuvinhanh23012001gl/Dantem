import numpy as np

from app.services import ProductService
from app.repository import ProductRepository

from app.utils import (
    Folder,
    Tool_OpenCv2
)

from app.model import Product

from app.core import Result


# =========================
# INIT
# =========================



obj_cv2 = Tool_OpenCv2()

repository = ProductRepository(

)

service = ProductService(
    repository=repository,
  
)


# =========================
# HELPER
# =========================

def print_result(
    result: Result
):

    print(f"ok      : {result.ok}")

    print(f"error   : {result.error}")

    print(f"message : {result.message()}")

    print(f"data    : {result.data}")


# =========================
# TEST ADD PRODUCT
# =========================

# def test_add_product():
#     print("\n===== TEST ADD PRODUCT =====")

#     product = Product(
#         id=1,
#         name="Ao Thun",
#         description="Ao mau den"
#     )

#     img = np.zeros(
#         (480, 640, 3),
#         dtype=np.uint8
#     )

#     result = service.add_product(
#         product=product,
#         img=img
#     )

#     print_result(result)



# =========================
# TEST GET PRODUCT
# =========================

def test_get_product():

    print("\n===== TEST GET PRODUCT =====")

    result = service.get_product_by_id(
        6
    )

    print_result(result)

    if result.ok:

        product = result.data

        print(
            f"name : {product.name}"
        )


# =========================
# TEST GET ALL PRODUCTS
# =========================

def test_get_all_products():

    print("\n===== TEST GET ALL PRODUCTS =====")

    result = service.get_all_products()

    print_result(result)

    if result.ok:

        products = result.data

        print(
            f"total product : {len(products)}"
        )

        for product in products:

            print(product)


# =========================
# TEST ADD ROI IMAGE
# =========================

def test_add_roi_image():

    print("\n===== TEST ADD ROI IMAGE =====")

    img = np.zeros(
        (200, 200, 3),
        dtype=np.uint8
    )

    result = service.add_roi_image(
        product_id=5,
        img=img
    )

    print_result(result)


# =========================
# TEST DELETE PRODUCT
# =========================

def test_delete_product():

    print("\n===== TEST DELETE PRODUCT =====")

    result = service.delete_product(
        product_id=5
    )

    print_result(result)


# =========================
# RUN ALL TEST
# =========================

def test_update_product():

    print("\n===== TEST UPDATE PRODUCT =====")

    result = service.update_product(
        product_id=6,
        name="Ao Thun Update",
        description="Ao moi"
    )

    print_result(result)

    if result.ok:

        product = result.data

        print(product.updated_at)

def test_get_arr_path_img_roi_product_by_id():

    print(
        "\n===== TEST GET ROI IMAGE PATHS ====="
    )
    id = 6 
    result = service.get_arr_path_img_roi_product_by_id(id)

    print_result(result)

    if result.ok:

        print("\nDanh sách ảnh ROI:")

        for path_img in result.data:

            print(path_img)


def run_all_test():

    test_add_product()

    # test_get_product()

    # test_get_all_products()

    #test_add_roi_image()

    #atest_delete_product()
    #test_update_product()

    # test_get_arr_path_img_roi_product_by_id()
    # python -m app.tests.test_product_service
    pass


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    run_all_test()