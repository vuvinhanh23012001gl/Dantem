from enum import Enum


class ErrorCode(Enum):

    # =====================================
    # CAMERA
    # =====================================

    CAMERA_TIMEOUT = 1001
    CAMERA_DISCONNECT = 1002

    # =====================================
    # CALIBRATION
    # =====================================
    CALIBRATION_ALREADY_EXISTS = 1500
    CALIBRATION_NOT_FOUND = 1501
    CALIBRATION_NOT_ENOUGH_SAMPLE = 1502
    CALIBRATION_EMPTY_DATA  = 1503
    CALIBRATION_INVALID_REAL_LENGTH = 1504
    CALIBRATION_INVALID_MEAN = 1505
    CALIBRATION_FILTERED_TOO_MUCH = 1506
    CALIBRATION_ID_TEMS_MISMATCH = 1507
    # =====================================
    # PRODUCT
    # =====================================

    PRODUCT_ALREADY_EXISTED = 5001
    PRODUCT_NOT_FOUND = 5002
    PRODUCT_IMAGE_EMPTY = 5003
    PRODUCT_SAVE_IMAGE_FAIL = 5004

    PRODUCT_ID_INVALID = 5005

    # =====================================
    # DATA
    # =====================================

    DATA_INVALID = 5050
    INVALID_INPUT = 5051

    
    # =====================================
    # FRAME
    # =====================================

    FACE_ID_INVALID = 5500
    FRAME_ID_INVALID = 5500

    # =====================================
    # POINT
    # =====================================

    POINT_NOT_FOUND = 6001
    POINT_ALREADY_EXISTS = 6002
    IMAGE_INVALID = 6003

    FACE_NOT_FOUND = 6050
    FRAME_NOT_FOUND = 6050

    POINT_X_INVALID = 6004
    POINT_Y_INVALID = 6005
    POINT_Z_INVALID = 6006
    IMAGE_NOT_FOUND = 7000

    #law regulation
    DATA_IS_NOT_CORRECT_FROMAT = 3001
    DATA_NOT_FOUND = 3002
    
    LABEL_NOT_FOUND = 8000
    BOX_DATA_INVALID = 8100      # Thiếu trường trong box hoặc box sai định dạng
    BOX_COORDINATE_INVALID = 8101 # Tọa độ x, y, width, height không hợp lệ
    INVALID_TYPE = 8001
    INVALID_FORMAT = 8002        # <-- THÊM MỚI: Định dạng JSON/Dict chung không đúng
    MISSING_FIELD = 8003         # <-- THÊM MỚI: Thiếu trường bắt buộc trong dữ liệu
    INVALID_VALUE = 8004
    PATCHCORE_MODEL_NOT_FOUND = 8200
    PATCHCORE_BUSY = 8201




ERROR_MESSAGE = {
    ErrorCode.PATCHCORE_BUSY: "[Thông báo] Model PatchCore đang bận. Vui lòng chờ phiên hiện tại hoàn tất.",
    ErrorCode.PATCHCORE_MODEL_NOT_FOUND: "[Lỗi] Chưa tạo model PatchCore cho item này. Vui lòng nhấn 'Tạo model' trước.",
    ErrorCode.IMAGE_NOT_FOUND:"[Thất bại] Không thể tìm thấy ảnh trong bộ nhớ.",
    # =====================================
    # CAMERA
    # =====================================

    ErrorCode.CAMERA_TIMEOUT:
        "[Thất bại] Camera timeout",

    ErrorCode.CAMERA_DISCONNECT:
        "[Thất bại] Mất kết nối với camera",

    # =====================================
    # CALIBRATION
    # =====================================


    ErrorCode.CALIBRATION_ALREADY_EXISTS :"[Cảnh báo] Calibartion đã tồn tại",
    ErrorCode.CALIBRATION_NOT_FOUND :"[Cảnh báo] Không tìm thấy Calibration",
    ErrorCode.CALIBRATION_NOT_ENOUGH_SAMPLE: "[Cảnh báo] Không đủ dữ liệu hiệu chuẩn",
    ErrorCode.CALIBRATION_EMPTY_DATA: "[Cảnh báo] Dữ liệu hiệu chuẩn rỗng",
    ErrorCode.CALIBRATION_INVALID_REAL_LENGTH: "[Cảnh báo] Chiều dài thực không hợp lệ",
    ErrorCode.CALIBRATION_INVALID_MEAN: "[Lỗi] Giá trị trung bình pixel không hợp lệ (= 0)",
    ErrorCode.CALIBRATION_FILTERED_TOO_MUCH: "[Cảnh báo] Lọc nhiễu quá nhiều, không đủ dữ liệu tin cậy",
    ErrorCode.CALIBRATION_ID_TEMS_MISMATCH :"CALIBRATION_ID_TEMS_MISMATCH",
    # =====================================
    # PRODUCT
    # =====================================

    ErrorCode.PRODUCT_ALREADY_EXISTED:
        "[Cảnh báo] Sản phẩm hiện đã tồn tại. Hãy tạo sản phẩm mới mã ID khác",

    ErrorCode.PRODUCT_NOT_FOUND:
        "[Lỗi] Không tìm thấy product",

    ErrorCode.PRODUCT_IMAGE_EMPTY:
        "[Lỗi] Ảnh product rỗng",

    ErrorCode.PRODUCT_SAVE_IMAGE_FAIL:
        "[Lỗi] Không thể lưu ảnh product",

    ErrorCode.PRODUCT_ID_INVALID:
        "[Lỗi] product_id không hợp lệ",

    # =====================================
    # DATA
    # =====================================

    ErrorCode.DATA_INVALID:
        "[Lỗi] Dữ liệu không hợp lệ",

    # =====================================
    # FRAME
    # =====================================

    ErrorCode.FRAME_ID_INVALID:
        "[Lỗi] frame_id không hợp lệ",

    # =====================================
    # POINT
    # =====================================

    ErrorCode.POINT_NOT_FOUND:
        "[Lỗi] Không tìm thấy point",

    ErrorCode.POINT_ALREADY_EXISTS:
        "[Thất bại] Point đã tồn tại",

    ErrorCode.IMAGE_INVALID:
        "[Lỗi] Ảnh đầu vào rỗng hoặc không hợp lệ",

    ErrorCode.POINT_X_INVALID:
        "[Lỗi] point.x không hợp lệ",

    ErrorCode.POINT_Y_INVALID:
        "[Lỗi] point.y không hợp lệ",

    ErrorCode.POINT_Z_INVALID:
        "[Lỗi] point.z không hợp lệ",

    ErrorCode.INVALID_INPUT:
    "[Lỗi] Dữ liệu đầu vào không hợp lệ",

    ErrorCode.FRAME_NOT_FOUND:
    "[Lỗi] Frame này đang không tồn tại",

    #law regulation
    ErrorCode.DATA_IS_NOT_CORRECT_FROMAT : "Dữ liệu không đúng khung",
    ErrorCode.DATA_NOT_FOUND : "Không tìm thấy ID yêu cầu",
    ErrorCode.LABEL_NOT_FOUND:  "Không tìm thấy đối tượng trong vùng đã chọn.",

    ErrorCode.BOX_DATA_INVALID: "[Lỗi] Thông tin vùng nhận diện (box) không hợp lệ hoặc thiếu trường bắt buộc",
    ErrorCode.BOX_COORDINATE_INVALID: "[Lỗi] Tọa độ hoặc kích thước của vùng nhận diện (box) phải là số nguyên dương",
    ErrorCode.INVALID_TYPE: "[Lỗi] Kiểu dữ liệu truyền vào không đúng định dạng số",
    ErrorCode.INVALID_FORMAT: "[Lỗi] Cấu trúc hoặc định dạng dữ liệu gửi lên không đúng yêu cầu", # <-- THÊM MỚI
    ErrorCode.MISSING_FIELD: "[Lỗi] Thiếu trường thông tin bắt buộc trong dữ liệu yêu cầu",         # <-- THÊM MỚI
    ErrorCode.INVALID_VALUE: "[Lỗi] Giá trị dữ liệu không hợp lệ hoặc chưa được thiết lập (-1)",  # <-- THÊM MỚI
}

# print(" ErrorCode.POINT_ALREADY_EXISTS", ErrorCode.POINT_ALREADY_EXISTS.name)
# print(" ErrorCode.POINT_ALREADY_EXISTS", ErrorCode.POINT_ALREADY_EXISTS.value)