

import base64
import cv2
import numpy as np
import threading
import time
from queue import Queue

from app.utils import Folder
# from app.services.product import ChooseProduct
# from app.services.product import ProductManager
from app.services.calculate_the_dimensions.handler_aggregator import ProductAggregator
from app.services.calculate_the_dimensions.handler_face import (
    FaceHandlers,
    FrameHandlers,
)
from app.services.calculate_the_dimensions.handler_model import ModelHandler


# from app.utils import obj_queue,name_queue_process_capture,name_queue_data_client,datatype_Home

class HandlerWorkDetect:
    def __init__(self,Choose_Product : ChooseProduct,Manager_Product : ProductManager, obj_handler_calibration = None,queue_data_send_client:Queue=None,queue_process_capture:Queue=None,type_data_home=None,path_product_model=None):
        self.queue_data_send_client = queue_data_send_client
        self.queue_process_capture =  queue_process_capture
        self.type_data_home  = type_data_home
        self.path_product_model =  path_product_model
        
       
        self.Choose_Product  = Choose_Product
        self.Manager_Product =  Manager_Product

        self.cout_thread =  0 # ĐẾM SỐ THREAD ĐANG MỞ HIỆN TẠI ĐỂ KIỂM SOÁT THREAD
        self.open_thread  = False
        self.thread_task = None

        self.choose_product_current = None
        self.data_regulation = None
        self.count =  0   # dem so diem can xet
    
        self._lock = threading.Lock()
        self._start_detect = False

        self.obj_ModelHandler = None
        self.obj_Aggregator = None

        self.obj_handler_calibration = obj_handler_calibration
        self.Init()

  

        
    @property
    def start_detect(self):
        with self._lock:
            return self._start_detect

    # ===== SET =====
    @start_detect.setter
    def start_detect(self, value: bool):
        with self._lock:
            self._start_detect = value


    def Init(self):
        print("--- Init detect Model---")
        status_Check_file,message = Folder.check_file(self.path_product_model)
        if  not status_Check_file :
            print("Đường dẫn Mô hình không tồn tại.")
            raise FileNotFoundError(message)
        self.obj_ModelHandler = ModelHandler(self.path_product_model)
        self.obj_Aggregator =  ProductAggregator()
        self.start_thread_inference()


    def update_product_if_changed(self):
        new_product = self.Choose_Product.get_choose_product_pick()
        if new_product != self.choose_product_current:
            status, data,cout, error = self.Manager_Product.get_data_regulation_by_product_id(new_product)
            if status:
                self.choose_product_current = new_product
                self.data_regulation = data
                self.count = cout
                print("status",status,"data",data,"count",cout,"error",error)
                print("Đã cập nhật regulation mới. Do thay đổi sản phẩm đã chọn")
            print("Lỗi dữ liệu regualtion",error)

    def task_work_detect(self):
        print("---Bắt đầu mở luồng nhận diện---")
        while self.open_thread_inference:
            if self.start_detect:
                self.start_detect = False
                self.update_product_if_changed()
                for index in range(0,self.count):
                    frame = self.queue_process_capture.get() # Sau 10s mà không nhận được ảnh thì cho ảnh lỗi và quay về lại gốc
                    self.process_multi_thread(index,self.data_regulation[f"{index}"],frame)
                self.cout_thread = 0 #ChO Bien nay  bang 0 de
            time.sleep(0.01)
        
                        
    def worker_judget(self, index, arr_regualtion, img):
            if img is not None:
                polygon = self.obj_ModelHandler.get_polygon(img)
                frame = FrameHandlers(img, polygon, arr_regualtion,convert_mm = getattr(self.obj_handler_calibration, "calibration", 1.0) if self.obj_handler_calibration else 1.0)
                status_judment, arr_line, img = frame.judment_frame()
                print("index", index, "count", self.count)
                final_status = self.obj_Aggregator.add_frame(
                    index=index,
                    status_frame=status_judment,
                    length=self.count
                )
                # ==========================
                # 🔥 CONVERT DỮ LIỆU Ở ĐÂY
                # ==========================

                # Convert numpy array -> list
                if isinstance(arr_line, np.ndarray):
                    arr_line = arr_line.tolist()

                # Convert image -> base64
                _, buffer = cv2.imencode('.jpg', img)
                img_base64 = base64.b64encode(buffer).decode('utf-8')

                # ==========================

                if final_status is None:
                    data_send = {self.type_data_home:{
                        "index": index,
                        "arr_line": arr_line,
                        "img": img_base64,"judment_frame":status_judment
                    }}
                    self.queue_data_send_client.put(data_send)
                    return
                self.start_detect = True
                if final_status:
                    print("✔️ PRODUCT OK")
                    data_send = {self.type_data_home:{
                        "index": index,
                        "arr_line": arr_line,
                        "judment": True,
                        "img": img_base64,
                        "judment_frame":status_judment
                    }}
                else:
                    print("❌ PRODUCT NG")
                    data_send = {self.type_data_home:{
                        "index": index,
                        "arr_line": arr_line,
                        "judment": False,
                        "img": img_base64,
                        "judment_frame":status_judment
                    }}
                self.queue_data_send_client.put(data_send)
            return None
            

    def process_multi_thread(self,index,arr_regualtion,img):
        """Hàm này dùng để tạo luồng xử lý phán định sản phẩm trong đa luồng."""
        print(f" Mở luồng thứ {self.cout_thread}")
        self.cout_thread += 1
        t = threading.Thread(
            target= self.worker_judget,name=f"judment_{index}",
            args=(index,arr_regualtion,img),
            daemon=True 
        )
        t.start()     


    def start_thread_inference(self):
        self.open_thread_inference =  True
        self.thread_task = threading.Thread( target= self.task_work_detect, daemon = True)
        self.thread_task.start()
    


   


# import cv2
# import time
# import threading

# class ImageQueueTester:
#     def __init__(self, handler, interval =2,image_path=None):
#         """
#         handler     : instance HandlerWorkDetect
#         queue       : queue object (obj_queue)
#         queue_name  : tên queue (name_queue_process_capture)
#         image_path  : đường dẫn ảnh test
#         interval    : thời gian push (giây)
#         """
#         self.handler = handler
#         self.queue = obj_queue
#         self.queue_name = name_queue_process_capture
#         self.interval = interval

#         # self.img = cv2.imread(image_path)
#         # if self.img is None:
#         #     raise ValueError("Không load được ảnh test")

#         self._running = False
#         self._thread = None
#         self.start()
#     # ==========================
#     # THREAD LOOP
#     # ==========================
#     def _run(self):
#         print("--- Bắt đầu luồng push ảnh ---")

#         while self._running:
#             # self.queue.put(self.queue_name, self.img.copy())

#             print("Đã push 1 ảnh vào queue")
#             time.sleep(self.interval)

#         print("--- Dừng luồng push ảnh ---")
#     # ==========================
#     # START
#     # ==========================
#     def start(self):
#         if self._running:
#             return
#         self.handler.start_detect = True
#         self._running = True
#         self._thread = threading.Thread(target=self._run, daemon=True)
#         self._thread.start()
#     # ==========================
#     # STOP
#     # ==========================
#     def stop(self):
#         self._running = False
#         if self._thread:
#             self._thread.join()


# c1 = HandlerCalibration()
# H1 = HandlerWorkDetect(c1)
# tester = ImageQueueTester(
#     handler=H1,
#     queue=obj_queue,
#     queue_name = name_queue_process_capture,
#     image_path=None,
#     interval=2
# )
# tester.start()
## tester.stop()