import queue
import threading
import webbrowser
from enum import Enum, auto

from app.config import (
    IAIConfig,
    QueueConfig,
)


from app.model import QueueManager, Worker
from app.repository import (
    ChooseProductRepository,
    ProductRepository,
    PointRepository,
    JudmentLawProductRepository,
    ProductCountRepository,
    BarcodeAccountRepository,
)
from app.services import (
    CaptureItemDeleteService,
    ChooseProductService,
    IAIService,
    PointService,
    ProductService,
    JudmentLawProductSevice,
    ProductCountService,
    BarcodeAccountService,
)
from app.services.camera import Camera
from app.services.log import Config_SoftWare, Infor_Software, Manager_Log
from app.validate import ValidateCaptureProduct

from app.config import (
    PATH_FILE_MODEL_YOLO_STAMP,
    PATH_FILE_MODEL_YOLO_FOREIGN,
    PATH_FILE_MODEL_YOLO_STAMP_ALIGNMENT,
)

from app.engines.model_AI import ModelYoloObject, ModelYoloOBB
from app.engines.AI_model_process import FrameModelYoloObject
from app.judger import (
    Judment,
    StampDetector,
    StampAlignmentDetector,
    StampReversedDetector,
    ForeignObjectDetector,
    AnomalyPointDetector,
    OCRTextDetector,
    ColorDetector,
    BarcodeDetector,
    QRDetector,
)
from app.config import (
    YoloDetectObjectConfig,
    ClassNameObjectStructureDetectConfig,
)
from app.engines.service import (
    StructureFrameYoloService,
    AnomalyPointPatchCoreService,
    ForeignObjectPatchCoreService,
    StampAlignmentService,
    StampReversedService,
    ColorService,
    BarcodeQRService,
)
from app.core.context import RuntimeState


# from app.services.calculate_the_dimensions.handler_calibration import HandlerCalibration
# from app.services.calculate_the_dimensions.handler_work_detect import HandlerWorkDetect
# from app.services.calculate_the_dimensions.handler_work_detect import ImageQueueTester
# from app.services.product import ChooseProduct,ProductManager


class EnumMode(Enum):
    MODE_IDLE = auto()
    MODE_PREPOCESS = auto()
    MODE_TRANSFORM = auto()
    MODE_EXPORT = auto()


class ServiceContainer:
    def __init__(self):
        self.runtime_state = RuntimeState()
        self.prepared_product = None
        self.stage_preprocess = None
        print("---------------Load config-----------")
        self.obj_iai_config = IAIConfig()
        self.obj_iai_service = IAIService(self.obj_iai_config)

        print("---------------Tạo hàng đợi-----------")
        self.queue_manager = QueueManager()

        q_log_send_client = self.queue_manager.create_queue(
            name=QueueConfig.name_queue_log_client,
            maxsize=QueueConfig.SIZE_QUEUE_LOG_SEND_CLIENT,
        )
        q_data_send_client = self.queue_manager.create_queue(
            name=QueueConfig.ame_queue_data_client,
            maxsize=QueueConfig.SIZE_QUEUE_DATA_SEND_CLIENT,
        )
        # q_img_send_client (calibration removed)
        q_img_send_client = None
        q_process_capture = self.queue_manager.create_queue(
            name=QueueConfig.name_queue_process_capture,
            maxsize=QueueConfig.SIZE_QUEUE_IMG_CAPTURE,
        )
        q_manage = self.queue_manager.create_queue(
            name=QueueConfig.name_queue_manage,
            maxsize=QueueConfig.SIZE_QUEUE_MANAGE_LOG,
        )

        self.queue_log_send_client = Worker(q_log_send_client)
        self.queue_data_send_client = Worker(q_data_send_client)
        self.queue_img_send_client = None
        self.queue_process_capture = Worker(q_process_capture)
        self.queue_manage_log = Worker(q_manage)
        self.queue_send_MCU = queue.Queue(maxsize=QueueConfig.SIZE_QUEUE_DATA_SEND_MCU)
        self.queue_listen_MCU = queue.Queue(maxsize=QueueConfig.SIZE_QUEUE_DATA_LISTEN_MCU)

        # ---------------------------------------------------------
        # 2. CHẾ ĐỘ HOẠT ĐỘNG (MODES) & VALIDATE
        # ---------------------------------------------------------
        self._mode = EnumMode.MODE_IDLE
        self._lock_mode = threading.Lock()

        print("...----------------------------------.Init Service...-----------------------------.")
        self.obj_validate_capture_product = ValidateCaptureProduct()

        # ---------------------------------------------------------
        # 3. PHẦN CỨNG & KẾT NỐI ROBOT / COBOT (ETHERNET TCP)
        # ---------------------------------------------------------
        from app.machine.iaicontrol import IAIControl
        from app.config.robot_config import RobotConfig
        from app.machine.robot_control import RobotControl

        self.obj_robot_config = RobotConfig()
        self.obj_robot_control = RobotControl(self.obj_robot_config)
        print("✔ RobotControl (Ethernet TCP) init")

        self.obj_iai_control = IAIControl(
            serial_manager=None,
            config=self.obj_iai_config,
        )

        self.obj_manager_serial = None
        self.obj_com_service = None

        self.obj_camera = Camera()
        print("✔ Camera init")

        # ---------------------------------------------------------
        # 4. KHỞI TẠO TẦNG REPOSITORIES & SERVICES
        # ---------------------------------------------------------
        # Quản lý Point
        self.obj_point_repository = PointRepository()
        self.obj_point_service = PointService(self.obj_point_repository)
        self.obj_anomaly_point_patch_core_service = AnomalyPointPatchCoreService(
            self.obj_point_service
        )

        # Quản lý dữ liệu law regulations
        self.obj_law_regulation_reponsitory = JudmentLawProductRepository()
        self.obj_law_regulation_service = JudmentLawProductSevice(self.obj_law_regulation_reponsitory)

        # Quản lý Product & ChooseProduct
        self.obj_product_repository = ProductRepository()
        self.obj_products_service = ProductService(self.obj_product_repository)
        print("✔ ProductService init")

        self.obj_choose_product_repository = ChooseProductRepository()
        self.obj_choose_product = ChooseProductService(
            self.obj_choose_product_repository, self.obj_products_service
        )
        print("✔ ChooseProductService init")

        # Quản lý số đếm sản phẩm OK/NG/Tổng
        self.obj_product_count_repository = ProductCountRepository()
        self.obj_product_count_service = ProductCountService(self.obj_product_count_repository)
        print("✔ ProductCountService init")

        # HandlerWorkDetect (Commented gốc)
        # self.obj_detect = HandlerWorkDetect(
        #     self.obj_choose_product,
        #     self.obj_products_service,
        #     self.obj_calibration, self.queue_data_send_client,self.queue_process_capture,TypeSend.datatype_Home,PATH_PRODUCT_MODEL
        # )
        # print("✔ HandlerWorkDetect init")

        # Cấu hình phần mềm & Log
        self.obj_infor_software = Infor_Software()
        print("✔ Infor_Software init")
        self.obj_config_software = Config_SoftWare()
        print("✔ Config_SoftWare init")

        self.obj_manager_log = Manager_Log(
            Config_Software=self.obj_config_software,
            choose_product=self.obj_choose_product,
            product_service=self.obj_products_service,
            product_count_service=self.obj_product_count_service,
            queue_manager_log=self.queue_manage_log,
        )
        print("✔ Manager_Log init")

        # Quản lý Barcode & Account
        self.barcode_account_repository = BarcodeAccountRepository()
        self.barcode_account_service = BarcodeAccountService(self.barcode_account_repository)
        print("✔ BarcodeAccountService init")

        # self.obj_img_queue_capture_test = ImageQueueTester(self.obj_detect)
        # self.obj_img_queue_capture_test.start()

        print("-------------------------------------------------------------------------------------")

        # Quản lý Calibration (Đã loại bỏ hệ số calibration)
        self.obj_calibration_repository = None
        self.obj_service_calibration = None

        self.obj_capture_item_delete_service = CaptureItemDeleteService(
            self.obj_point_service,
            self.obj_law_regulation_service,
            calibration_service=None,
        )
        print("✔ CaptureItemDeleteService init")

        # ---------------------------------------------------------
        # 5. KHỞI TẠO CÁC AI ENGINES & COORDINATOR
        # ---------------------------------------------------------
        self.CLASS_STRUCTURE_NAME = ClassNameObjectStructureDetectConfig  # cai nay tham chieu den bien khong thay doi
        self.obj_yolo_structure_config = YoloDetectObjectConfig(
            path_model=PATH_FILE_MODEL_YOLO_STAMP
        )
        self.obj_model_yolo_structure = ModelYoloObject(
            self.obj_yolo_structure_config
        )
        self.obj_frame_model_yolo_structure = FrameModelYoloObject(
            self.obj_model_yolo_structure
        )
        self.obj_face_model_yolo_structure = self.obj_frame_model_yolo_structure
        self.obj_structure_model_service = StructureFrameYoloService(
            self.obj_frame_model_yolo_structure
        )
        self.obj_stamp_detector = StampDetector(self.obj_structure_model_service)

        # Cấu hình riêng cho dị vật
        self.obj_yolo_foreign_config = YoloDetectObjectConfig(
            path_model=PATH_FILE_MODEL_YOLO_FOREIGN
        )
        self.obj_model_yolo_foreign = ModelYoloObject(self.obj_yolo_foreign_config)

        # Cấu hình riêng cho kiểm tra có, lệch tem (YOLO OBB)
        self.obj_yolo_stamp_alignment_config = YoloDetectObjectConfig(
            path_model=PATH_FILE_MODEL_YOLO_STAMP_ALIGNMENT
        )
        self.obj_model_yolo_obb = ModelYoloOBB(self.obj_yolo_stamp_alignment_config)
        self.obj_stamp_alignment_service = StampAlignmentService(self.obj_model_yolo_obb)
        self.obj_stamp_alignment_detector = StampAlignmentDetector(
            self.obj_stamp_alignment_service
        )

        self.obj_ocr_text_detector = OCRTextDetector()
        self.obj_stamp_reversed_service = StampReversedService(
            yolo_obb=self.obj_model_yolo_obb,
            ocr_service=self.obj_ocr_text_detector.ocr_service,
        )
        self.obj_stamp_reversed_detector = StampReversedDetector(
            self.obj_stamp_reversed_service
        )

        self.obj_foreign_object_patch_core_service = ForeignObjectPatchCoreService(
            self.obj_point_service,
            self.obj_model_yolo_foreign,
        )
        self.obj_foreign_object_detector = ForeignObjectDetector(
            foreign_service=self.obj_foreign_object_patch_core_service
        )
        self.obj_anomaly_point_detector = AnomalyPointDetector(
            anomaly_point_service=self.obj_anomaly_point_patch_core_service
        )

        # Cấu hình kiểm tra màu sắc (CIE2000 Delta E)
        self.obj_color_service = ColorService()
        self.obj_color_detector = ColorDetector(self.obj_color_service)

        # Cấu hình kiểm tra mã vạch Barcode 1D và mã QR 2D
        self.obj_barcode_qr_service = BarcodeQRService()
        self.obj_barcode_detector = BarcodeDetector(self.obj_barcode_qr_service)
        self.obj_qr_detector = QRDetector(self.obj_barcode_qr_service)

        self.obj_judment = Judment(
            {
                "StampItemInspector": self.obj_stamp_detector,
                "StampAlignmentInspector": self.obj_stamp_alignment_detector,
                "StampReversedInspector": self.obj_stamp_reversed_detector,
                "ForeignObjectInspector": self.obj_foreign_object_detector,
                "AnomalyPointInspector": self.obj_anomaly_point_detector,
                "OCRTextInspector": self.obj_ocr_text_detector,
                "ColorItemInspector": self.obj_color_detector,
                "BarcodeItemInspector": self.obj_barcode_detector,
                "QRItemInspector": self.obj_qr_detector,
            }
        )

        self.obj_unet_calib_search_coordinator = None

        # Phần AI detect

        # ---------------------------------------------------------
        # 6. TỰ ĐỘNG MỞ TRÌNH DUYỆT (UI)
        # ---------------------------------------------------------
        def open_browser():
            webbrowser.open("http://127.0.0.1:8000")

        threading.Thread(target=open_browser).start()

        print("..--------------------------------.. init Complete ...----------------------------------.")

    def stop(self) -> None:
        """
        Dừng toàn bộ dịch vụ, giải phóng cổng COM, đóng Camera, ngắt luồng và giải phóng bộ nhớ.
        """
        print("🛑 ....Stopping Service & Releasing Resources....")
        try:
            self.runtime_state.request_stop()
        except Exception as e:
            print(f"[Stop] Lỗi request_stop: {e}")

        if getattr(self, "obj_iai_control", None):
            try:
                self.obj_iai_control.stop_thread_input_handler_stm32()
                self.obj_iai_control.stop_thread_handler_stm32()
            except Exception as e:
                print(f"[Stop] Lỗi dừng IAIControl: {e}")

        if getattr(self, "obj_robot_control", None):
            try:
                self.obj_robot_control.disconnect()
            except Exception as e:
                print(f"[Stop] Lỗi ngắt kết nối RobotControl: {e}")

        if getattr(self, "obj_robot_control", None):
            try:
                self.obj_robot_control.disconnect()
            except Exception as e:
                print(f"[Stop] L?i ng?t k?t n?i RobotControl: {e}")

        if getattr(self, "obj_camera", None):
            try:
                self.obj_camera.release()
            except Exception as e:
                print(f"[Stop] Lỗi giải phóng Camera: {e}")

        if getattr(self, "obj_manager_log", None):
            try:
                self.obj_manager_log.stop_log_thread()
            except Exception as e:
                print(f"[Stop] Lỗi dừng Manager_Log: {e}")

        try:
            import gc

            gc.collect()
            print("🧹 [Memory] Đã thu gom rác bộ nhớ (gc.collect).")
        except Exception:
            pass

    def send_judgment_log(self, message: str) -> None:
        """Gửi log pipeline tới ô log phán định trên giao diện và ghi vào file log hệ thống."""
        self.queue_log_send_client.put(
            {
                "type": "log_Home",
                "message": str(message),
            }
        )
        if getattr(self, "queue_manage_log", None):
            self.queue_manage_log.put(
                {
                    "type": "system",
                    "level": "info",
                    "msg": str(message),
                }
            )

    def set_mode(self, mode: EnumMode):
        with self._lock_mode:
            self._mode = mode

    def get_mode(self) -> EnumMode:
        with self._lock_mode:
            return self._mode

    def notify_config_changed(self, source: str = "") -> None:
        """Thông báo cấu hình sản phẩm (points, law, calibration, choose_product) đã thay đổi từ UI."""
        if getattr(self, "stage_preprocess", None):
            self.stage_preprocess.mark_dirty(source=source)
        else:
            print(
                f"[CONTAINER] Nhận notify_config_changed({source}) nhưng stage_preprocess chưa được gán."
            )

    @property
    def is_tcp_connected(self) -> bool:
        """Kiểm tra trạng thái kết nối mạng TCP socket tới Robot/PLC."""
        if getattr(self, "obj_robot_control", None):
            return self.obj_robot_control.is_connected()
        return False


def create_container():
    return ServiceContainer()
