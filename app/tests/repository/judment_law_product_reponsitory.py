# from app.repository import JudmentLawProductRepository
# repo = JudmentLawProductRepository()
# repo.clear()
# repo.upsert(
#     product_id="product_1",
#     frame_id="frame_1",
#     item_id="item_1",
#     item_data={
#         "check_measure": {
#             "line_1": {
#                 "name_line": "abc",
#                 "level1": 1,
#                 "level2": 2,
#                 "level3": 3,
#                 "level4": 4,
#                 "level5": 5
#             }
#         }
#     }
# )

# repo.upsert(
#     product_id="product_1",
#     frame_id="frame_1",
#     item_id="item_2",
#     item_data={
#         "check_measure": {
#             "line_2": {
#                 "name_line": "xyz",
#                 "level1": 10
#             }
#         }
#     }
# )

# print("========== EXISTS ==========")
# print(repo.exists("product_1", "frame_1", "item_1"))
# print(repo.exists("product_1", "frame_1", "item_2"))

# print("\n========== GET ==========")
# print(repo.get("product_1", "frame_1", "item_1"))

# print("\n========== PRODUCT ==========")
# print(repo.get_product("product_1"))

# print("\n========== FRAME ==========")
# print(repo.get_frame("product_1", "frame_1"))

# print("\n========== PRODUCT IDS ==========")
# print(repo.get_product_ids())

# print("\n========== FRAME IDS ==========")
# print(repo.get_frame_ids("product_1"))

# print("\n========== ITEM IDS ==========")
# print(repo.get_item_ids("product_1", "frame_1"))

# print("\n========== UPDATE ==========")
# repo.upsert(
#     product_id="product_1",
#     frame_id="frame_1",
#     item_id="item_1",
#     item_data={
#         "name": "updated item"
#     }
# )

#print(repo.get("product_1", "frame_1", "item_1"))

# print("\n========== DELETE ==========")
# print(repo.delete("product_1", "frame_1", "item_2"))
# print(repo.get("product_1", "frame_1", "item_2"))

# print("\n========== RAW DATA ==========")
# print(repo.data)

# python -m app.tests.repository.judment_law_product_reponsitory


# print("\n========== LOAD FROM DICT (REPLACE) ==========")
# repo.load_from_dict({
#     "product_1": {
#         "frame_1": {
#             "item_1": {
#                 "check_measure": {
#                     "line_1": {
#                         "name_line": "abc",
#                         "level1": 1
#                     }
#                 }
#             }
#         }
#     }
# })
# print(repo.data)


# print("\n========== LOAD FROM DICT (MERGE) ==========")
# repo.load_from_dict({
#     "product_1": {
#         "frame_1": {
#             "item_2": {
#                 "check_measure": {
#                     "line_2": {
#                         "name_line": "xyz",
#                         "level1": 10
#                     }
#                 }
#             }
#         },
#         "frame_2": {
#             "item_3": {
#                 "check_measure": {
#                     "line_3": {
#                         "name_line": "new_frame",
#                         "level1": 999
#                     }
#                 }
#             }
#         }
#     },
#     "product_2": {
#         "frame_1": {
#             "item_1": {
#                 "check_measure": {
#                     "line_1": {
#                         "name_line": "product_2_data",
#                         "level1": 123
#                     }
#                 }
#             }
#         }
#     }
# }, merge=True)

# print(repo.data)


# print("\n========== VERIFY MERGE RESULT ==========")

# print("product_1:", "product_1" in repo.data)
# print("frame_2:", "frame_2" in repo.data["product_1"])
# print("item_2:", "item_2" in repo.data["product_1"]["frame_1"])
# print("product_2:", "product_2" in repo.data)

# print(repo.get("product_1", "frame_1", "item_2"))
# print(repo.get("product_1", "frame_2", "item_3"))
# print(repo.get("product_2", "frame_1", "item_1"))