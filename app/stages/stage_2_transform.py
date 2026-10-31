from app.container import ServiceContainer, EnumMode
from app.core.context import RuntimePipelineState
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any
import queue
import threading
from app.config.path_config import (
    BASE_DIR,
    PATH_FOLDER_OUTPUT_JUDGMENT,
    PATH_FOLDER_OUTPUT,
    URL_PATH_OUTPUT,
)
import cv2
import json
import shutil
import time
import numpy as np
from app.machine.anti_blur_service import AntiBlurService


@dataclass
class InspectionTaskItem:
    """Đóng gói dữ liệu một điểm đo để chuyển từ luồng chụp sang luồng phán định."""
    prepared: Any
    frame: dict[str, Any]
    point: dict[str, Any]
    step: int
    image: Any = None
    inspectors: dict[str, Any] = field(default_factory=dict)
    active_scale_mm_per_pixel: float = 1.0
    is_calibrated: bool = True
    calibration_reason: str = ""
    is_no_data: bool = False

    @property
    def face(self) -> dict[str, Any]:
        return self.frame
    no_data_message: str = ""
    sharpness_score: float = 0.0


class StageTransform:
    LINE_BASED_INSPECTORS: set[str] = set()

    INSPECTOR_DISPLAY_NAMES = {
        "AnomalyPointInspector": "Kiểm tra điểm bất thường",
        "ForeignObjectInspector": "Dị vật",
        "StampItemInspector": "Kiểm tra Có/Không tem",
        "StampAlignmentInspector": "Ki?m tra ?? l?ch tem",
        "OCRTextInspector": "Nhận diện chữ OCR",
        "ColorItemInspector": "Ki?m tra m?u",
    }

    def __init__(
        self,
        services: ServiceContainer,
        queue_maxsize: int = 5,
        max_judger_workers: int = 5,
    ):
        self.services = services
        self.max_judger_workers = max(1, int(max_judger_workers))
        self.queue_maxsize = max(self.max_judger_workers, int(queue_maxsize))
        self._output_save_queue: queue.Queue[dict[str, Any] | None] = queue.Queue(maxsize=100)
        self._output_saver_thread: threading.Thread | None = None

    def run(self):
        """Di chuyển, chụp ảnh và phán định toàn bộ point của sản phẩm theo mô hình Pipelined Queue.

        Input: ``services.prepared_product`` từ Stage 1.
        Output: danh sách kết quả point lưu vào runtime state và chuyển Stage 3.
        Errors: ``RuntimeError`` khi phần cứng, di chuyển hoặc camera thất bại.
        """
        prepared = self.services.prepared_product
        if prepared is None:
            raise RuntimeError("Stage 2 chưa nhận dữ liệu từ Stage 1")
        print(
            f"[STAGE2] Bắt đầu session={prepared.session_id}, "
            f"product={prepared.product_id}, number_step={prepared.number_step}"
        )
        self.services.runtime_state.set_pipeline_state(RuntimePipelineState.RUNNING)
        self.services.runtime_state.set_judgment_running(True)
        results: list[dict[str, Any]] = []
        consumer_errors: list[Exception] = []

        self._send_client({
            "type": "judgment_reset",
            "data": {
                "product_id": prepared.product_id,
                "number_step": prepared.number_step,
                "session_id": prepared.session_id,
            },
        })

        inspection_queue: queue.Queue[InspectionTaskItem | None] = queue.Queue(
            maxsize=self.queue_maxsize
        )

        output_saver_thread = threading.Thread(
            target=self._output_saver_worker,
            daemon=True,
            name="Stage2OutputSaverWorker",
        )
        self._output_saver_thread = output_saver_thread
        output_saver_thread.start()

        configured_max_workers = self.max_judger_workers
        cfg_sw = getattr(self.services, "obj_config_software", None)
        if cfg_sw is not None and hasattr(cfg_sw, "get_max_judger_workers"):
            try:
                val = cfg_sw.get_max_judger_workers()
                if isinstance(val, (int, float, str)):
                    configured_max_workers = max(1, min(10, int(val)))
            except Exception:
                pass

        step_count = getattr(prepared, "number_step", 1)
        if not isinstance(step_count, int):
            try:
                step_count = int(step_count)
            except Exception:
                step_count = 1

        num_workers = min(configured_max_workers, max(1, step_count))
        results_lock = threading.Lock()
        errors_lock = threading.Lock()
        consumer_threads: list[threading.Thread] = []
        for worker_idx in range(num_workers):
            worker_thread = threading.Thread(
                target=self._consumer_worker,
                args=(inspection_queue, results, consumer_errors, results_lock, errors_lock),
                daemon=True,
                name=f"Stage2JudgerWorker-{worker_idx + 1}",
            )
            worker_thread.start()
            consumer_threads.append(worker_thread)

        try:
            # Luồng Producer: Điều khiển di chuyển IAI, chụp ảnh và đẩy task vào queue
            self._producer_loop(prepared, inspection_queue, consumer_errors, num_workers)

            # Chờ toàn bộ Consumer workers hoàn tất task trong queue
            for worker_thread in consumer_threads:
                worker_thread.join()

            if consumer_errors:
                raise consumer_errors[0]

            # Đảm bảo toàn bộ file output được ghi xuống đĩa hoàn tất trước khi sang Stage 3
            try:
                self._output_save_queue.put(None, timeout=2.0)
                output_saver_thread.join(timeout=10.0)
            except Exception as saver_err:
                print(f"[STAGE2] Cảnh báo chờ flush output saver: {saver_err}")

            # Đảm bảo toàn bộ ảnh retrain nền được ghi xuống đĩa hoàn tất
            try:
                if hasattr(self.services.obj_judment, "flush_retrain_queue"):
                    self.services.obj_judment.flush_retrain_queue()
            except Exception as retrain_err:
                print(f"[STAGE2] Cảnh báo chờ flush retrain saver: {retrain_err}")

            # Sắp xếp lại danh sách kết quả theo đúng thứ tự step trước khi tổng hợp
            results.sort(key=lambda r: int(r.get("step", 0)))

            self.services.runtime_state.set_product_result(results)
            is_overall_ok = all(result.get("overall") is True for result in results)
            counts = self.services.obj_product_count_service.record_result(is_overall_ok)
            self._send_client({
                "type": "judgment_product_result",
                "data": {
                    "product_id": prepared.product_id,
                    "session_id": prepared.session_id,
                    "number_step": prepared.number_step,
                    "overall": is_overall_ok,
                    "status": "OK" if is_overall_ok else "NG",
                    "items": results,
                    "counts": counts,
                },
            })
            self.services.set_mode(EnumMode.MODE_EXPORT)
            return results
        except Exception as error:
            # Dừng output saver và toàn bộ consumer threads an toàn nếu có lỗi ở producer hoặc consumer
            try:
                self._output_save_queue.put_nowait(None)
            except (queue.Full, Exception):
                pass
            if output_saver_thread.is_alive():
                output_saver_thread.join(timeout=1.0)

            for _ in range(num_workers):
                try:
                    inspection_queue.put_nowait(None)
                except (queue.Full, Exception):
                    pass
            for worker_thread in consumer_threads:
                if worker_thread.is_alive():
                    worker_thread.join(timeout=1.0)

            results.sort(key=lambda r: int(r.get("step", 0)))
            counts = self.services.obj_product_count_service.record_result(False)
            self._send_client({
                "type": "judgment_product_result",
                "data": {
                    "product_id": prepared.product_id,
                    "session_id": prepared.session_id,
                    "number_step": prepared.number_step,
                    "overall": False,
                    "status": "NG",
                    "error": str(error),
                    "items": results,
                    "counts": counts,
                },
            })
            raise
        finally:
            self.services.runtime_state.set_judgment_running(False)

    def _ensure_running(self) -> None:
        """Dừng stage nếu người dùng yêu cầu stop hoặc IAI đang ở lỗi."""
        if self.services.runtime_state.is_stop_requested():
            raise RuntimeError("Pipeline đã nhận yêu cầu dừng")
        if self.services.obj_iai_control.get_status().name == "STOP":
            raise RuntimeError("IAI đang ở trạng thái STOP")

    def _producer_loop(
        self,
        prepared: Any,
        inspection_queue: queue.Queue,
        consumer_errors: list[Exception],
        num_workers: int = 1,
    ) -> None:
        """Luồng Producer: Di chuyển IAI và trigger chụp ảnh, đẩy vào hàng đợi."""
        step = 0
        try:
            for frame in prepared.frames:
                for point in frame["points"]:
                    self._ensure_running()
                    if consumer_errors:
                        raise consumer_errors[0]

                    step += 1
                    task = self._capture_point_task(prepared, frame, point, step)
                    self._enqueue_task(inspection_queue, task, consumer_errors)

            # Sau khi chụp xong toàn bộ point, lập tức đưa IAI về vị trí item đầu tiên (step 1)
            self._return_iai_to_start(prepared)

            # Gửi tín hiệu hoàn tất (sentinel) cho toàn bộ consumer workers
            for _ in range(num_workers):
                self._enqueue_task(inspection_queue, None, consumer_errors)
        except Exception:
            for _ in range(num_workers):
                try:
                    inspection_queue.put_nowait(None)
                except (queue.Full, Exception):
                    pass
            raise

    def _enqueue_task(
        self,
        inspection_queue: queue.Queue,
        task: InspectionTaskItem | None,
        consumer_errors: list[Exception],
    ) -> None:
        """Đưa task vào queue, hỗ trợ backpressure chặn luồng chụp tạm thời khi queue đầy."""
        while not self.services.runtime_state.is_stop_requested():
            if consumer_errors:
                raise consumer_errors[0]
            try:
                inspection_queue.put(task, timeout=0.2)
                return
            except queue.Full:
                continue
        if self.services.runtime_state.is_stop_requested():
            raise RuntimeError("Pipeline đã nhận yêu cầu dừng trong khi chờ hàng đợi phán định")

    def _return_iai_to_start(self, prepared: Any) -> None:
        """Đưa IAI về vị trí item đầu tiên (step 1) hoặc vị trí 0,0,0."""
        first_point = None
        if prepared.frames and prepared.frames[0].get("points"):
            first_point = prepared.frames[0]["points"][0]

        if first_point is not None:
            first_frame_id = prepared.frames[0].get("frame_id", "0")
            first_point_id = first_point.get("point_id", "0")
            first_point_target = {
                "frame_id": first_frame_id,
                "point_id": first_point_id,
                "x": first_point["x"],
                "y": first_point["y"],
                "z": first_point["z"],
            }
            print(
                f"[STAGE2] Hoàn tất chụp ảnh các điểm, đưa IAI về vị trí item đầu tiên "
                f"(step 1: frame={first_frame_id}, item={first_point_id}) "
                f"tại X={first_point['x']}, Y={first_point['y']}, Z={first_point['z']}"
            )
            self.services.send_judgment_log(
                f"🔄 Đưa IAI về vị trí item đầu tiên (step 1: frame {first_frame_id}, point {first_point_id})."
            )
            if not self._move_with_retry(first_point_target):
                raise RuntimeError(
                    f"IAI không về được vị trí item đầu tiên (step 1: frame {first_frame_id}, point {first_point_id}) sau sản phẩm"
                )
        else:
            if not self.services.obj_iai_control.move_to_point(0, 0, 0):
                raise RuntimeError("IAI không về được vị trí 0,0,0 sau sản phẩm")

    def _capture_point_task(
        self,
        prepared: Any,
        frame: dict[str, Any],
        point: dict[str, Any],
        step: int,
    ) -> InspectionTaskItem:
        """Thực hiện di chuyển và chụp ảnh tại một điểm, đóng gói thành task cho hàng đợi."""
        frame_id = frame["frame_id"]
        point_id = point["point_id"]
        inspectors = point.get("judgment") or {}
        print(
            f"[STAGE2] step={step}/{prepared.number_step}, "
            f"frame={frame_id}, item={point_id}, inspectors={list(inspectors.keys())}"
        )
        if not inspectors:
            self.services.send_judgment_log(
                f"⚠️ Frame {frame_id}, point {point_id}: không có dữ liệu master phán định."
            )
            return InspectionTaskItem(
                prepared=prepared,
                frame=frame,
                point=point,
                step=step,
                inspectors={},
                is_no_data=True,
                no_data_message="Không có dữ liệu master phán định.",
            )

        # Đã loại bỏ ràng buộc calibration, sử dụng hệ số mặc định 1.0 mm/pixel
        fallback_scale = getattr(prepared, "scale_mm_per_pixel", 1.0)
        if not isinstance(fallback_scale, (int, float)) or float(fallback_scale) <= 0:
            fallback_scale = 1.0
        active_scale_mm_per_pixel = float(fallback_scale)
        is_calibrated = True
        calibration_reason = ""

        print(f"[STAGE2] Di chuyển IAI đến frame={frame_id}, item={point_id}: {point['x']},{point['y']},{point['z']}")
        if not self._move_with_retry(point):
            raise RuntimeError(f"IAI di chuyển thất bại tại frame {frame_id}, point {point_id}")
        # Lấy cấu hình chống rung nhòe cơ khí (Anti-Motion Blur)
        anti_blur_cfg = AntiBlurService.load_config()
        iai_config = getattr(self.services, "obj_iai_config", None) or getattr(
            getattr(self.services, "obj_iai_control", None), "config", None
        )
        t_settle_s = float(anti_blur_cfg.get("t_settle_ms", getattr(iai_config, "t_settle_ms", 40.0))) / 1000.0
        t_hold_safety_s = float(anti_blur_cfg.get("t_hold_safety_ms", getattr(iai_config, "t_hold_safety_ms", 15.0))) / 1000.0
        blur_threshold = float(anti_blur_cfg.get("blur_threshold", getattr(iai_config, "blur_threshold", 100.0)))
        auto_retrigger = bool(anti_blur_cfg.get("auto_retrigger_on_blur", getattr(iai_config, "auto_retrigger_on_blur", True)))
        max_retrigger_count = int(anti_blur_cfg.get("max_retrigger_count", getattr(iai_config, "max_retrigger_count", 1)))
        extra_settle_s = float(anti_blur_cfg.get("extra_settle_ms", 20.0)) / 1000.0

        # 1. Chờ ổn định dao động cơ học sau PEND (Mechanical Settle Time)
        if t_settle_s > 0:
            time.sleep(t_settle_s)

        # 2. Trigger chụp ảnh và ghi nhận thời điểm bắt đầu trigger
        trigger_start = time.time()
        image = self._capture_with_retry()

        # 3. Sharpness Gate & Tự động chụp lại nếu bị nhòe (Auto-Retrigger)
        is_sharp, sharpness_score = AntiBlurService.evaluate_sharpness(
            image, threshold=blur_threshold
        )
        if not is_sharp and auto_retrigger:
            for retry_idx in range(max_retrigger_count):
                print(
                    f"[STAGE2][ANTI-BLUR] Ảnh tại frame={frame_id}, item={point_id} có độ nét {sharpness_score} < {blur_threshold}. "
                    f"Kích hoạt chụp lại lần {retry_idx + 1}/{max_retrigger_count} sau khi chờ thêm {int(extra_settle_s * 1000)}ms..."
                )
                self.services.send_judgment_log(
                    f"⚠️ Ảnh frame {frame_id}, point {point_id} có thể bị rung nhòe (score={sharpness_score} < {blur_threshold}). Đang chụp lại..."
                )
                time.sleep(extra_settle_s)  # Bù thêm thời gian tắt dần dao động
                trigger_start = time.time()
                image = self._capture_with_retry()
                is_sharp, sharpness_score = AntiBlurService.evaluate_sharpness(
                    image, threshold=blur_threshold
                )
                if is_sharp:
                    print(
                        f"[STAGE2][ANTI-BLUR] Chụp lại thành công tại frame={frame_id}, item={point_id}! "
                        f"Độ nét đạt {sharpness_score} >= {blur_threshold}."
                    )
                    break
            if not is_sharp:
                print(
                    f"[STAGE2][ANTI-BLUR] Cảnh báo: Ảnh tại frame={frame_id}, item={point_id} "
                    f"vẫn không đạt ngưỡng nét sau {max_retrigger_count} lần chụp lại (score={sharpness_score})."
                )

        # 4. Bảo vệ phơi sáng trục (Exposure Axis Hold Protection)
        elapsed = time.time() - trigger_start
        if elapsed < t_hold_safety_s:
            time.sleep(t_hold_safety_s - elapsed)

        print(f"[STAGE2] Đã chụp ảnh frame={frame_id}, item={point_id}; đẩy vào hàng đợi phán định (sharpness={sharpness_score}).")

        return InspectionTaskItem(
            prepared=prepared,
            frame=frame,
            point=point,
            step=step,
            image=image,
            inspectors=inspectors,
            active_scale_mm_per_pixel=active_scale_mm_per_pixel,
            is_calibrated=is_calibrated,
            calibration_reason=calibration_reason,
            is_no_data=False,
            sharpness_score=sharpness_score,
        )

    def _consumer_worker(
        self,
        inspection_queue: queue.Queue,
        results: list[dict[str, Any]],
        consumer_errors: list[Exception],
        results_lock: Any = None,
        errors_lock: Any = None,
    ) -> None:
        """Luồng Consumer Worker: lấy ảnh từ hàng đợi, thực thi Judment.run_summary và gửi Socket.IO."""
        while not self.services.runtime_state.is_stop_requested():
            if errors_lock is not None:
                with errors_lock:
                    if consumer_errors:
                        break
            elif consumer_errors:
                break

            try:
                task = inspection_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if task is None:
                inspection_queue.task_done()
                break

            try:
                if task.is_no_data:
                    result = self._handle_no_data_task(task)
                else:
                    result = self._execute_judgment_task(task)

                if results_lock is not None:
                    with results_lock:
                        results.append(result)
                else:
                    results.append(result)

                self._send_client({"type": "judgment_item_result", "data": result})
            except Exception as error:
                result = {
                    "product_id": task.prepared.product_id,
                    "frame_id": task.frame["frame_id"],
                    "item_id": task.point["point_id"],
                    "session_id": task.prepared.session_id,
                    "status": "ERROR",
                    "overall": False,
                    "number_step": task.prepared.number_step,
                    "step": task.step,
                    "inspectors": {},
                    "message": str(error),
                }
                if results_lock is not None:
                    with results_lock:
                        results.append(result)
                else:
                    results.append(result)

                self._send_client({"type": "judgment_item_result", "data": result})

                if errors_lock is not None:
                    with errors_lock:
                        consumer_errors.append(error)
                else:
                    consumer_errors.append(error)
                break
            finally:
                inspection_queue.task_done()

    def _handle_no_data_task(self, task: InspectionTaskItem) -> dict[str, Any]:
        """Xử lý item NO_DATA (không có cấu hình hoặc thiếu calibration)."""
        judgment_path = self._save_no_data_result(
            task.prepared,
            task.frame,
            task.point,
            task.step,
            task.no_data_message,
        )
        return {
            "product_id": task.prepared.product_id,
            "frame_id": task.frame["frame_id"],
            "item_id": task.point["point_id"],
            "session_id": task.prepared.session_id,
            "status": "NO_DATA",
            "overall": False,
            "number_step": task.prepared.number_step,
            "step": task.step,
            "judgment_path": judgment_path,
            "inspectors": {},
            "message": task.no_data_message,
        }

    def _execute_judgment_task(self, task: InspectionTaskItem) -> dict[str, Any]:
        """Thực thi phán định AI và tạo kết quả cho một item đã chụp.

        Input: ``task`` chứa ảnh, cấu hình inspector và metadata của item.
        Output: Dict kết quả phán định, metadata và đường dẫn ảnh output.
        Errors: Lỗi từ ``run_summary`` hoặc xử lý output được truyền lên worker.
        """
        frame_id = task.frame["frame_id"]
        point_id = task.point["point_id"]
        image = task.image

        print(f"[STAGE2][WORKER] Bắt đầu Judment.run_summary cho frame={frame_id}, item={point_id}, step={task.step}")
        cfg_sw = getattr(self.services, "obj_config_software", None)
        if cfg_sw is None:
            try:
                from app.services.log.config_software import Config_SoftWare
                cfg_sw = Config_SoftWare()
            except Exception:
                cfg_sw = None

        training_context = {
            "session_id": task.prepared.session_id,
            "product_id": task.prepared.product_id,
            "frame_id": frame_id,
            "item_id": point_id,
            "enabled_inspectors": set(),
            "async_retrain": False,
        }
        if cfg_sw is not None and cfg_sw.get_open_retrain():
            training_context["enabled_inspectors"] = cfg_sw.get_enabled_retrain_inspectors()
            training_context["async_retrain"] = True

        raw_summary = self.services.obj_judment.run_summary(
            image=image,
            inspectors=task.inspectors,
            scale_mm_per_pixel=task.active_scale_mm_per_pixel,
            training_context=training_context,
        )
        summary = dict(raw_summary) if isinstance(raw_summary, dict) else {}
        summary["inspectors"] = {
            k: dict(v) if isinstance(v, dict) else v
            for k, v in summary.get("inspectors", {}).items()
        }
        print(
            f"[STAGE2][WORKER] Kết thúc phán định frame={frame_id}, item={point_id}: "
            f"status={summary.get('status')}, overall={summary.get('overall')}"
        )
        for inspector_name, inspector_result in summary.get("inspectors", {}).items():
            inspector_result["display_name"] = self.INSPECTOR_DISPLAY_NAMES.get(
                inspector_name,
                inspector_name,
            )
        judgment_path = self._output_url(
            self._session_item_dir(task.prepared, frame_id, point_id) / "judgment.jpg"
        )
        summary.update({
            "product_id": task.prepared.product_id,
            "frame_id": frame_id,
            "point_id": point_id,
            "item_id": point_id,
            "session_id": task.prepared.session_id,
            "number_step": task.prepared.number_step,
            "step": task.step,
            "iai": {key: task.point[key] for key in ("x", "y", "z")},
            "calibration": {
                "is_calibrated": task.is_calibrated,
                "scale_mm_per_pixel": task.active_scale_mm_per_pixel,
                "reason": task.calibration_reason,
            },
            "judgment_path": judgment_path,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        })
        judgment_path = self._save_judgment_result(
            image,
            task.prepared,
            frame_id,
            point_id,
            summary,
        )
        summary["judgment_path"] = judgment_path

        # Ghi log judgment theo chuẩn: chỉ ghi khi có hạng mục NG
        ng_errors: list[str] = []
        for inspector_name, inspector_result in summary.get("inspectors", {}).items():
            if inspector_result.get("ok") is False:
                errs = inspector_result.get("errors")
                if errs and isinstance(errs, list):
                    for err in errs:
                        err_str = str(err).strip()
                        if not err_str.startswith("🔵"):
                            err_str = f"🔵{err_str}"
                        ng_errors.append(err_str)
                else:
                    msg = inspector_result.get("message") or "Không đạt chuẩn"
                    display_name = inspector_result.get("display_name", inspector_name)
                    ng_errors.append(
                        f"🔵[{display_name}] NG - \"{display_name}\" - Quy định:\"Đạt chuẩn\" - Thực tế :\"{msg}\""
                    )

        if ng_errors:
            log_lines = [f"🔻Frame: {frame_id} Ảnh thứ: {point_id}"]
            log_lines.extend(ng_errors)
            self.services.send_judgment_log("\n".join(log_lines))

        # Đẩy dữ liệu vào hệ thống logging công nghiệp (CSV session chi tiết, IMG)
        if getattr(self.services, "queue_manage_log", None):
            try:
                status_str = "OK" if summary.get("overall") else "NG"
                inspectors = summary.get("inspectors", {})
                foreign_insp = inspectors.get("ForeignObjectInspector")
                anomaly_insp = inspectors.get("AnomalyPointInspector")
                stamp_insp = inspectors.get("StampItemInspector")

                # Đặt tên file ảnh chuẩn: Bắt đầu bằng OK_ hoặc NG_
                img_name = f"{status_str}_{task.prepared.session_id}_f{frame_id}_item_{point_id}"
                img_file_full = f"{img_name}.jpg"

                def _format_insp_entry(
                    insp_obj: dict | None,
                    default_theory: str,
                    default_reality: str,
                    default_msg: str,
                ) -> tuple[str, str, str, str]:
                    """Nếu inspector không được gọi/cấu hình trong phiên: status=NA, Theory=NA, Reality=N/A, message=NA."""
                    if not insp_obj or not isinstance(insp_obj, dict):
                        return "NA", "NA", "N/A", "NA"
                    if insp_obj.get("ok") is True:
                        status = "OK"
                    elif insp_obj.get("ok") is False:
                        status = "NG"
                    else:
                        status = str(insp_obj.get("status", "NA"))

                    theory = insp_obj.get("theory") or default_theory
                    reality = insp_obj.get("reality") or default_reality
                    msg = insp_obj.get("message") or default_msg
                    return status, str(theory), str(reality), str(msg)

                # Các cột hạng mục đã gỡ bỏ xuất mặc định NA để giữ tương thích cấu trúc CSV
                weld_status, weld_theory, weld_reality, weld_message = ("NA", "NA", "N/A", "NA")
                sensor_status, sensor_theory, sensor_reality, sensor_message = ("NA", "NA", "N/A", "NA")
                cover_status, cover_theory, cover_reality, cover_message = ("NA", "NA", "N/A", "NA")
                hole_status, hole_theory, hole_reality, hole_message = ("NA", "NA", "N/A", "NA")
                slit_status, slit_theory, slit_reality, slit_message = ("NA", "NA", "N/A", "NA")

                # 7. Foreign Object
                foreign_score = foreign_insp.get("score") if foreign_insp else None
                foreign_reality_val = f"Score: {foreign_score:.2f}" if isinstance(foreign_score, (int, float)) else "0.00"
                foreign_status, foreign_theory, foreign_reality, foreign_message = _format_insp_entry(
                    foreign_insp,
                    "Anomaly score <= 0.20",
                    foreign_reality_val,
                    "Đạt chuẩn" if foreign_insp and foreign_insp.get("ok") else "Phát hiện dị vật",
                )

                # 8. Anomaly Point (Kiểm tra điểm bất thường đa vùng)
                anom_total = (
                    anomaly_insp.get("standard_data", {}).get("total_boxes", 0)
                    if isinstance(anomaly_insp, dict)
                    else 0
                )
                anom_ok = (
                    anomaly_insp.get("runtime_data", {}).get("ok_count", 0)
                    if isinstance(anomaly_insp, dict)
                    else 0
                )
                anom_max_score = (
                    anomaly_insp.get("runtime_data", {}).get("max_score", anomaly_insp.get("score"))
                    if isinstance(anomaly_insp, dict)
                    else None
                )
                if anom_total > 0 and isinstance(anom_max_score, (int, float)):
                    anom_reality_val = f"{anom_ok}/{anom_total} vùng đạt (max: {anom_max_score:.3f})"
                elif isinstance(anom_max_score, (int, float)):
                    anom_reality_val = f"Score: {anom_max_score:.3f}"
                else:
                    anom_reality_val = "0.000"
                anomaly_status, anomaly_theory, anomaly_reality, anomaly_message = _format_insp_entry(
                    anomaly_insp,
                    f"Tất cả vùng <= ngưỡng ({anom_total} vùng)" if anom_total > 0 else "Anomaly score <= ngưỡng",
                    anom_reality_val,
                    "Đạt chuẩn" if anomaly_insp and anomaly_insp.get("ok") else "Phát hiện điểm bất thường",
                )

                # 9. Stamp (Kiểm tra Có/Không tem)
                stamp_total = (
                    stamp_insp.get("standard_data", {}).get("total_boxes", 0)
                    if isinstance(stamp_insp, dict)
                    else 0
                )
                stamp_present = (
                    stamp_insp.get("runtime_data", {}).get("present_count", 0)
                    if isinstance(stamp_insp, dict)
                    else 0
                )
                stamp_reality_val = (
                    f"{stamp_present}/{stamp_total} khung có tem"
                    if stamp_total > 0
                    else ("Đạt" if stamp_insp and stamp_insp.get("ok") else "Thiếu tem")
                )
                stamp_status, stamp_theory, stamp_reality, stamp_message = _format_insp_entry(
                    stamp_insp,
                    "Tất cả khung phải có tem",
                    stamp_reality_val,
                    "Đạt chuẩn" if stamp_insp and stamp_insp.get("ok") else "Thiếu tem",
                )

                csv_payload = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "session_id": task.prepared.session_id,
                    "product_id": task.prepared.product_id,
                    "product_name": getattr(task.prepared, "product_name", f"product_{task.prepared.product_id}"),
                    "frame_id": frame_id,
                    "item_id": point_id,
                    "overall_status": status_str,
                    # 1. Weld
                    "weld_status": weld_status,
                    "weld_theory": weld_theory,
                    "weld_reality": weld_reality,
                    "weld_message": weld_message,
                    # 2. Arm Sensor
                    "arm_sensor_status": sensor_status,
                    "arm_sensor_theory": sensor_theory,
                    "arm_sensor_reality": sensor_reality,
                    "arm_sensor_message": sensor_message,
                    # 3. Arm Cover
                    "arm_cover_status": cover_status,
                    "arm_cover_theory": cover_theory,
                    "arm_cover_reality": cover_reality,
                    "arm_cover_message": cover_message,
                    # 4. Hole
                    "hole_status": hole_status,
                    "hole_theory": hole_theory,
                    "hole_reality": hole_reality,
                    "hole_message": hole_message,
                    # 6. Slit
                    "slit_status": slit_status,
                    "slit_theory": slit_theory,
                    "slit_reality": slit_reality,
                    "slit_message": slit_message,
                    # 7. Foreign Object
                    "foreign_object_status": foreign_status,
                    "foreign_theory": foreign_theory,
                    "foreign_reality": foreign_reality,
                    "foreign_message": foreign_message,
                    # 8. Anomaly Point
                    "status_anomaly_point": anomaly_status,
                    "anomaly_point_status": anomaly_status,
                    "anomaly_theory": anomaly_theory,
                    "anomaly_reality": anomaly_reality,
                    "anomaly_message": anomaly_message,
                    # 9. Stamp
                    "status_stamp": stamp_status,
                    "stamp_status": stamp_status,
                    "stamp_theory": stamp_theory,
                    "stamp_reality": stamp_reality,
                    "stamp_message": stamp_message,
                    # Ảnh item
                    "image_name": img_file_full,
                    "image_path": img_file_full,
                }

                # Gửi chi tiết item vào file CSV session/{session_id}.csv (nếu open_csv được bật)
                if cfg_sw is None or getattr(cfg_sw, "open_csv", True):
                    self.services.queue_manage_log.put({
                        "type": "csv_item",
                        "session_id": task.prepared.session_id,
                        "msg": csv_payload,
                    })

                # Gửi ảnh phán định vào Log_img/ (nếu open_img được bật)
                if cfg_sw is None or getattr(cfg_sw, "open_img", True):
                    judgment_img = summary.get("judgment_image")
                    if not isinstance(judgment_img, type(image)):
                        judgment_img = image
                    raw_judgment_file = self._session_item_dir(task.prepared, frame_id, point_id) / "judgment.jpg"
                    self.services.queue_manage_log.put({
                        "type": "image",
                        "msg": judgment_img,
                        "source_file": str(raw_judgment_file),
                        "status": status_str,
                        "product_name": getattr(task.prepared, "product_name", f"product_{task.prepared.product_id}"),
                        "file_name": img_name,
                    })
            except Exception as log_err:
                print(f"[STAGE2] Lỗi gửi queue log: {log_err}")

        return summary

    def _process_point(
        self,
        prepared: Any,
        frame: dict[str, Any],
        point: dict[str, Any],
        step: int,
    ) -> dict[str, Any]:
        """Tương thích ngược: Xử lý đồng bộ một point (chụp và phán định trực tiếp)."""
        task = self._capture_point_task(prepared, frame, point, step)
        if task.is_no_data:
            return self._handle_no_data_task(task)
        return self._execute_judgment_task(task)

    def _send_client(self, payload: dict) -> None:
        """Đưa sự kiện phán định vào queue gửi Socket.IO."""
        self.services.queue_data_send_client.put(
            self._json_safe(self._strip_internal_images(payload))
        )

    @classmethod
    def _strip_internal_images(cls, value):
        """Loại ảnh NumPy nội bộ, giữ overlay và đường dẫn ảnh đã lưu."""
        if isinstance(value, np.ndarray):
            return None
        if isinstance(value, dict):
            stripped_dict = {}
            for key, child in value.items():
                if key in {
                    "image",
                    "judgment_image",
                    "inspector_images",
                    "overlay_data",
                }:
                    continue
                stripped_child = cls._strip_internal_images(child)
                if stripped_child is not None or not isinstance(child, np.ndarray):
                    stripped_dict[key] = stripped_child
            return stripped_dict
        if isinstance(value, (list, tuple)):
            stripped_list = [cls._strip_internal_images(child) for child in value]
            cleaned = [x for x in stripped_list if x is not None]
            return cleaned if isinstance(value, list) else tuple(cleaned)
        return value

    @staticmethod
    def _json_safe(value):
        """Chuyển payload judgment về kiểu có thể truyền qua Socket.IO."""
        try:
            return json.loads(json.dumps(value, ensure_ascii=False, default=str))
        except (TypeError, ValueError):
            return {"status": "NG", "message": "Payload judgment không hợp lệ."}

    def _session_item_dir(self, prepared, frame_id: str, point_id: str) -> Path:
        """Tạo thư mục lưu dữ liệu của một item trong một session."""
        output_dir = (
            PATH_FOLDER_OUTPUT_JUDGMENT
            / prepared.session_id
            / f"product_{prepared.product_id}"
            / f"face_{frame_id}"
            / f"item_{point_id}"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def _save_no_data_result(
        self,
        prepared,
        frame: dict,
        point: dict,
        step: int,
        message: str,
    ) -> str:
        """Lưu ảnh tham chiếu và result NO_DATA cho item chưa đủ dữ liệu chạy.

        Input: Dữ liệu prepared/frame/point, thứ tự step và nội dung message.
        Output: URL ảnh judgment đã lưu (copy từ ảnh point master nếu có).
        Errors: Không phát sinh; thiếu ảnh nguồn vẫn tạo ``result.json`` NO_DATA.
        """
        output_dir = self._session_item_dir(prepared, frame["frame_id"], point["point_id"])
        source_path = BASE_DIR / str(
            point["source"].get("path_img_point", "")
        ).replace("\\", "/")
        judgment_path = output_dir / "judgment.jpg"
        if source_path.exists():
            shutil.copy2(source_path, judgment_path)
        result = {
            "status": "NO_DATA",
            "overall": False,
            "step": step,
            "number_step": prepared.number_step,
            "message": message,
            "inspectors": {},
        }
        (output_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self._output_url(judgment_path)

    def _requires_calibration(self, inspectors: dict[str, Any]) -> bool:
        """Xác định item có chứa hạng mục đo cần calibration theo frame hay không."""
        if not isinstance(inspectors, dict):
            return False
        for inspector_name in self.LINE_BASED_INSPECTORS:
            inspector_config = inspectors.get(inspector_name)
            if isinstance(inspector_config, dict) and inspector_config:
                return True
        return False

    def _output_saver_worker(self) -> None:
        """Luồng Worker ghi file ảnh gốc, ảnh phán định và JSON kết quả xuống đĩa ngầm."""
        while True:
            try:
                task = self._output_save_queue.get(timeout=0.2)
            except queue.Empty:
                if self.services.runtime_state.is_stop_requested():
                    break
                continue

            if task is None:
                self._output_save_queue.task_done()
                break

            try:
                output_dir: Path = task["output_dir"]
                output_dir.mkdir(parents=True, exist_ok=True)

                # 1. Ghi ảnh phán định (nếu chưa được ghi trước đó)
                judgment_path = task.get("judgment_path")
                judgment_img = task.get("judgment_image")
                if not task.get("already_saved_judgment", False) and judgment_path and judgment_img is not None:
                    cv2.imwrite(str(judgment_path), judgment_img)

                # 2. Ghi ảnh gốc sau
                original_path = task.get("original_path")
                original_img = task.get("original_image")
                if original_path and original_img is not None:
                    cv2.imwrite(str(original_path), original_img)

                # 3. Ghi các ảnh inspector nếu có
                inspector_saves = task.get("inspector_saves") or []
                if inspector_saves:
                    inspector_dir = task.get("inspector_dir")
                    if inspector_dir:
                        inspector_dir.mkdir(parents=True, exist_ok=True)
                    for insp_path, insp_img in inspector_saves:
                        if insp_img is not None:
                            cv2.imwrite(str(insp_path), insp_img)

                # 4. Ghi result.json
                result_json_path = task.get("result_json_path")
                result_data = task.get("result_data")
                if result_json_path and result_data is not None:
                    result_json_path.write_text(
                        json.dumps(result_data, ensure_ascii=False, indent=2, default=str),
                        encoding="utf-8",
                    )
            except Exception as save_err:
                print(f"[STAGE2][ASYNC_OUTPUT] Lỗi ghi file kết quả: {save_err}")
            finally:
                self._output_save_queue.task_done()

    def _save_judgment_result(
        self,
        image,
        prepared,
        frame_id: str,
        point_id: str,
        summary: dict,
    ) -> str:
        """Lưu ảnh gốc, ảnh judgment và JSON kết quả của item (hỗ trợ cả bất đồng bộ và đồng bộ)."""
        output_dir = self._session_item_dir(prepared, frame_id, point_id)
        original_path = output_dir / "original.jpg"
        judgment_path = output_dir / "judgment.jpg"
        judgment_url = self._output_url(judgment_path)

        judgment_image = summary.get("judgment_image")
        if not isinstance(judgment_image, type(image)):
            judgment_image = image

        # Ghi file judgment.jpg ĐỒNG BỘ NGAY LẬP TỨC (chỉ tốn ~10ms):
        # Đảm bảo khi trả về URL và gửi Socket.IO, file đã chắc chắn tồn tại trên đĩa 100%,
        # triệt tiêu hoàn toàn race condition 404 khi client tải ảnh realtime.
        already_saved_judgment = False
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(judgment_path), judgment_image)
            already_saved_judgment = True
        except Exception as write_err:
            print(f"[STAGE2] Cảnh báo lỗi ghi đồng bộ judgment.jpg: {write_err}")

        inspector_images = summary.get("inspector_images", {})
        inspector_dir = output_dir / "inspectors"
        inspector_image_paths = {}
        inspector_saves = []
        if isinstance(inspector_images, dict):
            for inspector_name, inspector_image in inspector_images.items():
                if isinstance(inspector_image, type(image)):
                    inspector_path = inspector_dir / f"{inspector_name}.jpg"
                    inspector_image_paths[inspector_name] = self._output_url(inspector_path)
                    inspector_saves.append((inspector_path, inspector_image))
        summary["inspector_image_paths"] = inspector_image_paths

        result_data = {
            key: value for key, value in self._strip_internal_images(summary).items()
        }

        save_task = {
            "output_dir": output_dir,
            "original_path": original_path,
            "original_image": image,
            "judgment_path": judgment_path,
            "judgment_image": judgment_image,
            "already_saved_judgment": already_saved_judgment,
            "inspector_dir": inspector_dir,
            "inspector_saves": inspector_saves,
            "result_json_path": output_dir / "result.json",
            "result_data": result_data,
        }

        # Nếu luồng ghi ngầm output_saver_thread đang hoạt động, đẩy vào hàng đợi không chặn
        if self._output_saver_thread and self._output_saver_thread.is_alive():
            try:
                self._output_save_queue.put(save_task, timeout=1.0)
            except queue.Full:
                print(f"[STAGE2][ASYNC_OUTPUT] Hàng đợi lưu đĩa đầy, fallback ghi đồng bộ frame {frame_id} item {point_id}")
                self._write_output_disk_sync(save_task)
        else:
            # Fallback đồng bộ khi chạy đơn lẻ hoặc trong unit test không bật thread
            self._write_output_disk_sync(save_task)

        return judgment_url

    @staticmethod
    def _write_output_disk_sync(task: dict[str, Any]) -> None:
        """Ghi kết quả ra đĩa đồng bộ (dùng làm fallback)."""
        output_dir: Path = task["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        # Ghi ảnh phán định (nếu chưa được ghi trước đó)
        if not task.get("already_saved_judgment", False) and task.get("judgment_path") and task.get("judgment_image") is not None:
            cv2.imwrite(str(task["judgment_path"]), task["judgment_image"])
        cv2.imwrite(str(task["original_path"]), task["original_image"])
        if task.get("inspector_saves"):
            task["inspector_dir"].mkdir(parents=True, exist_ok=True)
            for insp_path, insp_img in task["inspector_saves"]:
                cv2.imwrite(str(insp_path), insp_img)
        task["result_json_path"].write_text(
            json.dumps(task["result_data"], ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    @staticmethod
    def _output_url(path: Path) -> str:
        """Đổi đường dẫn app/output thành URL static cho client."""
        try:
            relative = path.relative_to(PATH_FOLDER_OUTPUT).as_posix()
            return f"{URL_PATH_OUTPUT}/{relative}"
        except ValueError:
            return f"{URL_PATH_OUTPUT}/{path.name}"

    def _move_with_retry(self, point: dict) -> bool:
        """Gửi lệnh di chuyển với số lần thử cấu hình trong IAIConfig."""
        attempts = max(1, int(getattr(self.services.obj_iai_config, "move_retry_count", 3)))
        timeout = float(getattr(self.services.obj_iai_config, "move_timeout", 4))
        for attempt in range(1, attempts + 1):
            if self.services.obj_iai_control.move_to_point(
                point["x"], point["y"], point["z"], timeout=timeout
            ):
                return True
            self.services.send_judgment_log(
                f"⚠️ Di chuyển frame {point.get('frame_id', '')}/point "
                f"{point['point_id']} thất bại lần {attempt}/{attempts}"
            )
        return False

    def _capture_with_retry(self):
        """Chụp ảnh camera với số lần thử cấu hình."""
        attempts = max(1, int(getattr(self.services.obj_iai_config, "capture_retry_count", 3)))
        timeout = float(getattr(self.services.obj_iai_config, "capture_timeout", 1))
        for attempt in range(1, attempts + 1):
            status, image = self.services.obj_camera.capture_once(timeout=timeout)
            if status and image is not None:
                return image
            self.services.send_judgment_log(f"⚠️ Camera lỗi lần {attempt}/{attempts}")
        raise RuntimeError("Camera không chụp được ảnh")

    def _save_image(self, image, prepared, frame_id: str, point_id: str) -> str:
        """Lưu ảnh point vào app/output và trả về đường dẫn tương đối."""
        output_dir = self._session_item_dir(prepared, frame_id, point_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / "original.jpg"
        if not cv2.imwrite(str(image_path), image):
            raise RuntimeError(f"Không lưu được ảnh phán định: {image_path}")
        return self._output_url(image_path)
