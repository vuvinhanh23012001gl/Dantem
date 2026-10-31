from app.model import Point
from app.repository import PointRepository
from app.services import PointService

from app.config import (
    PATH_CONFIG_POINTS,
    PATH_FOLDER_MODEL_DETECT_PATCH_CORE,
    PATH_FOLDER_IMG_COORDINATE_PRODUCT,
    PATH_FOLDER_IMG_COORDINATE_PRODUCT_RETRAIN,
    BASE_DIR
)
# =========================================
# PRINT RESULT
# =========================================

def print_result(
    title,
    result
):

    print("\n" + "=" * 60)

    print(title)

    print("=" * 60)

    print("OK:", result.ok)

    print("DATA:", result.data)

    print("ERROR:", result.error)


# =========================================
# TEST
# =========================================

def test_point_service():

    # =========================================
    # INIT
    # =========================================

    repository = PointRepository(
        
    )

    service = PointService(
        repository,
    )

    # =========================================
    # TEST PARAM
    # =========================================

    # product_id = 1

    # frame_id = 0

    # point_id = 0

    # # =========================================
    # # CREATE POINT
    # # =========================================

    # point = Point(

    #     point_id=point_id,

    #     x=20,

    #     y=200,

    #     z=300,

    #     arr_polygon=[

    #         [

    #             (10, 10),

    #             (100, 10),

    #             (100, 100)

    #         ],

    #         [

    #             (200, 200),

    #             (300, 200),

    #             (300, 300)

    #         ]
    #     ]
    # )
    #  # =========================================
    # # get_points_by_product_id
    # # =========================================
    # dict_data = service.get_points_by_product_id(1)
    # print(dict_data.data)
    
    # =========================================
    # CREATE IMAGE
    # =========================================

    # img = np.zeros(

    #     (200, 200, 3),

    #     dtype=np.uint8
    # )

    # =========================================
    # ADD POINT
    # =========================================

    # res_add = service.add_point(

    #     product_id=product_id,

    #     frame_id=frame_id,

    #     point=point,

    #     img=img
    # )

    # print_result(
    #     "ADD POINT",
    #     res_add
    # )

    # # =========================================
    # # GET PRODUCT
    # # =========================================

    # res_get_product = (

    #     service.get_points_by_product_id(
    #         product_id
    #     )
    # )

    # print_result(
    #     "GET PRODUCT",
    #     res_get_product
    # )

    # # =========================================
    # # GET FRAME
    # # =========================================

    # res_get_frame = (

    #     service.get_points_by_frame_id(

    #         product_id,

    #         frame_id
    #     )
    # )

    # print_result(
    #     "GET FRAME",
    #     res_get_frame
    # )

    # # =========================================
    # # GET POINT
    # # =========================================

    # res_get_point = (

    #     service.get_point_by_id(

    #         product_id,

    #         frame_id,

    #         point_id
    #     )
    # )

    # print_result(
    #     "GET POINT",
    #     res_get_point
    # )

    # # =========================================
    # # UPDATE POINT
    # # =========================================
 
    # res_update = (

    #     service.update_point(

    #         product_id = product_id,

    #         frame_id=frame_id,

    #         point_id=point_id,

    #         x=999,

    #         y=888,

    #         z=777,

    #         arr_polygon=[

    #             [

    #                 (1, 1),

    #                 (2, 2),

    #                 (3, 3)

    #             ]
    #         ]
    #     )
    # )

    # print_result(
    #     "UPDATE POINT",
    #     res_update
    # )

    # # =========================================
    # # SET POLYGON
    # # =========================================

    # res_polygon = (

    #     service.set_arr_polygon_by_point_id(

    #         product_id=product_id,

    #         frame_id=frame_id,

    #         point_id=point_id,

    #         arr_polygon=[

    #             [

    #                 [0, 0],

    #                 [10, 0],

    #                 [10, 10]

    #             ]
    #         ]
    #     )
    # )

    # print_result(
    #     "SET POLYGON",
    #     res_polygon
    # )

    # # =========================================
    # # CHECK MODEL
    # # =========================================

    # res_has_model = (

    #     service.has_path_model_patch_core(

    #         product_id=product_id,

    #         frame_id=frame_id,

    #         point_id=point_id
    #     )
    # )

    # print("\nHAS MODEL PATH")

    # print(res_has_model)

    # # =========================================
    # # CHECK POLYGON
    # # =========================================

    # res_has_polygon = (

    #     service.has_arr_polygon(

    #         product_id=product_id,

    #         frame_id=frame_id,

    #         point_id=point_id
    #     )
    # )

    # print("\nHAS POLYGON")

    # print(res_has_polygon)

    # # =========================================
    # # CHECK IMG
    # # =========================================

    # res_has_img = (

    #     service.has_path_img_point(

    #         product_id=product_id,

    #         frame_id=frame_id,

    #         point_id=point_id
    #     )
    # )

    # print("\nHAS IMG")

    # print(res_has_img)

    # # =========================================
    # # GET ALL DATA
    # # =========================================

    # res_all = service.get_dict_data()

    # print_result(
    #     "GET ALL DATA",
    #     res_all
    # )

    # # =========================================
    # # DELETE POINT
    # # =========================================

    # res_delete = (

    #     service.delete_point(

    #         product_id=product_id,

    #         frame_id=frame_id,

    #         point_id=point_id
    #     )
    # )

    # print_result(
    #     "DELETE POINT",
    #     res_delete
    # )

    # # =========================================
    # # FINAL DATA
    # # =========================================

    # res_final = (
    #     service.get_dict_data()
    # )

    # print_result(
    #     "FINAL DATA",
    #     res_final
    # )

    # # =========================================
    # # DELETE PRODUCT
    # # =========================================

    # # res_delete_product = (
    # #
    # #     service.delete_by_product_id(
    # #         product_id
    # #     )
    # # )
    # #
    # # print_result(
    # #     "DELETE PRODUCT",
    # #     res_delete_product
    # # )
    # # =========================================
    # # DELETE Frame
    # # =========================================
    # service.delete_frame(1,1)




        # =========================================
    # TEST EXISTS POINT ID
    # =========================================
    # =========================================
    # TEST EXISTS PRODUCT + POINT ID
    # =========================================
    # print("TEST EXISTS PRODUCT + POINT ID")
    # exists = (
    #     service.is_exists_product_and_point_id(
    #         product_id=product_id,
    #         point_id=point_id
    #     )
    # )
    # print(
    #     f"Product ID {product_id} "
    #     f"+ Point ID {point_id} exists:",
    #     exists
    # )
    # # =========================================
    # # TEST NOT EXISTS PRODUCT + POINT ID
    # # =========================================
    # not_exists = (
    #     service.is_exists_product_and_point_id(
    #         product_id=product_id,
    #         point_id=999999
    #     )
    # )
    # print(
    #     f"Product ID {product_id} "
    #     f"+ Point ID 999999 exists:",
    #     not_exists
    # )
    # data = service.get_xyz_by_product_frame(1,0).data
    # print(data)

    # data = service.get_all_xyz_by_product_id(1).data
    # print(data)

    # get_all_retrain_paths_by_product_id
    # result = service.get_all_retrain_paths_by_product_id(1) # tra ve lop path danh sach nhung foler retrain
    # print("Danh sách đường dẫn ảnh retrain",str(result.data))

    # test path
    # result = service.get_retrain_paths_by_product_frame(1,0)
    # print(result.data)

    #test get_product_frame_id_tree
    # tree = service.get_product_frame_id_tree()
    # print(tree)
    # result = service.get_point_tree_by_product_id("1")
    # print("result",result.data)
    result = service.get_path_img_point(1,0,0)
    print(result.to_dict())

# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    pass
    test_point_service()
    # python -m app.tests.test_point_service