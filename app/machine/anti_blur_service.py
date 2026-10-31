import json
import math
import os
import threading
from typing import Any
import cv2
import numpy as np


class AntiBlurService:
    """Service tính toán tham số chống rung nhòe cơ khí (Stop-and-Shoot) và kiểm tra độ nét ảnh."""

    _config_lock = threading.RLock()
    _cached_config: dict[str, Any] | None = None
    _cached_config_mtime_ns: int | None = None
    _cached_config_path: str | None = None

    DEFAULT_CONFIG = {
        "fov_mm": 40.0,
        "sensor_px": 2000,
        "b_max_px": 0.5,
        "a0_um": 50.0,
        "fn_hz": 50.0,
        "zeta": 0.08,
        "t_exp_ms": 2.0,
        "is_hardware_trigger": False,
        "t_safety_ms": 5.0,
        "t_settle_ms": 40.0,
        "t_hold_safety_ms": 15.0,
        "blur_threshold": 100.0,
        "auto_retrigger_on_blur": True,
        "max_retrigger_count": 1,
        "extra_settle_ms": 20.0,
    }

    @classmethod
    def get_config_path(cls) -> str:
        try:
            from app.config.path_config import PATH_FILE_DATA_CONFIG_ANTI_BLUR
            return PATH_FILE_DATA_CONFIG_ANTI_BLUR
        except ImportError:
            return "app/storage/anti_blur.json"

    @classmethod
    def load_config(cls) -> dict[str, Any]:
        """Đọc cấu hình anti-blur, dùng cache đến khi file cấu hình thay đổi.

        Input: Không có; đường dẫn cấu hình được lấy từ ``get_config_path``.
        Output: Dict cấu hình độc lập, đã ghép các giá trị mặc định.
        Errors: Trả về cấu hình mặc định nếu file lỗi; lỗi tạo file mặc định
            được truyền lên caller.
        """
        path = cls.get_config_path()
        with cls._config_lock:
            if not os.path.exists(path):
                return cls.save_config(cls.DEFAULT_CONFIG)
            try:
                mtime_ns = os.stat(path).st_mtime_ns
                if (
                    cls._cached_config is not None
                    and cls._cached_config_path == path
                    and cls._cached_config_mtime_ns == mtime_ns
                ):
                    return dict(cls._cached_config)

                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config = dict(cls.DEFAULT_CONFIG)
                if isinstance(data, dict):
                    config.update(data)
                cls._cached_config = dict(config)
                cls._cached_config_mtime_ns = os.stat(path).st_mtime_ns
                cls._cached_config_path = path
                return dict(config)
            except Exception:
                return dict(cls.DEFAULT_CONFIG)

    @classmethod
    def save_config(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Chuẩn hóa và lưu cấu hình anti-blur, đồng thời cập nhật cache.

        Input: ``data`` là dict các giá trị cấu hình cần lưu.
        Output: Dict cấu hình đã chuẩn hóa theo kiểu và giá trị mặc định.
        Errors: Lỗi tạo thư mục, ghi file hoặc đọc metadata file được truyền lên.
        """
        path = cls.get_config_path()
        config = dict(cls.DEFAULT_CONFIG)
        if isinstance(data, dict):
            for key in cls.DEFAULT_CONFIG:
                if key in data:
                    target_type = type(cls.DEFAULT_CONFIG[key])
                    try:
                        if target_type is bool:
                            config[key] = bool(data[key])
                        elif target_type is int:
                            config[key] = int(data[key])
                        elif target_type is float:
                            config[key] = float(data[key])
                        else:
                            config[key] = data[key]
                    except (ValueError, TypeError):
                        pass
        with cls._config_lock:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            cls._cached_config = dict(config)
            cls._cached_config_mtime_ns = os.stat(path).st_mtime_ns
            cls._cached_config_path = path
        return dict(config)

    @staticmethod
    def calculate_recommended_timers(
        fov_mm: float,
        sensor_px: int,
        b_max_px: float = 0.5,
        a0_um: float = 50.0,
        fn_hz: float = 50.0,
        zeta: float = 0.08,
        t_exp_ms: float = 2.0,
        is_hardware_trigger: bool = False,
        t_safety_ms: float | None = None,
    ) -> dict[str, float]:
        """Tính toán các bộ định thời T_settle, T_hold và T_total_stop theo đặc tả URD.

        Args:
            fov_mm: Chiều rộng vùng nhìn theo phương trục IAI (mm).
            sensor_px: Số điểm ảnh của cảm biến theo phương chuyển động (pixels).
            b_max_px: Độ nhòe tối đa cho phép trên ảnh (pixels, mặc định 0.5 px).
            a0_um: Biên độ sai số Positioning Band khi PEND bật (micromet, ví dụ 50 um).
            fn_hz: Tần số dao động riêng của hệ gá cơ khí (Hz, ví dụ 50 Hz).
            zeta: Hệ số tắt dần dao động cơ khí (Damping Ratio, ví dụ 0.08).
            t_exp_ms: Thời gian phơi sáng của Camera (Exposure Time, ms).
            is_hardware_trigger: True nếu dùng xung trigger cứng I/O, False nếu dùng Software Trigger qua SDK.
            t_safety_ms: Thời gian đệm an toàn tùy chọn (ms).

        Returns:
            Dict chứa các giá trị tính toán:
                - resolution_um_per_px (R)
                - allowed_vibration_um (A_allow)
                - t_settle_ms (T_settle)
                - t_hold_ms (T_hold)
                - t_total_stop_ms (T_total_stop)
        """
        if sensor_px <= 0:
            raise ValueError("sensor_px phải lớn hơn 0")
        if fov_mm <= 0:
            raise ValueError("fov_mm phải lớn hơn 0")

        # 1. Độ phân giải không gian R (um/pixel)
        resolution_um = (fov_mm * 1000.0) / float(sensor_px)

        # 2. Biên độ dao động cho phép A_allow (um)
        allowed_vibration_um = b_max_px * resolution_um

        # 3. Thời gian chờ ổn định cơ khí T_settle (ms)
        if a0_um > allowed_vibration_um and fn_hz > 0 and zeta > 0:
            omega_factor = 2.0 * math.pi * fn_hz * zeta
            amplitude_ratio = a0_um / allowed_vibration_um
            t_settle_ms = (1000.0 / omega_factor) * math.log(amplitude_ratio)
        else:
            t_settle_ms = 5.0

        # 4. Thời gian giữ trục đứng yên T_hold (ms)
        if is_hardware_trigger:
            t_trig_delay_ms = 0.1
            safety_ms = 2.0 if t_safety_ms is None else float(t_safety_ms)
        else:
            t_trig_delay_ms = 10.0
            safety_ms = 5.0 if t_safety_ms is None else float(t_safety_ms)

        t_hold_ms = t_trig_delay_ms + t_exp_ms + safety_ms

        # 5. Tổng thời gian dừng trục tại 1 điểm chụp
        t_total_stop_ms = t_settle_ms + t_hold_ms

        return {
            "resolution_um_per_px": round(resolution_um, 4),
            "allowed_vibration_um": round(allowed_vibration_um, 4),
            "t_settle_ms": round(t_settle_ms, 2),
            "t_hold_ms": round(t_hold_ms, 2),
            "t_total_stop_ms": round(t_total_stop_ms, 2),
        }

    @staticmethod
    def evaluate_sharpness(
        image: np.ndarray,
        threshold: float = 100.0,
    ) -> tuple[bool, float]:
        """Kiểm tra độ nét của ảnh dựa trên phương sai toán tử Laplacian (Laplacian Variance).

        Args:
            image: Khung hình numpy (BGR hoặc Grayscale).
            threshold: Ngưỡng tối thiểu để coi là ảnh sắc nét (mặc định 100.0).

        Returns:
            Tuple (is_sharp: bool, sharpness_score: float).
        """
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            return False, 0.0

        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif len(image.shape) == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
        else:
            gray = image

        # Tính toán phương sai Laplacian
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_sharp = laplacian_var >= threshold

        return is_sharp, round(laplacian_var, 2)
