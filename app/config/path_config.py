import sys
from pathlib import Path

# Thư mục gốc: tương thích cả môi trường dev lẫn môi trường biên dịch exe (PyInstaller / auto-py-to-exe)
if getattr(sys, "frozen", False):
    EXE_DIR = Path(sys.executable).resolve().parent
    meipass = getattr(sys, "_MEIPASS", None)
    mei_dir = Path(meipass) if meipass else None

    # Tìm vị trí thực tế của thư mục chứa templates / static (có thể trong app, _internal/app, hoặc cùng cấp exe)
    candidates = [
        EXE_DIR / "app",
        EXE_DIR / "_internal" / "app",
        mei_dir / "app" if mei_dir else None,
        EXE_DIR,
        EXE_DIR / "_internal",
        mei_dir if mei_dir else None,
    ]
    BASE_DIR = EXE_DIR
    for cand in candidates:
        if cand and cand.exists() and (cand / "templates").exists():
            BASE_DIR = cand
            break
    WORKSPACE_DIR = EXE_DIR
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    WORKSPACE_DIR = BASE_DIR.parent
    EXE_DIR = WORKSPACE_DIR

PATH_STORAGE = "storage"
PATH_INPUT = "input"

# Xác định vị trí BASE_PATH_STORAGE, BASE_PATH_INPUT_STORAGE, BASE_PATH_OUTPUT
if getattr(sys, "frozen", False):
    # Ưu tiên storage nằm trong _internal (được đóng gói cùng app theo thiết kế onedir)
    if (BASE_DIR / "storage").exists():
        BASE_PATH_STORAGE = BASE_DIR / "storage"
    elif (EXE_DIR / "_internal" / "app" / "storage").exists():
        BASE_PATH_STORAGE = EXE_DIR / "_internal" / "app" / "storage"
    elif (EXE_DIR / "_internal" / "storage").exists():
        BASE_PATH_STORAGE = EXE_DIR / "_internal" / "storage"
    elif (EXE_DIR / "storage").exists():
        BASE_PATH_STORAGE = EXE_DIR / "storage"
    elif (EXE_DIR / "app" / "storage").exists():
        BASE_PATH_STORAGE = EXE_DIR / "app" / "storage"
    else:
        BASE_PATH_STORAGE = (EXE_DIR / "_internal" / "app" / "storage") if (EXE_DIR / "_internal" / "app").exists() else (EXE_DIR / "_internal" / "storage")

    if (EXE_DIR / "input").exists():
        BASE_PATH_INPUT_STORAGE = EXE_DIR / "input"
    elif (EXE_DIR / "app" / "input").exists():
        BASE_PATH_INPUT_STORAGE = EXE_DIR / "app" / "input"
    else:
        BASE_PATH_INPUT_STORAGE = EXE_DIR / "input"

    if (EXE_DIR / "output").exists():
        BASE_PATH_OUTPUT = EXE_DIR / "output"
    elif (EXE_DIR / "app" / "output").exists():
        BASE_PATH_OUTPUT = EXE_DIR / "app" / "output"
    else:
        BASE_PATH_OUTPUT = EXE_DIR / "output"
else:
    BASE_PATH_INPUT_STORAGE = BASE_DIR / PATH_INPUT
    BASE_PATH_STORAGE = BASE_DIR / PATH_STORAGE
    BASE_PATH_OUTPUT = BASE_DIR / "output"

PATH_FOLDER_STATIC = BASE_DIR / "static"
PATH_FOLDER_TEMPLATES = BASE_DIR / "templates"
URL_PATH_STATIC = "/static"
URL_PATH_STORAGE = "/storage"
URL_PATH_OUTPUT = "/output"


# --- ĐỊNH NGHĨA THỦ CÔNG CÁC ĐƯỜNG DẪN ---
# 1. Các Folder (Đường dẫn tuyệt đối)
PATH_PRODUCT_IMG = str(BASE_PATH_STORAGE / "manager_product_images")
PATH_PRODUCT_ROI_PRODUCT_IMG = str(BASE_PATH_STORAGE / "manager_product_roi_images")

# 2. Các File (Đường dẫn tuyệt đối)
PATH_PRODUCT_DATA = str(BASE_PATH_STORAGE / "products_data.json")
PATH_PRODUCT_CHOOSE_PRODUCT = str(BASE_PATH_STORAGE / "choose_product_select.json")
# PATH_PRODUCT_MODEL = str(BASE_PATH_STORAGE / "unetpp.pth")
PATH_FEATUERES_CFG_CAM = str(BASE_PATH_STORAGE / "features.cfg")
PATH_INFORMATION_SOFTWARE = str(BASE_PATH_STORAGE / "information_software.json")
PATH_CONFIG_SOFTWARE = str(BASE_PATH_STORAGE / "config_software.json")
PATH_COUNT_PRODUCT = str(BASE_PATH_STORAGE / "count_product.json")
PATH_FILE_BARCODE_ACCOUNT = str(BASE_PATH_STORAGE / "barcode_accounts.json")

# --- ĐỊNH NGHĨA ĐƯỜNG DẪN TƯƠNG ĐỐI (Dùng cho Frontend hoặc lưu JSON) ---
PATH_CONFIG_POINTS =   str(BASE_PATH_STORAGE / "points.json")
# print(PATH_CONFIG_POINTS)

PATH_FOLDER_IMG_COORDINATE_PRODUCT = str(BASE_PATH_STORAGE/"img_points")
PATH_FOLDER_OUTPUT = BASE_PATH_OUTPUT
PATH_FOLDER_OUTPUT_JUDGMENT = PATH_FOLDER_OUTPUT / "judgment"
PATH_FOLDER_OUTPUT_RETRAIN = PATH_FOLDER_OUTPUT / "retrain"

# Tự động đảm bảo các thư mục runtime thiết yếu luôn tồn tại
for _dir in [
    BASE_PATH_STORAGE,
    BASE_PATH_STORAGE / "config",
    BASE_PATH_STORAGE / "manager_product_images",
    BASE_PATH_STORAGE / "manager_product_roi_images",
    BASE_PATH_STORAGE / "img_points",
    BASE_PATH_OUTPUT,
    PATH_FOLDER_OUTPUT_JUDGMENT,
    PATH_FOLDER_OUTPUT_RETRAIN,
    PATH_FOLDER_STATIC,
    PATH_FOLDER_TEMPLATES,
]:
    try:
        _dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

PATH_DEFAULT_LOG_DISK = Path("C:/")
PATH_FOLDER_IMG_COORDINATE_OUTPUT = str(BASE_PATH_OUTPUT / "patch_core")
# Alias giữ tương thích với các module/test đang dùng tên cũ.
PATH_FOLDER_IMG_COORDINATE_PRODUCT_RETRAIN = PATH_FOLDER_IMG_COORDINATE_OUTPUT
PATH_FILE_DATA_CONFIG_IAI = str(BASE_PATH_STORAGE/"config"/"iai.json")
PATH_FILE_DATA_CONFIG_ROBOT = str(BASE_PATH_STORAGE/"config"/"robot.json")
PATH_FILE_DATA_CONFIG_ANTI_BLUR = str(BASE_PATH_STORAGE/"anti_blur.json")
PATH_FILE_DATA_CONFIG_JUDMENT_LAW = str(BASE_PATH_STORAGE/"config_judgment_law.json")

PATH_FOLDER_MODEL_DETECT_PATCH_CORE = str(BASE_PATH_INPUT_STORAGE/"model"/"patch_core")
PATH_FILE_RESNET18_BACKBONE = str(BASE_PATH_INPUT_STORAGE / "model" / "backbone" / "resnet18-f37072fd.pth")
PATH_FILE_DEFAULT_PATCHCORE_INDEX = str(WORKSPACE_DIR / "model" / "patchcore_ivf.index")
PATCHCORE_RUNTIME_DIR_NAME = "runtime"
PATCHCORE_INITIAL_DIR_NAME = "the_first"
PATCHCORE_INDEX_FILE_NAME = "patchcore.index"
PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST = str(
	BASE_PATH_STORAGE / "anomaly_point_crop_patch_core_record.json"
)
PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST = str(
	BASE_PATH_STORAGE / "foreign_crop_patch_core_record.json"
)
PATH_FILE_MODEL_YOLO_STAMP = str(BASE_PATH_INPUT_STORAGE/"model"/"yolo"/"object_stamp_detect.pt")
PATH_FILE_MODEL_YOLO_FOREIGN = str(BASE_PATH_INPUT_STORAGE/"model"/"yolo"/"object_foreign_object.pt")
PATH_FILE_MODEL_YOLO_STAMP_ALIGNMENT = str(BASE_PATH_INPUT_STORAGE / "model" / "yolo" / "object_obb_stamp_frame.pt")

# 3. Đường dẫn tài liệu hướng dẫn sử dụng (PDF)
PATH_DOCUMENTS_DIR = BASE_DIR / "static" / "docurments"
PATH_DOC_INSTRUCT_WORKER = str(PATH_DOCUMENTS_DIR / "instruct_worker.pdf")
PATH_DOC_INSTRUCT_STAFF_EE = str(PATH_DOCUMENTS_DIR / "instruct_staff_ee.pdf")
PATH_DOC_INSTRUCT_FIX_ERRO = str(PATH_DOCUMENTS_DIR / "instruct_fix_erro.pdf")

