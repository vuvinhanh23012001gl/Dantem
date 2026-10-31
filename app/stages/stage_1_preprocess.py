import json
import threading
from datetime import datetime, timezone
from dataclasses import dataclass, replace
from pathlib import Path

from app.config import (
    PATH_CONFIG_POINTS,
    PATH_FILE_DATA_CONFIG_JUDMENT_LAW,
    PATH_PRODUCT_CHOOSE_PRODUCT,
)
from app.container import EnumMode, ServiceContainer
from app.core.context import RuntimePipelineState


@dataclass
class PreparedProduct:
    """Dữ liệu đã chuẩn hóa để Stage 2 xử lý tuần tự."""

    product_id: str
    frames: list[dict]
    frame_calibrations: dict[str, dict]
    scale_mm_per_pixel: float
    session_id: str
    number_step: int

    @property
    def faces(self) -> list[dict]:
        return self.frames

    @property
    def face_calibrations(self) -> dict[str, dict]:
        return self.frame_calibrations

class StagePreprocess:
    """Đọc và chuẩn hóa dữ liệu sản phẩm trước khi điều khiển IAI."""
    def __init__(self, services: ServiceContainer):

        self.services = services
        self.protocol_connection_OK = False
        self._cached_product: PreparedProduct | None = None
        self._cache_mtimes: dict[str, float] = {}
        self._cache_lock = threading.Lock()
        self._is_dirty = True
        self._last_session_id = ""
        self._cycle_sub_counter = 0
        self.preload()

    def preload(self) -> bool:
        """Nạp dữ liệu lần đầu khi khởi động phần mềm."""
        with self._cache_lock:
            try:
                self._load_and_cache_locked()
                print(
                    "[STAGE1] Đã preload sẵn dữ liệu product="
                    f"{self._cached_product.product_id} vào RAM ({len(self._cached_product.frames)} frames, "
                    f"{self._cached_product.number_step} points)."
                )
                return True
            except Exception as error:
                print(f"[STAGE1] Chưa thể preload cấu hình lúc khởi động: {error}")
                return False

    def mark_dirty(self, source: str = "") -> None:
        """Đánh dấu cấu hình đã thay đổi từ UI và reload ngay vào RAM."""
        with self._cache_lock:
            self._is_dirty = True
            try:
                self._load_and_cache_locked()
                product_id = self._cached_product.product_id if self._cached_product else "None"
                steps = self._cached_product.number_step if self._cached_product else 0
                msg = f"🔄 Đã cập nhật cấu hình vào RAM ({source}): product {product_id}, {steps} points."
                print(f"[STAGE1] {msg}")
                self.services.send_judgment_log(msg)
            except Exception as error:
                print(f"[STAGE1] Lỗi reload cấu hình sau thay đổi ({source}): {error}")
                self.services.send_judgment_log(f"⚠️ Cấu hình mới không hợp lệ ({source}): {error}")

    def _has_files_changed_on_disk(self) -> bool:
        """Kiểm tra timestamp mtime của 4 file cấu hình (tốn ~2us, không đọc nội dung file)."""
        config_files = [
            PATH_PRODUCT_CHOOSE_PRODUCT,
            PATH_CONFIG_POINTS,
            PATH_FILE_DATA_CONFIG_JUDMENT_LAW,
                ]
        for file_str in config_files:
            p = Path(file_str)
            if not p.exists():
                return True
            try:
                current_mtime = p.stat().st_mtime
                if self._cache_mtimes.get(file_str) != current_mtime:
                    return True
            except OSError:
                return True
        return False

    def _load_and_cache_locked(self) -> None:
        """Đọc 4 file JSON và nạp vào _cached_product (chỉ chạy khi nạp lần đầu hoặc đổi cấu hình)."""
        prepared = self._load_product_data()
        self._cached_product = prepared
        self._is_dirty = False
        config_files = [
            PATH_PRODUCT_CHOOSE_PRODUCT,
            PATH_CONFIG_POINTS,
            PATH_FILE_DATA_CONFIG_JUDMENT_LAW,
                ]
        mtimes = {}
        for file_str in config_files:
            p = Path(file_str)
            mtimes[file_str] = p.stat().st_mtime if p.exists() else 0.0
        self._cache_mtimes = mtimes

    def run(self):
        """Lấy dữ liệu từ RAM cho chu kỳ này và chuyển sang Stage 2.

        Input: dữ liệu sản phẩm đã nạp sẵn trong cache RAM.
        Output: lưu PreparedProduct (với session_id mới) vào container và chuyển mode sang transform.
        Errors: ValueError nếu dữ liệu cấu hình thiếu hoặc không hợp lệ.
        """
        with self._cache_lock:
            if self._cached_product is None or self._is_dirty or self._has_files_changed_on_disk():
                print("[STAGE1] Phát hiện cấu hình chưa có hoặc có thay đổi trên đĩa -> Đang nạp lại...")
                self._load_and_cache_locked()

            # Cấp phát session_id mới cho chu kỳ này, KHÔNG đọc lại file
            now_str = datetime.now(timezone.utc).strftime("session_%Y%m%dT%H%M%S%fZ")
            if now_str == self._last_session_id:
                self._cycle_sub_counter += 1
                new_session_id = f"{now_str}_{self._cycle_sub_counter}"
            else:
                self._last_session_id = now_str
                self._cycle_sub_counter = 0
                new_session_id = now_str
            cycle_product = replace(self._cached_product, session_id=new_session_id)

        print(
            "[STAGE1] Chuẩn bị chu kỳ từ RAM: product="
            f"{cycle_product.product_id}, frames={len(cycle_product.frames)}, "
            f"number_step={cycle_product.number_step}, session={cycle_product.session_id}"
        )
        self.services.prepared_product = cycle_product
        self.services.runtime_state.set_pipeline_state(
            RuntimePipelineState.READY
        )
        self.services.set_mode(EnumMode.MODE_TRANSFORM)
        self.services.send_judgment_log(
            f"✅ Stage 1 hoàn tất (RAM): product {cycle_product.product_id}, "
            f"{cycle_product.number_step} point, session {cycle_product.session_id}."
        )
        return cycle_product

    def _read_json(self, path: str) -> dict:
        """Đọc một file JSON object.

        Input: ``path`` là đường dẫn file JSON.
        Output: object JSON dạng dict.
        Errors: ``ValueError`` nếu file không tồn tại, sai JSON hoặc không phải object.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise ValueError(f"Không tìm thấy file dữ liệu: {file_path}")
        try:
            with file_path.open("r", encoding="utf-8-sig") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Không đọc được file {file_path}: {error}") from error
        if not isinstance(data, dict):
            raise ValueError(f"Dữ liệu {file_path} phải là object JSON")
        return data

    def _load_product_data(self) -> PreparedProduct:
        """Ghép bốn nguồn JSON thành danh sách frame/point có judgment config."""
        choose_data = self._read_json(PATH_PRODUCT_CHOOSE_PRODUCT)
        product_id = str(choose_data.get("product", "")).strip()
        if not product_id:
            raise ValueError("Chưa có sản phẩm hiện tại trong choose_product_select.json")

        points_data = self._read_json(PATH_CONFIG_POINTS).get(product_id)
        law_data = self._read_json(PATH_FILE_DATA_CONFIG_JUDMENT_LAW).get(product_id)
        calibration_data = {}
        if not isinstance(points_data, dict) or not points_data:
            raise ValueError(f"Không có points cho product {product_id}")
        if not isinstance(law_data, dict):
            raise ValueError(f"Không có config judgment cho product {product_id}")
        print(
            f"[STAGE1] Đã đọc product={product_id}: "
            f"frames_points={len(points_data)}, judgment_frames={len(law_data)}"
        )

        frames = []
        for frame_id in sorted(points_data, key=self._sort_key):
            raw_points = points_data[frame_id]
            frame_law = law_data.get(str(frame_id), {})
            if not isinstance(raw_points, dict) or not isinstance(frame_law, dict):
                raise ValueError(f"Frame {frame_id} của product {product_id} không hợp lệ")
            points = []
            for point_id in sorted(raw_points, key=self._sort_key):
                point = raw_points[point_id]
                if not isinstance(point, dict):
                    raise ValueError(f"Point {frame_id}/{point_id} không hợp lệ")
                try:
                    coordinates = {
                        "x": int(point["x"]),
                        "y": int(point["y"]),
                        "z": int(point["z"]),
                    }
                except (KeyError, TypeError, ValueError) as error:
                    raise ValueError(
                        f"Point {frame_id}/{point_id} thiếu tọa độ IAI"
                    ) from error
                judgment = frame_law.get(str(point_id))
                if not isinstance(judgment, dict) or not judgment:
                    judgment = {}
                print(
                    f"[STAGE1] frame={frame_id}, item={point_id}, "
                    f"inspectors={list(judgment.keys()) if judgment else []}"
                )
                points.append({
                    "point_id": str(point_id),
                    **coordinates,
                    "judgment": judgment,
                    "source": point,
                })
            if points:
                frames.append({"frame_id": str(frame_id), "face_id": str(frame_id), "points": points})
        if not frames:
            raise ValueError(f"Product {product_id} không có frame/point hợp lệ")

        frame_calibrations: dict[str, dict] = {}
        for frame in frames:
            frame_id = frame["frame_id"]
            calibration_info = {
                "is_calibrated": True,
                "scale_mm_per_pixel": 1.0,
                "reason": "Mặc định (đã loại bỏ tính năng calibration)",
            }
            frame_calibrations[frame_id] = calibration_info
            frame["calibration"] = calibration_info

        scale = 1.0
        number_step = sum(len(frame["points"]) for frame in frames)
        session_id = datetime.now(timezone.utc).strftime("session_%Y%m%dT%H%M%S%fZ")
        return PreparedProduct(
            product_id,
            frames,
            frame_calibrations,
            scale,
            session_id,
            number_step,
        )

    @staticmethod
    def _sort_key(value: str) -> tuple[int, str]:
        """Sắp xếp ID số trước ID chữ."""
        text = str(value)
        return (0, f"{int(text):020d}") if text.isdigit() else (1, text)

    @staticmethod
    def _read_frame_scale(calibration_data: dict, frame_id: str) -> dict:
        """Đọc trạng thái calibration của một frame theo product hiện tại.

        Input: ``calibration_data`` dạng `{frame_id: calibration_dict}` và
            ``frame_id`` cần kiểm tra.
        Output: Dict thống nhất gồm:
            - ``is_calibrated`` (bool): frame đã có hệ số hợp lệ hay chưa.
            - ``scale_mm_per_pixel`` (float | None): hệ số mm/pixel nếu hợp lệ.
            - ``reason`` (str): mô tả ngắn trạng thái dữ liệu calibration.
        Errors: Không phát sinh; dữ liệu thiếu/sai kiểu được trả về dưới dạng
            ``is_calibrated=False`` cùng thông điệp tương ứng.
        """
        frame_data = calibration_data.get(str(frame_id)) if isinstance(calibration_data, dict) else None
        if not isinstance(frame_data, dict):
            return {
                "is_calibrated": False,
                "scale_mm_per_pixel": None,
                "reason": "Frame chưa có dữ liệu calibration.",
            }

        result = frame_data.get("result_parameters")
        if not isinstance(result, dict):
            return {
                "is_calibrated": False,
                "scale_mm_per_pixel": None,
                "reason": "Thiếu result_parameters trong dữ liệu calibration.",
            }

        scale_raw = result.get("scale_mm_per_pixel")
        try:
            scale_value = float(scale_raw)
        except (TypeError, ValueError):
            return {
                "is_calibrated": False,
                "scale_mm_per_pixel": None,
                "reason": "scale_mm_per_pixel không hợp lệ.",
            }

        if scale_value <= 0:
            return {
                "is_calibrated": False,
                "scale_mm_per_pixel": None,
                "reason": "scale_mm_per_pixel phải lớn hơn 0.",
            }

        return {
            "is_calibrated": True,
            "scale_mm_per_pixel": scale_value,
            "reason": "Calibration hợp lệ.",
        }

    @staticmethod
    def _pick_default_scale(frame_calibrations: dict[str, dict]) -> float:
        """Lấy scale hợp lệ đầu tiên để giữ tương thích luồng cũ.

        Input: Mapping trạng thái calibration theo frame.
        Output: Hệ số mm/pixel đầu tiên hợp lệ; nếu không có trả về 1.0.
        Errors: Không phát sinh.
        """
        for calibration_info in frame_calibrations.values():
            if not isinstance(calibration_info, dict):
                continue
            if not calibration_info.get("is_calibrated"):
                continue
            scale_value = calibration_info.get("scale_mm_per_pixel")
            if isinstance(scale_value, (int, float)) and float(scale_value) > 0:
                return float(scale_value)
        return 1.0
        

    def check_protocol_connect_com(self):
        """Kiểm tra phần cứng sẵn sàng (chế độ độc lập / Ethernet TCP)."""
        self.protocol_connection_OK = True
        return True
    


      
            


                
                
             
             
        

            
            
       














