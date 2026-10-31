from app.stages import StagePreprocess, StageTransform, StageExport
from app.container import ServiceContainer, EnumMode
from app.config import ModeState
from app.core.context import RuntimePipelineState
import threading
import time

class Pipeline:
    def __init__(self,services: ServiceContainer):

        self.services = services
        self.stage_ingest = StagePreprocess(self.services)
        self.services.stage_preprocess = self.stage_ingest
        self.stage_transform = StageTransform(self.services)
        self.stage_export   =  StageExport(self.services)

        self.running = False
        self.awaiting_reset = True
        self._last_connections = None
        self._previous_reset = None
        self._reset_rejected_logged = False
        self._reset_lock = threading.Lock()
        self._reset_start_pending = False
        self._reset_watcher = threading.Thread(
            target=self._watch_reset_button,
            daemon=True,
            name="PipelineResetWatcher",
        )
        self.thread = threading.Thread(
            target=self._run_pipeline,
            daemon=True,
            name="RunPipeline"
        )
        self.open_task_pipeline()
        self._reset_watcher.start()
        self.thread.start()

    def open_task_pipeline(self):
        self.running = True
        print("[PIPELINE] Đã bật pipeline chính.")

    def stop_task_pipeline(self):
        self.running = False
        self.services.runtime_state.request_stop()
        print("[PIPELINE] Đã yêu cầu dừng pipeline chính.")

    def _watch_reset_button(self) -> None:
        """Theo dõi cạnh nhấn Reset và khóa Reset trong lúc phán định."""
        previous_reset = False
        while self.running and not self.services.runtime_state.is_stop_requested():
            reset_pressed = bool(self.services.obj_iai_control.get_btn_inp_reset())
            reset_rising = reset_pressed and not previous_reset
            if reset_rising:
                print(
                    "[PIPELINE][RESET] Phát hiện cạnh Reset 0->1: "
                    f"mode={self.services.get_mode().name}, "
                    f"iai_status={self.services.obj_iai_control.get_status().name}, "
                    f"is_origin={self.services.obj_iai_control.get_is_origin()}, "
                    f"judgment_running={self.services.runtime_state.is_judgment_running()}"
                )
                if self.services.runtime_state.is_judgment_running():
                    if not self._reset_rejected_logged:
                        self._publish_log(
                            "⚠️ Đang phán định, không thể nhấn Reset để bắt đầu sản phẩm mới."
                        )
                        self._reset_rejected_logged = True
                elif (
                    self.services.get_mode() == EnumMode.MODE_IDLE
                    and self.services.obj_iai_control.get_is_origin()
                ):
                    with self._reset_lock:
                        self._reset_start_pending = True
                    print("[PIPELINE][RESET] Đã ghi nhận Reset chờ bắt đầu chu kỳ.")
                else:
                    print("[PIPELINE][RESET] Bị từ chối: pipeline/IAI chưa ở trạng thái sẵn sàng.")
            if not reset_pressed:
                self._reset_rejected_logged = False
            previous_reset = reset_pressed
            time.sleep(0.05)

    def _publish_log(self, message: str) -> None:
        """Gửi log pipeline vào ô ``log_judment`` qua queue hiện có."""
        self.services.queue_log_send_client.put({
            "type": "log_Home",
            "message": message,
        })

    def _read_runtime_status(self) -> None:
        """Đọc trạng thái phần cứng và trạng thái IAI/Robot, không điều khiển phần cứng."""
        tcp_connected = getattr(self.services, "is_tcp_connected", False)
        camera_connected = self.services.obj_camera.get_is_connect()
        self.services.runtime_state.set_connections(tcp_connected, camera_connected)
        connections = (tcp_connected, camera_connected)
        if self._last_connections is not None and connections != self._last_connections:
            if not tcp_connected:
                self._publish_log("❌ Mất kết nối mạng Ethernet TCP, đang chờ kết nối lại.")
            if not camera_connected:
                self._publish_log("❌ Mất kết nối camera, đang chờ kết nối lại.")
            if tcp_connected and camera_connected:
                self._publish_log("✅ Mạng Ethernet TCP và camera đã kết nối.")
        self._last_connections = connections
        iai_status = self.services.obj_iai_control.get_status()
        if iai_status == ModeState.STOP:
            self.services.runtime_state.set_pipeline_state(RuntimePipelineState.ERROR)
        elif self.services.runtime_state.is_judgment_running():
            self.services.runtime_state.set_pipeline_state(RuntimePipelineState.RUNNING)
        elif self.services.obj_iai_control.get_pause_because_sensor_safety():
            self.services.runtime_state.set_pipeline_state(RuntimePipelineState.WARNING)
        elif self.services.obj_iai_control.get_is_origin():
            self.services.runtime_state.set_pipeline_state(RuntimePipelineState.READY)
        else:
            self.services.runtime_state.set_pipeline_state(RuntimePipelineState.WAIT_START)

    def _start_cycle_after_reset(self) -> None:
        """Chuyển sang Stage 1 sau tín hiệu Reset của IAI."""
        if self.services.get_mode() != EnumMode.MODE_IDLE:
            print(f"[PIPELINE][START] Bỏ qua: mode hiện tại={self.services.get_mode().name}.")
            return

        with self._reset_lock:
            reset_start_pending = self._reset_start_pending

        if self.awaiting_reset and not reset_start_pending:
            return

        com_connected, camera_connected = self.services.runtime_state.get_connections()
        print(
            "[PIPELINE][START] Kiểm tra điều kiện: "
            f"com={com_connected}, camera={camera_connected}, "
            f"iai_status={self.services.obj_iai_control.get_status().name}, "
            f"is_origin={self.services.obj_iai_control.get_is_origin()}, "
            f"reset_pending={reset_start_pending}, awaiting_reset={self.awaiting_reset}"
        )
        if not com_connected:
            self._publish_log("⏳ Chưa bắt đầu phán định: COM chưa sẵn sàng.")
            return
        if not camera_connected:
            self._publish_log("⏳ Chưa bắt đầu phán định: Camera chưa sẵn sàng.")
            return
        iai_status = self.services.obj_iai_control.get_status()
        if not self.services.obj_iai_control.get_is_origin():
            self._publish_log("⏳ Chưa bắt đầu phán định: IAI chưa về gốc.")
            return
        allowed_start_statuses = {
            ModeState.WAIT_AUTO,
            ModeState.AUTO,
            ModeState.PUT_PRODUCT,
        }
        if iai_status not in allowed_start_statuses:
            self._publish_log(
                f"⏳ Đã nhận Reset nhưng IAI chưa sẵn sàng: {iai_status.name}."
            )
            return
        if self.awaiting_reset:
            with self._reset_lock:
                self._reset_start_pending = False
            self.awaiting_reset = False
            self.services.runtime_state.clear_stop()
        self._publish_log("✅ Reset hợp lệ, bắt đầu phán định sản phẩm.")
        print("[PIPELINE][START] Điều kiện hợp lệ -> chuyển MODE_PREPOCESS.")
        self.services.set_mode(EnumMode.MODE_PREPOCESS)


    def _run_pipeline(self):
        print(
            "[PIPELINE] Vòng lặp bắt đầu: "
            f"running={self.running}, "
            f"stop_requested={self.services.runtime_state.is_stop_requested()}"
        )
        while self.running and not self.services.runtime_state.is_stop_requested():
            self._read_runtime_status()
            if self.running:
                mode = self.services.get_mode() 
                if mode == EnumMode.MODE_IDLE:
                    self._start_cycle_after_reset()
                elif (mode == EnumMode.MODE_PREPOCESS): 
                    print("--Vào chế độ chuẩn bị chạy --") 
                    try:
                        print("[PIPELINE] Gọi Stage 1 preprocess.")
                        self.stage_ingest.run()
                        print("[PIPELINE] Stage 1 hoàn tất.")
                        continue
                    except Exception as error:
                        print(f"[PIPELINE] Stage 1 exception: {error!r}")
                        self._publish_log(f"❌ Stage 1 lỗi: {error}")
                        self.awaiting_reset = True
                        self.services.set_mode(EnumMode.MODE_IDLE)

                elif (mode == EnumMode.MODE_TRANSFORM):
                    print("----Vào chế độ chạy -----")
                    print("[PIPELINE] Gọi Stage 2 transform.")
                    transform_succeeded = False
                    try:
                        self.stage_transform.run()
                        transform_succeeded = True
                    except Exception as error:
                        print(f"[PIPELINE] Stage 2 exception: {error!r}")
                        self._publish_log(f"❌ Stage 2 lỗi: {error}")
                        self.awaiting_reset = True
                        self.services.set_mode(EnumMode.MODE_IDLE)
                    if transform_succeeded:
                        try:
                            print("[PIPELINE] Gọi Stage 3 export.")
                            self.stage_export.run()
                            self.awaiting_reset = True
                        except Exception as error:
                            print(f"[PIPELINE] Stage 3 exception: {error!r}")
                            self._publish_log(f"❌ Stage 3 lỗi: {error}")
                            self.awaiting_reset = True
                            self.services.set_mode(EnumMode.MODE_IDLE)
                elif (mode == EnumMode.MODE_EXPORT):
                    print("----Vào chế độ hoàn thiện-----")
                    
                time.sleep(0.05)

        print(
            "[PIPELINE] Vòng lặp kết thúc: "
            f"running={self.running}, "
            f"stop_requested={self.services.runtime_state.is_stop_requested()}"
        )


            

