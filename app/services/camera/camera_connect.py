from pathlib import Path
# import sys
# sys.path.append(str(Path(__file__).resolve().parents[3]))


from app.config import CameraConfig, PATH_FEATUERES_CFG_CAM
import stapipy as st
import cv2
import numpy as np
import threading
import time 
import os

class Camera():

    DISPLAY_RESIZE_FACTOR = 1.0
    ERRO_TIMEOUT = "ErroTimeOutCapture"
    TIMEOUT_WAIT_NEW_FRAME  = 10     # số giây để reconnect lại
    TIMEDELAY_TASK_THREAD_CAMERA = 0.1

    def __init__(self):

        self.config = CameraConfig()
        self._lock_config = threading.Lock()

        self.camera_lost = False

        self.lock_connect =  threading.Lock()
        self._isConnect = False
        self._last_time = time.time()
        
        self.open_task_camera = True
        self.thread_camera = None
     
        self.st_device = None
        self.st_datastream = None
        self._image = None         # Image buffer
        self._lock = threading.Lock()

        self._lock_capture = threading.Lock()
        self._capture_event  = threading.Event()
        self._capture_one = False    # Flag to capture one image
        self._captured_image = None   # Captured image buffer

        # Viết chụp ảnh triger bằng Camera
        self.nodemap = None
        self.trigger_software = None
        self.trigger_mode = False

        self._running_watchdog = True
        self._reconnect_lock = threading.Lock()
        self.init()
        self._start_watchdog()

        
    def display_captured_image(self, img, window_name="Captured Image", wait_time=2000):
        """
        Hiển thị ảnh sau khi chụp bằng OpenCV.
        :param img: Khung hình (numpy array) cần hiển thị.
        :param window_name: Tên của cửa sổ hiển thị.
        :param wait_time: Thời gian hiển thị ảnh tính bằng mili-giây (ms). 
                          Nếu truyền 0, cửa sổ sẽ giữ nguyên cho đến khi nhấn phím bất kỳ.
        """
        if img is None:
            print("Không có ảnh để hiển thị (img is None)")
            return False
        
        try:
            # Tạo cửa sổ có thể thay đổi kích thước nếu ảnh quá lớn
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.imshow(window_name, img)
            
            print(f"Đang hiển thị ảnh trong {wait_time/1000} giây...")
            cv2.waitKey(wait_time)
            
            # Đóng cửa sổ sau khi hết thời gian chờ
            cv2.destroyWindow(window_name)
            return True
        except Exception as e:
            print("Lỗi khi hiển thị ảnh:", e)
            return False
    def refesh_data(self):
            
            self.camera_lost = False
            self.lock_connect =  threading.Lock()
            self._isConnect = False

            self._last_time = time.time()
            self.open_task_camera = True
            self.thread_camera = None
        
            self.st_device = None
            self.st_datastream = None
            self._image = None         # Image buffer
            self._lock = threading.Lock()

            self._lock_capture = threading.Lock()
            self._capture_event  = threading.Event()
            self._capture_one = False    # Flag to capture one image
            self._captured_image = None   # Captured image buffer


    def init(self):
        try:
            print("--------- Init Camera -------")
            st.initialize()
            st_system = st.create_system()
            self.st_device = st_system.create_first_device()
            self.st_datastream = self.st_device .create_datastream()
            print('Device=', self.st_device.info.display_name)
            # nodemap = self.st_device.remote_port.nodemap  #cu
            self.nodemap = self.st_device.remote_port.nodemap
            if os.path.exists(PATH_FEATUERES_CFG_CAM):
                print("Tìm thấy file mô hình")
                featurebag = st.create_featurebag()
                featurebag.store_file_to_bag(PATH_FEATUERES_CFG_CAM)
                featurebag.load(self.nodemap, verify=True)
                self.featurebag = featurebag
                self.config = CameraConfig.from_feature_file(PATH_FEATUERES_CFG_CAM)
                print("Camera config loaded compelete")
                self.create_task_camera()
                self.camera_lost = False
                print("--------- Init Camera thành công -------")
            else:
                print("Không tìm thấy file mô hình features.cfg")
                print("--------- Init Camera thất bại -------")
                self.camera_lost = True
                self.set_is_connect(False)
        except Exception as e:
            self.camera_lost = True
            self.set_is_connect(False)
            print(f"--------- Init Camera thất bại: {e} -------")

    def _set_float_node(self, node_name, value):
        """Ghi giá trị float vào node camera.

        Input: tên node và giá trị số.
        Output: không trả về giá trị.
        Errors: exception từ SDK nếu node không tồn tại hoặc không writable.
        """
        node = st.PyIFloat(self.nodemap.get_node(node_name))
        node.value = value

    def _read_float_node(self, node_name):
        """Đọc giá trị float từ node camera.

        Input: tên node cần đọc.
        Output: giá trị float hiện tại của node.
        Errors: exception từ SDK nếu node không tồn tại hoặc không đọc được.
        """
        return float(st.PyIFloat(self.nodemap.get_node(node_name)).value)

    def _read_enum_node(self, node_name):
        """Đọc symbolic value của node enumeration camera.

        Input: tên node enumeration.
        Output: tên symbolic hiện tại.
        Errors: exception từ SDK nếu node không tồn tại hoặc không đọc được.
        """
        enumeration = st.PyIEnumeration(self.nodemap.get_node(node_name))
        entry = enumeration.current_entry
        return str(entry.symbolic_value if entry else enumeration.value)

    def sync_config_from_camera(self):
        """Đồng bộ cấu hình runtime từ nodemap đã nạp từ features.cfg.

        Input: nodemap camera đã được khởi tạo.
        Output: không trả về; cập nhật ``self.config`` tại chỗ.
        Errors: node không hỗ trợ sẽ giữ giá trị mặc định tương ứng.
        """
        if self.nodemap is None:
            return
        float_fields = {
            "acquisition_frame_rate": "AcquisitionFrameRate",
            "exposure_time": "ExposureTime",
            "gain": "Gain",
            "gamma": "Gamma",
            "black_level": "BlackLevel",
        }
        enum_fields = {
            "exposure_auto": "ExposureAuto",
            "trigger_mode": "TriggerMode",
            "trigger_selector": "TriggerSelector",
            "balance_white_auto": "BalanceWhiteAuto",
        }
        for field, node_name in float_fields.items():
            try:
                setattr(self.config, field, self._read_float_node(node_name))
            except Exception as error:
                print(f"[CameraConfig] Read FAILED: {node_name} - {error}")
        for field, node_name in enum_fields.items():
            try:
                setattr(self.config, field, self._read_enum_node(node_name))
            except Exception as error:
                print(f"[CameraConfig] Read FAILED: {node_name} - {error}")
        for color, field in (
            ("Red", "balance_ratio_red"),
            ("Green", "balance_ratio_green"),
            ("Blue", "balance_ratio_blue"),
        ):
            try:
                self.set_enumeration("BalanceRatioSelector", color)
                setattr(self.config, field, self._read_float_node("BalanceRatio"))
            except Exception as error:
                print(f"[CameraConfig] Read FAILED: BalanceRatio {color} - {error}")

    def apply_config(self):
        """Áp dụng cấu hình hiện tại vào các node camera.

        Input: không có, sử dụng ``self.config``.
        Output: dictionary gồm trạng thái và lỗi theo từng node.
        Errors: lỗi node được thu thập trong ``errors`` để không dừng camera.
        """
        if self.nodemap is None:
            return {"applied": False, "errors": ["Camera nodemap is unavailable"]}
        node_values = {
            "AcquisitionFrameRate": self.config.acquisition_frame_rate,
            "ExposureTime": self.config.exposure_time,
            "Gain": self.config.gain,
            "ExposureAuto": self.config.exposure_auto,
            "TriggerMode": self.config.trigger_mode,
            "TriggerSelector": self.config.trigger_selector,
            "Gamma": self.config.gamma,
            "BlackLevel": self.config.black_level,
        }
        errors = []
        for node_name, value in node_values.items():
            try:
                print(f"[CameraConfig] Sending {node_name} = {value}")
                if isinstance(value, str):
                    self.set_enumeration(node_name, value)
                else:
                    self._set_float_node(node_name, value)
                print(f"[CameraConfig] Sent OK: {node_name}")
            except Exception as error:
                print(f"[CameraConfig] Send FAILED: {node_name} - {error}")
                errors.append(f"{node_name}: {error}")
        try:
            print(f"[CameraConfig] Sending BalanceWhiteAuto = {self.config.balance_white_auto}")
            self.set_enumeration("BalanceWhiteAuto", self.config.balance_white_auto)
            print("[CameraConfig] Sent OK: BalanceWhiteAuto")
            if self.config.balance_white_auto.lower() == "off":
                for color, ratio in (
                    ("Red", self.config.balance_ratio_red),
                    ("Green", self.config.balance_ratio_green),
                    ("Blue", self.config.balance_ratio_blue),
                ):
                    print(f"[CameraConfig] Sending BalanceRatio {color} = {ratio}")
                    self.set_enumeration("BalanceRatioSelector", color)
                    self._set_float_node("BalanceRatio", ratio)
                    print(f"[CameraConfig] Sent OK: BalanceRatio {color}")
        except Exception as error:
            print(f"[CameraConfig] Send FAILED: WhiteBalance - {error}")
            errors.append(f"WhiteBalance: {error}")
        print(f"[CameraConfig] Completed: applied={not errors}, errors={len(errors)}")
        return {"applied": not errors, "errors": errors}

    def get_config(self):
        """Lấy cấu hình camera hiện tại.

        Input: không có.
        Output: dictionary JSON-compatible.
        Errors: không phát sinh.
        """
        with self._lock_config:
            return self.config.to_dict()

    def get_device_info(self) -> dict:
        """Lấy thông tin phần cứng thiết bị camera ở chế độ chỉ đọc (Read-only).

        Returns:
            dict: Thông tin model, serial, độ phân giải, kết nối, payload.
        """
        is_connected = self.get_is_connect()
        device_name = "OMRON Sentech USB3 Camera"
        device_model = "STC-MCS510U3V"
        serial_number = "Unknown"
        vendor = "OMRON SENTECH CO., LTD."
        width = 2448
        height = 2048
        payload_size = 0
        pixel_format = "BayerRG8"
        interface_type = "USB3 Vision (U3V)"

        if getattr(self, "st_device", None) is not None:
            try:
                dev_info = getattr(self.st_device, "info", None)
                if dev_info:
                    device_name = getattr(dev_info, "display_name", device_name) or device_name
                    device_model = getattr(dev_info, "model", device_model) or device_model
                    serial_number = getattr(dev_info, "serial_number", serial_number) or serial_number
                    vendor = getattr(dev_info, "vendor", vendor) or vendor
            except Exception as e:
                print(f"[CameraInfo] Error reading st_device.info: {e}")

        if getattr(self, "nodemap", None) is not None:
            try:
                node_model = self.nodemap.get_node("DeviceModelName")
                if node_model:
                    val = str(st.PyIString(node_model).value)
                    if val:
                        device_model = val
            except Exception:
                pass
            try:
                node_serial = self.nodemap.get_node("DeviceSerialNumber")
                if node_serial:
                    val = str(st.PyIString(node_serial).value)
                    if val:
                        serial_number = val
            except Exception:
                pass
            try:
                node_w = self.nodemap.get_node("Width")
                if node_w:
                    width = int(st.PyIInteger(node_w).value)
            except Exception:
                pass
            try:
                node_h = self.nodemap.get_node("Height")
                if node_h:
                    height = int(st.PyIInteger(node_h).value)
            except Exception:
                pass
            try:
                node_payload = self.nodemap.get_node("PayloadSize")
                if node_payload:
                    payload_size = int(st.PyIInteger(node_payload).value)
            except Exception:
                pass
            try:
                node_pix = self.nodemap.get_node("PixelFormat")
                if node_pix:
                    enum_node = st.PyIEnumeration(node_pix)
                    entry = enum_node.current_entry
                    pixel_format = str(entry.symbolic_value if entry else enum_node.value)
            except Exception:
                pass

        with self._lock:
            if self._image is not None and hasattr(self._image, "shape"):
                h, w = self._image.shape[:2]
                if w > 0 and h > 0:
                    width = w
                    height = h

        if payload_size == 0 and width > 0 and height > 0:
            payload_size = width * height

        status_text = "Đang kết nối (Online)" if is_connected else "Mất kết nối (Offline)"

        return {
            "connected": is_connected,
            "status": status_text,
            "device_name": device_name,
            "device_model": device_model,
            "serial_number": serial_number,
            "vendor": vendor,
            "resolution": f"{width} x {height} px",
            "width": width,
            "height": height,
            "payload_size": f"{payload_size:,} bytes" if payload_size else "N/A",
            "pixel_format": pixel_format,
            "interface": interface_type,
        }

    def apply_config_values(self, values):
        """Áp dụng tạm thời field vận hành mà chưa lưu file.

        Input: dictionary field vận hành.
        Output: cấu hình tạm thời và kết quả áp dụng node.
        Errors: ``ValueError`` nếu payload không hợp lệ.
        """
        with self._lock_config:
            print(f"[CameraConfig] Apply request: {values}")
            previous_config = CameraConfig(**self.config.to_dict())
            temporary_config = CameraConfig(**self.config.to_dict())
            temporary_config.update_operator_values(values)
            self.config = temporary_config
            try:
                apply_result = self.apply_config()
                if not apply_result["applied"]:
                    self.config = previous_config
                    self.reload_feature_file()
                    return {
                        "config": previous_config.to_dict(),
                        "apply_result": apply_result,
                        "rolled_back": True,
                    }
                result = {"config": temporary_config.to_dict(), "apply_result": apply_result}
            finally:
                if self.config is temporary_config:
                    self.config = previous_config
            return result

    def save_config_values(self, values):
        """Cập nhật, lưu file và áp dụng cấu hình vận hành.

        Input: dictionary field vận hành.
        Output: cấu hình đã lưu và kết quả áp dụng node.
        Errors: ``ValueError`` hoặc ``OSError`` nếu cấu hình không hợp lệ.
        """
        with self._lock_config:
            print(f"[CameraConfig] Save request: {values}")
            previous_config = CameraConfig(**self.config.to_dict())
            feature_path = Path(PATH_FEATUERES_CFG_CAM)
            previous_feature = feature_path.read_bytes()
            self.config.update_operator_values(values)
            apply_result = self.apply_config()
            if not apply_result["applied"]:
                self.config = previous_config
                self.reload_feature_file()
                return {
                    "config": previous_config.to_dict(),
                    "apply_result": apply_result,
                    "feature_save_result": {"saved": False, "error": "Apply failed; configuration restored"},
                    "rolled_back": True,
                }
            save_result = self.save_feature_config()
            if not save_result["saved"]:
                feature_path.write_bytes(previous_feature)
                self.config = previous_config
                self.reload_feature_file()
                return {
                    "config": previous_config.to_dict(),
                    "apply_result": apply_result,
                    "feature_save_result": save_result,
                    "rolled_back": True,
                }
            return {
                "config": self.config.to_dict(),
                "apply_result": apply_result,
                "feature_save_result": save_result,
            }

    def reload_feature_file(self):
        """Nạp lại features.cfg để khôi phục camera sau thao tác thất bại.

        Input: không có; sử dụng ``PATH_FEATUERES_CFG_CAM``.
        Output: không trả về giá trị.
        Errors: lỗi SDK được ghi log và giữ nguyên cấu hình runtime cũ.
        """
        try:
            featurebag = st.create_featurebag()
            featurebag.store_file_to_bag(PATH_FEATUERES_CFG_CAM)
            featurebag.load(self.nodemap, verify=True)
            self.featurebag = featurebag
            self.config = CameraConfig.from_feature_file(PATH_FEATUERES_CFG_CAM)
            print("[CameraConfig] Rolled back from features.cfg")
        except Exception as error:
            print(f"[CameraConfig] Rollback FAILED: {error}")

    def save_feature_config(self):
        """Ghi trực tiếp nodemap hiện tại vào file features.cfg.

        Input: không có; sử dụng nodemap camera đã được áp dụng cấu hình.
        Output: dictionary trạng thái lưu file feature.
        Errors: lỗi SDK được trả về trong ``error`` thay vì làm mất trạng thái.
        """
        if self.nodemap is None:
            print("[CameraConfig] Feature save FAILED: nodemap unavailable")
            return {"saved": False, "error": "Camera nodemap is unavailable"}
        try:
            featurebag = st.create_featurebag()
            featurebag.store_nodemap_to_bag(self.nodemap)
            featurebag.save_to_file(PATH_FEATUERES_CFG_CAM)
            self.featurebag = featurebag
            print(f"[CameraConfig] Feature file saved: {PATH_FEATUERES_CFG_CAM}")
            return {"saved": True, "path": PATH_FEATUERES_CFG_CAM}
        except Exception as error:
            print(f"[CameraConfig] Feature save FAILED: {error}")
            return {"saved": False, "error": str(error)}

    def reset_config(self):
        """Đọc lại cấu hình đã lưu và áp dụng vào camera.

        Input: không có.
        Output: cấu hình sau reset và kết quả áp dụng node.
        Errors: ``ValueError`` nếu file JSON không hợp lệ.
        """
        with self._lock_config:
            self.featurebag = st.create_featurebag()
            self.featurebag.store_file_to_bag(PATH_FEATUERES_CFG_CAM)
            self.featurebag.load(self.nodemap, verify=True)
            self.config = CameraConfig.from_feature_file(PATH_FEATUERES_CFG_CAM)
            return {"config": self.config.to_dict(), "apply_result": {"applied": True, "errors": []}}
            

    def enable_software_trigger(self):
        try:
            try:
                self.set_enumeration(
                    "TriggerSelector",
                    "FrameStart"
                )
            except Exception:
                self.set_enumeration(
                    "TriggerSelector",
                    "ExposureStart"
                )
            self.set_enumeration(
                "TriggerMode",
                "On"
            )
            self.set_enumeration(
                "TriggerSource",
                "Software"
            )
            self.trigger_software = st.PyICommand(
                self.nodemap.get_node(
                    "TriggerSoftware"
                )
            )
            self.trigger_mode = True
            print("Software Trigger Enabled")
            return True
        except Exception as e:
            print("Enable Trigger Error:", e)
            return False 
        
    def disable_software_trigger(self):
        try:
            if not self.nodemap:
                self.trigger_mode = False
                return
            self.set_enumeration(
                "TriggerMode",
                "Off"
            )
            self.trigger_mode = False
            print("Software Trigger Disabled")
        except Exception as e:
            print("Disable Trigger Error:", e)


    def send_trigger(self):
        if not self.trigger_mode:
            return False
        try:
            self.trigger_software.execute()
            return True
        except Exception as e:
            print("Trigger Error:", e)
            return False
        
    def set_enumeration(self, enum_name, entry_name):
        if not self.nodemap:
            return
        node = self.nodemap.get_node(enum_name)
        if not node:
            return
        enum_node = st.PyIEnumeration(node)
        entry_node = st.PyIEnumEntry(
            enum_node[entry_name]
        )
        enum_node.set_entry_value(entry_node)

    def get_is_connect(self):
        with self.lock_connect:
            return self._isConnect   

    def set_is_connect(self, value: bool):
        with self.lock_connect:
            self._isConnect = value


    def create_task_camera(self):
        self.open_task_camera = True
        self.thread_camera = threading.Thread(target=self.run, daemon=True, name="CameraWorker")
        self.thread_camera.start()

    def _start_watchdog(self):
        """Khởi động luồng giám sát định kỳ tự phục hồi kết nối camera."""
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
            name="CameraWatchdog"
        )
        self._watchdog_thread.start()
        print("✅ [Camera] Đã khởi động luồng CameraWatchdog tự phục hồi.")

    def _watchdog_loop(self):
        """Luồng giám sát camera định kỳ. Nếu mất kết nối hoặc mất frame > 10s sẽ tự động tái kết nối."""
        while self._running_watchdog:
            try:
                time.sleep(2.0)
                if not self.open_task_camera or not self._running_watchdog:
                    continue
                thread_dead = bool(self.thread_camera and not self.thread_camera.is_alive())
                if self.camera_lost or not self.get_is_connect() or thread_dead:
                    if self._reconnect_lock.acquire(blocking=False):
                        try:
                            print("🔄 [Camera Watchdog] Phát hiện camera mất kết nối/frame, đang thử kết nối lại...")
                            self._auto_reconnect()
                        finally:
                            self._reconnect_lock.release()
            except Exception as e:
                print(f"⚠️ [Camera Watchdog] Lỗi giám sát: {e}")
                time.sleep(2.0)

    def _cleanup_camera_resources(self):
        """Dọn dẹp tài nguyên phần cứng camera phục vụ cho reconnect hoặc shutdown."""
        try:
            self.open_task_camera = False
            if self.thread_camera and self.thread_camera.is_alive():
                self.thread_camera.join(timeout=2.0)
            self.thread_camera = None
        except Exception as e:
            print("[Camera] Stop thread error:", e)

        try:
            if self.st_datastream:
                try:
                    self.st_datastream.unregister_callback()
                except Exception:
                    pass
                try:
                    self.st_datastream.stop_acquisition()
                except Exception:
                    pass
                self.st_datastream = None
        except Exception as e:
            print("[Camera] Datastream cleanup error:", e)

        try:
            if self.st_device:
                try:
                    self.st_device.acquisition_stop()
                except Exception:
                    pass
                self.st_device = None
        except Exception as e:
            print("[Camera] Device cleanup error:", e)

        try:
            st.terminate()
            print("[Camera] StApi terminated")
        except Exception as e:
            print("[Camera] StApi terminate error:", e)

        try:
            self.disable_software_trigger()
        except Exception:
            pass

        self._image = None
        self._captured_image = None
        self._capture_one = False
        self._capture_event.clear()

    def _auto_reconnect(self):
        """Thực hiện chu trình dọn dẹp và nạp lại cấu hình camera."""
        try:
            self.set_is_connect(False)
            self._cleanup_camera_resources()
            time.sleep(1.0)
            self.refesh_data()
            self.init()
            if self.get_is_connect():
                print("✅ [Camera Watchdog] Tự động kết nối lại camera THÀNH CÔNG!")
            else:
                print("⏳ [Camera Watchdog] Chưa kết nối lại được, sẽ thử lại sau...")
        except Exception as e:
            print(f"❌ [Camera Watchdog] Lỗi trong quá trình reconnect: {e}")

    def release(self):
        """Giải phóng camera hoàn toàn khi tắt ứng dụng."""
        print("--Release camera -- ")
        self._running_watchdog = False
        self._cleanup_camera_resources()
        print("---Release camera thành công -- ")


    def capture_once(self, timeout=1):
        with self._lock_capture:
            self._captured_image = None
            self._capture_one = True
        self._capture_event.clear()
        if self.trigger_mode:
            if not self.send_trigger():
                self._capture_one = False
                return False, "TriggerError"
        ok = self._capture_event.wait(timeout)
        if not ok:
            self._capture_one = False
            print("Capture Error image timeout")
            return False, Camera.ERRO_TIMEOUT
        return True, self._captured_image
    


    def capture_image_path(self, path, timeout=1):
        """Trả về True nếu chụp & lưu ảnh thành công"""
        status_capture, img = self.capture_once(timeout=timeout)
        if not status_capture:
            return False
        if img is None:
            print("Capture error: image is None")
            return False
        try:
            if os.path.isfile(path):
                os.remove(path)
            ok = cv2.imwrite(path, img)
            if not ok:
                print("Save image failed:", path)
                return False
        except Exception as e:
            print("Exception while saving image:", e)
            return False
        return True



    @property
    def image(self):
        with self._lock:
            if self._image is not None:
                return self._image.copy()
            return None
    

    def datastream_callback(self, handle=None, context=None):
        """
        Callback to handle events from DataStream.
        :param handle: handle that trigger the callback.
        :param context: user data passed on during callback registration.
        """
        st_datastream = handle.module
        if st_datastream:
            with st_datastream.retrieve_buffer() as st_buffer:
                # Check if the acquired data contains image data.
                if st_buffer.info.is_image_present:
                    # Create an image object.
                    st_image = st_buffer.get_image()

                    # Check the pixelformat of the input image.
                    pixel_format = st_image.pixel_format
                    pixel_format_info = st.get_pixel_format_info(pixel_format)

                    # Only mono or bayer is processed.
                    if not(pixel_format_info.is_mono or
                           pixel_format_info.is_bayer):
                        return
                    # Get raw image data.
                    data = st_image.get_image_data()
                    # Perform pixel value scaling if each pixel component is
                    # larger than 8bit. Example: 10bit Bayer/Mono, 12bit, etc.
                    if pixel_format_info.each_component_total_bit_count > 8:
                        nparr = np.frombuffer(data, np.uint16)
                        division = pow(2, pixel_format_info
                                       .each_component_valid_bit_count - 8)
                        nparr = (nparr / division).astype('uint8')
                    else:
                        nparr = np.frombuffer(data, np.uint8)

                    # Process image for display.
                    nparr = nparr.reshape(st_image.height, st_image.width, 1)

                    # Perform color conversion for Bayer.
                    if pixel_format_info.is_bayer:
                        bayer_type = pixel_format_info.get_pixel_color_filter()
                        if bayer_type == st.EStPixelColorFilter.BayerRG:
                            nparr = cv2.cvtColor(nparr, cv2.COLOR_BAYER_RG2RGB)
                        elif bayer_type == st.EStPixelColorFilter.BayerGR:
                            nparr = cv2.cvtColor(nparr, cv2.COLOR_BAYER_GR2RGB)
                        elif bayer_type == st.EStPixelColorFilter.BayerGB:
                            nparr = cv2.cvtColor(nparr, cv2.COLOR_BAYER_GB2RGB)
                        elif bayer_type == st.EStPixelColorFilter.BayerBG:
                            nparr = cv2.cvtColor(nparr, cv2.COLOR_BAYER_BG2RGB)
                    # Resize image and store to self._image.
                    nparr = cv2.resize(nparr, None,
                                       fx=Camera.DISPLAY_RESIZE_FACTOR,
                                       fy=Camera.DISPLAY_RESIZE_FACTOR)
                    with self._lock:
                        self._image = nparr
                    self._last_time =  time.time()
                    self.set_is_connect(True)
                    with self._lock_capture:
                        if self._capture_one:
                            self._captured_image = nparr.copy()
                            self._capture_one = False
                            self._capture_event.set()


    def run(self):
        cb_func = self.datastream_callback
        self.st_datastream.register_callback(cb_func)
        self.st_datastream.start_acquisition()
        self.st_device.acquisition_start()
        print("---Camera thread started----")
        while self.open_task_camera:
            if time.time() - self._last_time > Camera.TIMEOUT_WAIT_NEW_FRAME:
                print("Camera LOST")
                self.set_is_connect(False)
                self.camera_lost = True
                break
            time.sleep(Camera.TIMEDELAY_TASK_THREAD_CAMERA)


    def print_device_info(self):
        """In thông tin phần cứng thiết bị camera ra console (debug)."""
        if self.st_device is None:
            print("Device is None (Camera not connected)")
            return
        info = self.st_device.info
        print("===== DEVICE INFO =====")
        print("Display name        :", getattr(info, "display_name", ""))
        print("Model               :", getattr(info, "model", ""))
        print("Vendor              :", getattr(info, "vendor", ""))
        print("Serial number       :", getattr(info, "serial_number", ""))
        print("Device ID           :", getattr(info, "device_id", ""))
        print("TL type             :", getattr(info, "tl_type", ""))
        print("User defined name   :", getattr(info, "user_defined_name", ""))
        print("Version             :", getattr(info, "version", ""))
        print("Access status       :", getattr(info, "access_status", ""))
        print("Timestamp frequency :", getattr(info, "timestamp_frequency", ""))


    def get_device_info_dict(self):
        if self.st_device is None:
            return None
        info = self.st_device.info
        return {
            "display_name": info.display_name,
            "model": info.model,
            "vendor": info.vendor,
            "serial_number": info.serial_number,
            "device_id": info.device_id,
            "tl_type": info.tl_type,
            "user_defined_name": info.user_defined_name,
            "version": info.version,
            "access_status": info.access_status,
            "timestamp_frequency": info.timestamp_frequency,
        }
    

    def capture_image_trigger(self, folder_path, image_name, timeout=2):
        """
        Bật trigger -> chụp 1 ảnh -> lưu ảnh -> tắt trigger
        Return:
            (status, image, path_or_error)
            Success:
                True, img, image_path
            Fail:
                False, None, error_message
        """
        try:
            os.makedirs(folder_path, exist_ok=True)
            image_path = os.path.join(
                folder_path,
                image_name
            )
            print("Enable Trigger...")
            status_open_trigger = self.enable_software_trigger()
            if not status_open_trigger:
                return False, None, "EnableTriggerFail"
            with self._lock_capture:
                self._captured_image = None
                self._capture_one = True
            self._capture_event.clear()
            print("Send Trigger...")
            status_send_trigger = self.send_trigger()
            if not status_send_trigger:
                self._capture_one = False
                return False, None, "SendTriggerFail"
            ok = self._capture_event.wait(timeout)
            if not ok:
                self._capture_one = False
                return False, None, Camera.ERRO_TIMEOUT
            if self._captured_image is None:
                return False, None, "ImageIsNone"
            img = self._captured_image.copy()
            if os.path.isfile(image_path):
                os.remove(image_path)
            save_status = cv2.imwrite(image_path, img)
            if not save_status:
                return False, None, "SaveImageFail"
            print("Save Image OK:", image_path)
            return True, img, image_path
        except Exception as e:
            print("capture_image_trigger error:", e)
            return False, None, str(e)
        finally:
            try:
                self.disable_software_trigger()
                print("Disable Trigger OK")
            except Exception as e:
                print("Disable Trigger Error:", e)
        

    
    # def open_trigger(self):
    #     # Ham nay vi du để bật mode trigger
    #     status_open_trigger = self.enable_software_trigger()
    #     send_trigger = self.send_trigger()
    #     ok, img = self.capture_once(timeout=2)
    #     print("status_open_trigger",status_open_trigger,"send_trigger",send_trigger)
    #     if ok:
    #         cv2.imwrite("test.jpg", img)

# c1 = Camera()
# while True:
#     img = c1.image
#     if img is not None:
#         # c1.open_trigger()
#         cv2.imshow("image", img)
#     if c1.camera_lost:
#         print("Main: reconnect camera")
#         c1.release()
#         time.sleep(1)
#         c1.refesh_data()
#         c1.init()
#     if cv2.waitKey(1) & 0xFF == 27:
#         break
