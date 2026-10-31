
import queue
import threading
import time
from app.config import IAIConfig, ModeState
from typing import Any

class IAIControl:
    def __init__(
        self,
        serial_manager: Any = None,
        config: IAIConfig | None = None
    ):
        """Khởi tạo bộ điều khiển IAI dùng ManagerSerial bên ngoài hoặc chế độ độc lập/Cobot."""
        self.serial_manager = serial_manager
        self.config = config or IAIConfig()
        if self.serial_manager is not None:
            self.rx_queue = self.serial_manager.subscribe_rx()
            self.command_rx_queue = self.serial_manager.subscribe_rx()
        else:
            self.rx_queue = queue.Queue()
            self.command_rx_queue = queue.Queue()

        self.led_out_red = None
        self.led_out_blue = None
        self.led_out_yellow = None
        self.led_out_btn_reset = None
        self.buzzer_out = None

        self.btn_inp_start = None
        self.btn_inp_reset = None
        self.btn_inp_stop = None
        self.sensor_safety = None
        self.sensor_left_distance = None
        self.sensor_right_distance = None

        self.lock_btn_start = threading.Lock()
        self.lock_btn_stop = threading.Lock()
        self.lock_btn_reset = threading.Lock()
        self.lock_sensor_safety = threading.Lock()
        self.lock_sensor_left = threading.Lock()
        self.lock_sensor_right = threading.Lock()

        self.allow_button_thread =  True
        self.allow_open_thread = False
        self.show_product_ng  = False
        self.thread = None
        self.button_thread = None
        

        self.last_blink_time = 0
        self.last_blink_time_blue_and_yellow = 0
        self.last_blink_time_red = 0 

        self.has_decidedt  = False  #sản phẩm đã phán định hay chưa mặc định là chưa
        self.lock_has_decidedt  = threading.Lock()
        
        self.is_origin = False
        self.lock_is_origin = threading.Lock()

        
        self.status_current = ModeState.NORMOL
        self.lock_status = threading.Lock()
        
        
        self.is_run = False  # xet xem thiet bi da chay chua, chay roi thi bat len chua chay thi de nguyen
        self.lock_is_run = threading.Lock()
        
        self.ready_run = False  # xet xem thiet bi da chay chua, chay roi thi bat len chua chay thi de nguyen
        self.lock_ready_run = threading.Lock()
        
        self.pause =  False
        self.lock_pause = threading.Lock()

        self.pause_because_sensor_safety =  False
        self.lock_pause_because_sensor_safety = threading.Lock()

        self.pause_because_stop=  False
        self.lock_pause_because_stop = threading.Lock()
    
        self.pause_on_the_way_back_org = False
        self.machine_run = False

        self._prev_state = {
            'led_out_red': None,
            'led_out_blue': None,
            'led_out_yellow': None,
            'led_out_btn_reset': None,
            'buzzer_out': None,
            'btn_inp_start': None,
            'btn_inp_reset': None,
            'btn_inp_stop': None,
            'sensor_safety': None,
            'sensor_left_distance': None,
            'sensor_right_distance': None,
        }

    
    def get_btn_inp_start(self) -> int:
        with self.lock_btn_start:
            return self.btn_inp_start

    def get_btn_inp_stop(self) -> int:
        with self.lock_btn_stop:
            return self.btn_inp_stop

    def get_btn_inp_reset(self) -> int:
        with self.lock_btn_reset:
            return self.btn_inp_reset

    def get_sensor_left_distance(self) -> int:
        with self.lock_sensor_left:
            return self.sensor_left_distance

    def get_sensor_right_distance(self) -> int:
        with self.lock_sensor_right:
            return self.sensor_right_distance

    def get_sensor_safety(self) -> int:
        with self.lock_sensor_safety:
            return self.sensor_safety
        # Setter
    def set_pause_because_sensor_safety(self, value: bool):
        with self.lock_pause_because_sensor_safety:  # đảm bảo thread-safe
            self.pause_because_sensor_safety= value

    # Getter
    def get_pause_because_sensor_safety(self) -> bool:
        #False la goc true la khong o goc
        with self.lock_pause_because_sensor_safety:
            return self.pause_because_sensor_safety
        
    def set_pause_because_stop(self, value: bool):
        with self.lock_pause_because_stop :
            self.pause_because_stop= value

    # Getter
    def get_pause_because_stop(self) -> bool:
        #False la goc true la khong o goc
        with self.lock_pause_because_stop:
            return self.pause_because_stop
    
    # Setter
    def set_is_origin(self, value: bool):
        with self.lock_is_origin:  # đảm bảo thread-safe
            self.is_origin = value

    # Getter
    def get_is_origin(self) -> bool:
        #False la goc true la khong o goc
        with self.lock_is_origin:
            return self.is_origin

    def can_move_iai(self, action_name: str = "di chuyển") -> bool:
        """Kiểm tra trạng thái di chuyển (độc lập, không phụ thuộc cổng COM)."""
        if self.serial_manager is None:
            return True
        if hasattr(self.serial_manager, "is_running") and not self.serial_manager.is_running():
            return False
        return True

    def set_pause_becuase_ng(self, value: bool):
        with self.lock_pause:  
            self.pause = value

   
    def get_pause_becuase_ng(self) -> bool:
        with self.lock_pause:
            return self.pause

    # ====== SET ======
    def set_status(self, value):
        with self.lock_status:
            self.status_current = value

    def set_is_run(self, value):
        with self.lock_is_run:
            self.is_run = value
            
    def set_ready_run(self, value):
        with self.lock_ready_run:
            self.ready_run = value

    def set_has_decidedt(self, value):
        with self.lock_has_decidedt:
            self.has_decidedt  = value
    # ====== GET ======
    def get_has_decided(self):
        with self.lock_has_decidedt:
            return self.has_decidedt 
    def get_ready_run(self):
        with self.lock_ready_run:
            return self.ready_run 

    def get_status(self):
        with self.lock_status:
            return self.status_current
    def get_is_run(self):
        with self.lock_is_run:
            return self.is_run

    def update_var_input(self, name, value):
            """Cập nhật biến input với lock, thread-safe"""
            input_locks = {
                "btn_inp_start": self.lock_btn_start,
                "btn_inp_stop": self.lock_btn_stop,
                "btn_inp_reset": self.lock_btn_reset,
                "sensor_left_distance": self.lock_sensor_left,
                "sensor_right_distance": self.lock_sensor_right,
                "sensor_safety": self.lock_sensor_safety,
            }

            if name not in self._prev_state:
                print(f"⚠️ Unknown variable: {name}")
                return False
            lock = input_locks.get(name)
            if lock:
                with lock:
                    if self._prev_state[name] != value:
                        self._prev_state[name] = value
                        setattr(self, name, value)
                        print(f"✅ Cập nhật {name} = {value}")
                        return True
            else:
                if self._prev_state[name] != value:
                    self._prev_state[name] = value
                    setattr(self, name, value)
                    print(f"✅ Cập nhật {name} = {value} (no lock)")
                    return True
            return False

    def update_status_from_string(self, data: str):
        """
        Cập nhật trạng thái tất cả các biến từ chuỗi STM32, thread-safe
        data: chuỗi dạng 'status_all:1,0,1,1,0,0,1,0,0,1,1'
        """
        try:
            if not data.startswith("status_all:"):
                return 

            raw_values = data.replace("status_all:", "").strip()
            values = list(map(int, raw_values.split(",")))

            if len(values) < 11:
                print("⚠️ Dữ liệu không đủ số trạng thái:", values)
                return
            var_names = [
                'led_out_yellow', 'led_out_red', 'led_out_blue', 'buzzer_out', 'led_out_btn_reset',
                'btn_inp_reset', 'btn_inp_stop', 'btn_inp_start',
                'sensor_left_distance', 'sensor_right_distance', 'sensor_safety'
            ]

            # Gán giá trị từng biến, dùng hàm thread-safe update_var_input cho input
            for i, var_name in enumerate(var_names):
                value = values[i]
                if var_name in ['btn_inp_reset','btn_inp_stop','btn_inp_start',
                                'sensor_left_distance','sensor_right_distance','sensor_safety']:
                    # Cập nhật input có lock
                    self.update_var_input(var_name, value)
                else:
                    setattr(self, var_name, value)
                    self._prev_state[var_name] = value
            print("✅ Cập nhật trạng thái thành công (thread-safe).")
        except Exception as e:
            print("❌ Lỗi khi parse chuỗi:", e)


    def show_states(self):
        """show trạng thái hiện tại của của các Input Output"""
        print("--------------- TRẠNG THÁI OUT ---------------")
        print("=== Trạng thái hệ thống hiện tại ===")
        print("LED vàng          :", "active" if self.led_out_yellow else "non active")
        print("LED đỏ            :", "active" if self.led_out_red else "non active")
        print("LED xanh          :", "active" if self.led_out_blue else "non active")
        print("Còi buzzer        :", "active" if self.buzzer_out else "non active")
        print("LED nút Reset     :", "active" if self.led_out_btn_reset else "non active")
        print("--------------- TRẠNG THÁI INPUT ---------------")
        ACTIVE_LOW = {
            "sensor_safety": 0,
            "btn_inp_stop": 0,
        }
        ACTIVE_HIGH = {
            "sensor_right_distance": 1,
            "sensor_left_distance": 1,
            "btn_inp_start": 1,
            "btn_inp_reset": 1,
        }
        # In trạng thái nút và cảm biến theo loại active
        print("Nút Reset         :", "active" if self.btn_inp_reset == ACTIVE_HIGH["btn_inp_reset"] else "non active")
        print("Nút Start         :", "active" if self.btn_inp_start == ACTIVE_HIGH["btn_inp_start"] else "non active")
        print("Cảm biến trái     :", "active" if self.sensor_left_distance == ACTIVE_HIGH["sensor_left_distance"] else "non active")
        print("Cảm biến phải     :", "active" if self.sensor_right_distance == ACTIVE_HIGH["sensor_right_distance"] else "non active")
        print("Cảm biến an toàn  :", "active" if self.sensor_safety == ACTIVE_LOW["sensor_safety"] else "non active")
        print("Nút Stop          :", "active" if self.btn_inp_stop == ACTIVE_LOW["btn_inp_stop"] else "non active")
        print("===================================")
        print("btn_inp_reset",self.btn_inp_reset)



    def stop_thread_handler_stm32(self) -> None:
        """Dừng luồng chính xử lý logic và gửi dữ liệu Output tới STM32."""
        self.allow_open_thread = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        print("🛑 [IAIControl] Đã dừng luồng handler STM32.")

    def stop_thread_input_handler_stm32(self) -> None:
        """Dừng luồng đọc dữ liệu đầu vào từ các nút nhấn vật lý của STM32."""
        self.allow_button_thread = False
        if self.button_thread and self.button_thread.is_alive():
            self.button_thread.join(timeout=2)
        print("🛑 [IAIControl] Đã dừng luồng input STM32.")

    def start_input_thread(self):
        self.allow_button_thread = True
        self.button_thread = threading.Thread(target=self._input_thread, daemon=True)
        self.button_thread.start()
        print("✅ Input thread started")

    def start_thread_handl_request_stm32(self):
        """Hàm này để mở luồng xử lý STM32"""
        if self.serial_manager is None:
            return
        print("Mở luồng lắng nghe sự kiện nhấn của client")
        self.allow_open_thread = True
        self.thread = threading.Thread(target=self._handler_request_stm32, daemon=True)
        self.thread.start()

    def clear_command_rx_queue(self) -> int:
        """Xả sạch toàn bộ bản tin tồn đọng trong command_rx_queue trước khi gửi lệnh mới."""
        count = 0
        if not hasattr(self, "command_rx_queue") or self.command_rx_queue is None:
            return 0
        while True:
            try:
                self.command_rx_queue.get_nowait()
                count += 1
            except queue.Empty:
                break
            except Exception:
                break
        if count > 0:
            print(f"🗑️ [IAIControl] Đã xả sạch {count} bản tin tồn đọng trong command_rx_queue.")
        return count

    def stop(self) -> None:
        """Dừng toàn bộ các luồng hoạt động của bộ điều khiển STM32/IAI và hủy đăng ký RX queues."""
        self.stop_thread_input_handler_stm32()
        self.stop_thread_handler_stm32()
        if hasattr(self, "serial_manager") and self.serial_manager is not None:
            if hasattr(self, "rx_queue") and self.rx_queue is not None:
                self.serial_manager.unsubscribe_rx(self.rx_queue)
            if hasattr(self, "command_rx_queue") and self.command_rx_queue is not None:
                self.serial_manager.unsubscribe_rx(self.command_rx_queue)


    def _input_thread(self):
        while self.allow_button_thread:
            self.fuc_update_input_queue_request_arm()# Hàm này để cập nhật các input từ nút nhấn 
            time.sleep(self.config.input_poll_interval)


    def _handler_request_stm32(self):
        """Luồng này đọc trạng thái từ các nút nhấn.Xủ lý Input và cập nhật trạng thái gửi trạng thái cho STM32"""
        print("--- Đã vào luồng STM32 ---")
        while self.allow_open_thread and not self.serial_manager.is_running():
            time.sleep(0.1)
        if not self.allow_open_thread:
            return
        self.show_states()
        self.send_command_stm32(self.config.command_status)
        time.sleep(0.1)
        self.start_input_thread()
        while self.allow_open_thread:
            self.process_request_arm()                  # Hàm này để xử lý logic
            self.fuc_update_output_queue_request_arm()  # Hàm này gửi và cập nhật Output
            time.sleep(0.05)                            # Delay tránh xử lý nhiểu dữ liệu

    def send_command_stm32(self,data):
        """Gửi lệnh qua ManagerSerial được truyền từ bên ngoài.

        Input: ``data`` là chuỗi lệnh STM32.
        Output: không trả về giá trị; lệnh được đưa vào TX queue của manager.
        Errors: lỗi queue được xử lý bởi ``ManagerSerial``.
        """
        self.serial_manager.send_data(data)

    def move_to_point(self, x, y, z, timeout=4) -> bool:
        """Gửi tọa độ đến bộ điều khiển di chuyển."""
        if self.serial_manager is None:
            # Chế độ độc lập không cần COM, sẵn sàng cho Cobot
            print(f"🤖 [Motion] Di chuyển tới điểm: X={x}, Y={y}, Z={z}")
            return True
        try:
            if not self.can_move_iai("di chuyển IAI"):
                return False
            self.clear_command_rx_queue()
            command = f"cmd:{int(x)},{int(y)},{int(z)},80"
            self.send_command_stm32(command)
            return self.wait_for_specific_data(
                self.command_rx_queue,
                command,
                timeout
            )
        except (TypeError, ValueError) as error:
            print(f"⚠️ Tọa độ IAI không hợp lệ: {error}")
            return False

    def move_to_origin(self, timeout=4) -> bool:
        """Gửi lệnh đưa ARM về gốc và chờ xác nhận.

        Input: ``timeout`` là thời gian chờ phản hồi, tính bằng giây.
        Output: ``True`` nếu nhận được tín hiệu về gốc, ngược lại ``False``.
        Errors: COM chưa sẵn sàng hoặc hết thời gian chờ trả về ``False``.
        """
        if not self.serial_manager.is_running():
            return False
        # Xả sạch dữ liệu cũ còn tồn trong hàng đợi phản hồi trước khi gửi lệnh mới
        self.clear_command_rx_queue()
        self.send_command_stm32(self.config.command_move_to_origin)
        return self.wait_for_specific_data(
            self.command_rx_queue,
            self.config.status_returned_origin,
            timeout
        )


    def put_rx_stm32(self,data):
        """Gửi lệnh Ready vào RX moniter để sẵn sàng chạy"""
        try:
            self.serial_manager.rx_queue.put_nowait(data)
            print("Data push RX monitor:", data)
        except queue.Full:
            print("Không truyền được dữ liệu vì RX queue đầy")




    def fuc_update_output_queue_request_arm(self):
        """Gửi lệnh xuống STM32 khi trạng thái output thay đổi"""
        output_mapping = {
            "led_out_red": "led_red_",   
            "led_out_blue": "led_blue_",
            "led_out_yellow": "led_yellow_",
            "led_out_btn_reset": "btn_led_reset_",
            "buzzer_out": "buzzer_",
        }
        for var_name, command in output_mapping.items():
            current_value = getattr(self, var_name)
            prev_value = self._prev_state.get(var_name)
        
            if current_value != prev_value:
                self._prev_state[var_name] = current_value  # cập nhật trạng thái cũ
                data_send = f"{command}{'on' if current_value else 'off'}:\n"
                self.send_command_stm32(data_send)
                time.sleep(0.05)


            
    def fuc_update_input_queue_request_arm(self):
        """Cập nhật trạng thái nút và cảm biến từ RX queue của ManagerSerial.
        Xả toàn bộ các bản tin đang chờ (tối đa 25) để loại bỏ hoàn toàn độ trễ."""
        for _ in range(25):
            try:
                data_request_arm = self.rx_queue.get_nowait()
            except queue.Empty:
                break
            except Exception:
                break
            self._handle_single_input_message(data_request_arm)

    def _handle_single_input_message(self, data_request_arm: str) -> None:
        """Xử lý chi tiết từng bản tin input nhận từ STM32."""
        if not isinstance(data_request_arm, str):
            return
        if "status_all:" in data_request_arm:
            self.update_status_from_string(data_request_arm)
            print("Trạng thái sau khi update")
            self.show_states()
        elif "btn_reset:" in data_request_arm:
            value = self._parse_input_value(data_request_arm)
            if value is None:
                return
            self.update_var_input("btn_inp_reset", value)
        elif "btn_stop:" in data_request_arm:
            value = self._parse_input_value(data_request_arm)
            if value is None:
                return
            self.update_var_input("btn_inp_stop", value)
        elif "btn_start:" in data_request_arm:
            value = self._parse_input_value(data_request_arm)
            if value is None:
                return
            self.update_var_input("btn_inp_start", value)
        elif "sensor_left:" in data_request_arm:
            value = self._parse_input_value(data_request_arm)
            if value is None:
                return
            self.update_var_input("sensor_left_distance", value)
        elif "sensor_right:" in data_request_arm:
            value = self._parse_input_value(data_request_arm)
            if value is None:
                return
            self.update_var_input("sensor_right_distance", value)
        elif "sensor_safety:" in data_request_arm:
            value = self._parse_input_value(data_request_arm)
            if value is None:
                return
            self.update_var_input("sensor_safety", value)
        elif self.config.status_returned_origin in data_request_arm:
            if self.get_status() != ModeState.RETURNED_OR and not self.get_is_origin():
                self.send_log_html("cmd_control_log:clearn_log")
                self.send_log_html("✔️ Đã về gốc.")
                self.send_log_html("✅ Nhấn Start để thiết lập chế độ tự động.")
                self.set_is_origin(True)
                self.set_status(ModeState.RETURNED_OR)
        elif "erro:x" in data_request_arm:
            self.send_log_html("❌ Lỗi dữ liệu trục X bị quá hạn.")
        elif "erro:y" in data_request_arm:
            self.send_log_html("❌ Lỗi dữ liệu trục Y bị quá hạn.")

    @staticmethod
    def _parse_input_value(data: str):
        """Đọc giá trị số của một bản tin input STM32.

        Input: chuỗi dạng ``btn_start:1`` hoặc ``sensor_safety:0``.
        Output: số nguyên nếu hợp lệ, ngược lại ``None``.
        Errors: dữ liệu sai định dạng được ghi log và không làm chết thread.
        """
        try:
            return int(data.split(":", 1)[1].strip())
        except (IndexError, TypeError, ValueError) as error:
            print(f"⚠️ Bản tin input không hợp lệ: {data!r} ({error})")
            return None
            


    def process_request_arm(self):
        """Hàm này để xử lý logic mflow với biến input thread-safe"""
        if self.get_btn_inp_stop() == 0:
            if self.get_status() != ModeState.STOP:
                self.send_log_html("cmd_control_log:clearn_log")
                self.serial_manager.clear_tx_queue()
                self.send_command_stm32(self.config.command_stop)
                self.send_log_html("cmd_control:press_stop")
                time.sleep(0.05)
                self.machine_run = False
                self.handler_stop()
                self.set_pause_because_stop(True)
                self.set_status(ModeState.STOP)
                return
            return

        elif self.get_btn_inp_stop() == 1 and self.get_status() == ModeState.STOP and self.get_btn_inp_reset():
            self.send_command_stm32(self.config.command_reset_stop)
            time.sleep(0.05)
            self.release_stop()
            self.set_pause_because_stop(False)
            self.set_is_run(False)
            self.set_status(ModeState.WAIT_ORG)
 

        elif self.get_btn_inp_start() and self.get_btn_inp_stop() == 1 and self.get_status() == ModeState.WAIT_ORG:
            self.set_status(ModeState.WAIT_ORIGIN_SENSOR)
            self.press_start_stop_processing_complete()
            self.send_log_html("✔️ Đang về gốc .")
            time.sleep(0.1)
            print("hiển thị đang về gốc")
            return

        elif self.get_status() == ModeState.WAIT_ORIGIN_SENSOR:
            if not self.get_sensor_safety():
                self.send_log_html("❌ Cảnh báo chạm cảm biến an toàn khi về gốc.<br>✅ Nhấn Start tiếp tục về gốc.")
                self.send_log_html("status_show_warning:touch_sensor_safety")
                self.send_log_html("")
                self.serial_manager.clear_tx_queue()
                self.send_command_stm32(self.config.command_pause)
                time.sleep(0.05)
                self.pause_on_the_way_back_org = True
            elif self.get_btn_inp_start() and self.pause_on_the_way_back_org:
                self.handler_mode_auto()
                self.send_command_stm32(self.config.command_resume)
                self.send_log_html("status_show_warning:sensor_safety_ok")
                time.sleep(0.05)
                self.pause_on_the_way_back_org = False
                return
            if self.pause_on_the_way_back_org:
                self.handler_touch_sensor_safety()
                return

        elif self.get_btn_inp_stop() == 1 and self.get_status() == ModeState.RETURNED_OR:
            self.set_status(ModeState.WAIT_AUTO)
            if not self.get_is_run():
                self.set_is_origin(True)
                self.send_log_html("✅ Nhấn Start để thiết lập chế độ tự động.")
                return
            print("Chính thức vào về gốc nhé")
            return

        elif self.get_btn_inp_start() and self.get_btn_inp_stop() == 1 and self.get_status() == ModeState.WAIT_AUTO:
            self.set_status(ModeState.AUTO)
            self.send_log_html("✔️ Đã vào chế độ tự động.")
            self.handler_mode_auto()
            return

        elif self.get_btn_inp_stop() == 1 and self.get_status() == ModeState.WAIT_AUTO and not self.get_btn_inp_start():
            self.handler_wait_auto()
            return

        elif self.get_btn_inp_start() and self.get_status() == ModeState.NORMOL and not self.get_is_run():
            self.the_first_connect()
            self.set_status(ModeState.WAIT_ORG)
            return

        elif self.get_status() == ModeState.AUTO and self.get_sensor_left_distance() and self.get_sensor_right_distance() and self.get_sensor_safety() and not self.get_is_run():
            if self.show_product_ng:
                self.send_log_html("✅ Hãy lấy sản phẩm NG ra.")
                self.show_product_ng = False
            else:
                self.send_log_html("✅ Hãy lấy sản phẩm cũ ra.")
            self.set_status(ModeState.WAIT_TAKE_PRODUCT)

        elif self.get_status() == ModeState.WAIT_TAKE_PRODUCT and not self.get_sensor_left_distance() and not self.get_sensor_right_distance() and self.get_sensor_safety() and not self.get_is_run():
            self.send_log_html("✅ Cho sản phẩm mới vào.")
            self.send_log_html("cmd_control:reset_status_judment_product")
            self.set_status(ModeState.RUN_STEP)

        elif self.get_status() == ModeState.RUN_STEP and self.get_sensor_left_distance() and self.get_sensor_right_distance() and self.get_sensor_safety() and not self.get_is_run():
            time.sleep(0.3)
            if  self.get_status() == ModeState.RUN_STEP and self.get_sensor_left_distance() and self.get_sensor_right_distance() and self.get_sensor_safety() and not self.get_is_run():
                # debug_print("Sản phẩm đã sẵn sàng để chạy.")
                self.put_rx_stm32("ready")
                self.machine_run = True
                self.send_log_html("cmd_control_log:clearn_log")
            
        elif self.get_status() == ModeState.AUTO and not self.get_sensor_left_distance() and not self.get_sensor_right_distance() and self.get_sensor_safety() and not self.get_is_run():
            self.send_log_html("✅ Cho sản phẩm mới vào.")
            self.send_log_html("cmd_control:reset_status_judment_product")
            self.set_status(ModeState.PUT_PRODUCT)

        elif self.get_status() == ModeState.PUT_PRODUCT and self.get_sensor_left_distance() and self.get_sensor_right_distance() and self.get_sensor_safety() and not self.get_is_run():
            # debug_print("✔️ Đã cho sản phẩm mới vào.")
            self.send_log_html("✔️ Đã cho sản phẩm mới vào.")
            self.set_status(ModeState.RUN_STEP)

        else:
            match self.get_status():
                case ModeState.RUN_STEP:
                    if self.machine_run and not self.get_sensor_safety() and self.get_sensor_right_distance() and self.get_sensor_left_distance():
                        self.set_status(ModeState.RUN_STEP_3)
                        self.send_log_html("❌ Cảnh báo chạm cảm biến an toàn.")
                        self.send_log_html("status_show_warning:touch_sensor_safety")
                        self.send_log_html("✅ Bỏ tay ra khỏi vùng cảm biến an toàn.")
                        self.send_log_html("✅ Nhấn Start để tiếp tục chạy.")
                    if  self.get_sensor_left_distance() and self.get_sensor_right_distance() and self.get_sensor_safety() and self.get_is_run() and not self.get_is_origin():
                        # debug_print("San pham dang phan dinh")
                        self.machine_run = True
                        if not self.get_sensor_safety():
                            self.set_status(ModeState.RUN_STEP_3)
                            self.send_log_html("❌ Cảnh báo chạm cảm biến an toàn.")
                            self.send_log_html("status_show_warning:touch_sensor_safety")
                            self.send_log_html("✅ Bỏ tay ra khỏi vùng cảm biến an toàn.")
                            self.send_log_html("✅ Nhấn Start để tiếp tục chạy.")
                        # phan nay se uncomment neu hoan thien xong san pham 
                        if self.get_pause_becuase_ng():
                            if self.get_btn_inp_reset():
                                self.set_pause_becuase_ng(False)
                                self.send_command_stm32("cmd:0,0,0,0")
                                self.set_is_origin(True)
                                self.handler_mode_auto()
                                self.machine_run = False
                                self.set_is_run(False)
                                self.set_status(ModeState.AUTO)
                                self.show_product_ng = True
                            else:
                                self.handler_product_ng()
                        time.sleep(0.05)
                    elif self.get_sensor_left_distance() and self.get_sensor_right_distance() and self.get_sensor_safety() and self.get_is_run() and self.get_is_origin() and not self.get_has_decided():
                        time.sleep(0.3)
                        if self.get_sensor_left_distance() and self.get_sensor_right_distance() and self.get_sensor_safety() and self.get_is_run() and self.get_is_origin() and not self.get_has_decided():
                            self.put_rx_stm32("ready")
                            self.machine_run = True
                    elif self.get_sensor_left_distance() and self.get_sensor_right_distance() and self.get_sensor_safety() and self.get_is_run() and self.get_is_origin() and self.get_has_decided():
                        self.set_pause_becuase_ng(False)
                        self.machine_run = False
                    if not self.get_sensor_left_distance() and not self.get_sensor_right_distance() and self.get_sensor_safety() and self.get_is_run() and self.get_is_origin() and self.get_has_decided():
                        self.set_has_decidedt(False)
                        self.send_log_html("cmd_control:reset_status_judment_product")
                        self.set_status(ModeState.RUN_STEP_1)

                case ModeState.RUN_STEP_1:
                    if self.get_sensor_left_distance() and self.get_sensor_right_distance() and self.get_sensor_safety() and self.get_is_run() and self.get_is_origin():
                        time.sleep(0.3)
                        if self.get_sensor_left_distance() and self.get_sensor_right_distance() and self.get_sensor_safety() and self.get_is_run() and self.get_is_origin():
                            self.send_log_html("status_show_warning:balance")
                            self.put_rx_stm32("ready")
                            self.machine_run = True
                    if not self.get_sensor_left_distance() or not self.get_sensor_right_distance() and self.get_sensor_safety() and self.get_is_run() and self.get_is_origin():
                        pass
                    if (self.get_sensor_left_distance() != self.get_sensor_right_distance()) and self.get_is_origin() and not self.machine_run  and self.get_sensor_safety():
                        # sản phẩm đặt kênh
                        self.send_log_html("status_show_warning:unbalanced")
                    if not self.get_is_origin():
                        self.set_status(ModeState.RUN_STEP)

                case ModeState.RUN_STEP_3:
                    self.send_command_stm32("pause:")
                    self.set_pause_because_sensor_safety(True)
                    self.set_status(ModeState.RUN_STEP_4)

                case ModeState.RUN_STEP_4:
                    print("Tạm dừng vì người thao tác chạm cảm biến an toàn")
                    self.handler_touch_sensor_safety()
                    if self.machine_run and self.get_sensor_safety() and self.get_sensor_right_distance() and self.get_sensor_left_distance() and self.get_btn_inp_start():
                        self.send_command_stm32(self.config.command_resume)
                        status_wait = self.wait_for_specific_data(
                            self.rx_queue, "refesh_pause_ok", 1
                        )
                        if status_wait:
                            self.send_log_html("status_show_warning:sensor_safety_ok")
                            self.set_pause_because_sensor_safety(False)
                            self.handler_mode_auto()
                            self.set_status(ModeState.RUN_STEP)


    def handler_product_ng(self):
        blink_interval = 0.3
        current_time  = time.time()
        if current_time  -  self.last_blink_time_red  > blink_interval:
            self.last_blink_time_red = current_time
            self.led_out_red = 1 - self.led_out_red
            self.led_out_blue = 0
            self.led_out_yellow = 0
            self.buzzer_out = 1

          
    def release_stop(self):
        """Hàm này xử lý khi nhả stop"""
        self.send_log_html("✔️ Đã nhả nút Stop và nhấn Reset.")
        self.send_log_html("✅ Nhấn Start để về gốc.")
        self.send_log_html("cmd_control:refesh_stop")
        # debug_print("Hủy Stop")
        self.led_out_red = 0
        self.led_out_blue = 0
        self.led_out_yellow = 0
        self.buzzer_out = 0
        self.led_out_btn_reset = 0
        # debug_print("Hiệu ứng hủy stop kích hoạt")

    def handler_wait_auto(self):
        """Hàm này xử lý khi đợi Auto"""
        blink_interval = 0.3
        current_time  = time.time()
        if current_time  - self.last_blink_time > blink_interval:
            self.last_blink_time = current_time
            self.led_out_red = 0
            self.led_out_blue = 1 - self.led_out_blue
            self.led_out_yellow = 0
            self.buzzer_out = 0
            self.led_out_btn_reset = 0

    def send_log_html(self,data):
        """Gửi log điều khiển; log queue UI được quản lý bên ngoài controller."""
        print(data)

    def handler_stop(self):
        """ Hàm này xử lý khi có người nhấn nút Start"""
        # debug_print("Đang dừng khẩn cấp")
        self.send_log_html("❌ Đang dừng khẩn cấp !")
        self.send_log_html("✅Thả Stop -> Nhấn Reset -> Nhấn Start để về gốc.")
        self.led_out_red = 1
        self.led_out_blue = 0
        self.led_out_yellow = 0
        self.buzzer_out = 1
        self.led_out_btn_reset = 1
        # debug_print("Hiệu ứng dừng khẩn kích hoạt")
    
    def handler_mode_auto(self):
        """Hàm này xừ lý khi người dùng vào chế độ Auto"""
        self.led_out_red = 0
        self.led_out_blue = 1
        self.led_out_yellow = 0
        self.buzzer_out = 0
        print("Hiệu ứng Mode auto")
    

    def press_start_stop_processing_complete(self):
        """Hàm này xử lý khi người dùng nhấn nút nhấn về gốc"""
        self.led_out_red = 0
        self.led_out_blue = 1
        self.led_out_yellow = 0
        self.led_out_btn_reset= 0
        self.send_command_stm32(self.config.command_move_to_origin)
        
    def the_first_connect(self):
        """Hàm này xử lý đèn khi lần đầu chạy"""
        self.led_out_red = 0
        self.led_out_blue = 1
        self.led_out_yellow = 0
        self.led_out_btn_reset= 0
 

    def handler_touch_sensor_safety(self):
        """Hàm này nhấp nháy led vì chạm cảm biến an toàn"""
        blink_interval = 0.3
        current_time  = time.time()
        if current_time  - self.last_blink_time_blue_and_yellow > blink_interval:
            self.last_blink_time_blue_and_yellow = current_time
            if self.led_out_yellow != self.led_out_blue:
                self.led_out_yellow = self.led_out_blue
            self.buzzer_out = 1
            self.led_out_red = 0
            self.led_out_blue = 1 - self.led_out_blue
            self.led_out_yellow = 1 - self.led_out_yellow
            self.led_out_btn_reset = 0
    def wait_for_specific_data(self, queue_check_in_1, expected_signal, timeout = 1):
        """
        Chờ tín hiệu cụ thể từ queue_check_in_1.
        - expected_signal: tín hiệu mong đợi (chuỗi)
        - timeout: thời gian chờ tối đa (giây)
        Trả về True nếu nhận đúng tín hiệu, False nếu hết thời gian chờ.
        """
        print(f"⏳ Đang chờ tín hiệu: {expected_signal} trong {timeout} giây...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data = queue_check_in_1.get(timeout=self.config.queue_timeout)
            except (queue.Empty, Exception):
                data = None
            if data:
                print(f"📥 PC Nhận được: {data}")
                if self._matches_expected_signal(data, expected_signal):
                    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    print(now_str, "✅ Nhận đúng tín hiệu mong đợi.")
                    return True
                else:
                    print(f"⚠️ Tín hiệu nhận khác kỳ vọng: {data} (chờ: {expected_signal})")
            time.sleep(0.001)  # tránh CPU 100%
        print(f"❌ Timeout: Không nhận được tín hiệu {expected_signal} trong {timeout} giây.")
        return False

    @staticmethod
    def _matches_expected_signal(data: str, expected_signal: str) -> bool:
        """So khớp phản hồi ARM, kể cả dạng tọa độ có padding và hậu tố ``ok``.

        Input: ``data`` là phản hồi thực tế; ``expected_signal`` là lệnh chờ.
        Output: ``True`` nếu phản hồi đúng lệnh hoặc chứa tín hiệu mong đợi.
        Errors: dữ liệu không hợp lệ trả về ``False``.
        """
        actual = str(data).strip()
        expected = str(expected_signal).strip()
        if not expected.startswith("cmd:"):
            return expected in actual
        try:
            expected_values = [int(value) for value in expected[4:].split(",")]
            actual_values = [int(value) for value in actual[4:].split(",")[:4]]
            return actual.startswith("cmd:") and actual_values == expected_values
        except (IndexError, TypeError, ValueError):
            return False
    
    def get_sensor_values(self):
        return {
            "left_distance": self.sensor_left_distance,
            "right_distance": self.sensor_right_distance,
            "safety": self.sensor_safety,
        }


