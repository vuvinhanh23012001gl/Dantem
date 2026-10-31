import json
import os
from enum import Enum
from .base_config import BaseConfig
from app.config import PATH_FILE_DATA_CONFIG_IAI

class ModeState(Enum):
    NORMOL = 0
    PAUSE = 1
    STOP = 2
    WAIT_ORG = 3
    WAIT_ORIGIN_SENSOR = 16
    RETURNED_OR = 4
    WAIT_AUTO = 5
    AUTO = 6
    TOUCH_SAFETY = 8
    WAIT_TAKE_PRODUCT = 9
    PUT_PRODUCT = 10
    RUN_STEP = 11
    RUN_STEP_1 = 12
    RUN_STEP_3 = 14
    RUN_STEP_4 = 15

class IAIConfig(BaseConfig):
    def __init__(self):
        self.path_config_iai = PATH_FILE_DATA_CONFIG_IAI
        # =========================
        # LIMIT X DEFAULT
        # =========================
        self.limit_x_min_default = 0
        self.limit_x_max_default = 1000
        # =========================
        # LIMIT Y DEFAULT
        # =========================
        self.limit_y_min_default = 0
        self.limit_y_max_default = 1000
        # =========================
        # LIMIT Z DEFAULT
        # =========================
        self.limit_z_min_default = 0
        self.limit_z_max_default = 1000
        # =========================
        # HOME POSITION
        # =========================
        self.home_x = 0
        self.home_y = 0
        self.home_z = 0
        self.command_status = "status_all:"
        self.command_move_to_origin = "move_to_org:"
        self.command_stop = "stop:"
        self.command_reset_stop = "refesh_stop:"
        self.command_pause = "pause:"
        self.command_resume = "refesh_pause:"
        self.status_returned_origin = "has_returned_org:"
        self.input_poll_interval = 0.05
        self.queue_timeout = 0.01
        self.move_retry_count = 3
        self.capture_retry_count = 3
        self.move_timeout = 4.0
        self.capture_timeout = 1.0
        self.t_settle_ms = 40.0
        self.t_hold_safety_ms = 15.0
        self.blur_threshold = 100.0
        self.auto_retrigger_on_blur = True
        self.max_retrigger_count = 1
        self.load()

    # =========================
    # BACKWARD COMPATIBLE PROPERTIES
    # =========================
    @property
    def limit_x_min(self):
        return self.limit_x_min_default

    @limit_x_min.setter
    def limit_x_min(self, value):
        self.limit_x_min_default = value

    @property
    def limit_x_max(self):
        return self.limit_x_max_default

    @limit_x_max.setter
    def limit_x_max(self, value):
        self.limit_x_max_default = value

    @property
    def limit_y_min(self):
        return self.limit_y_min_default

    @limit_y_min.setter
    def limit_y_min(self, value):
        self.limit_y_min_default = value

    @property
    def limit_y_max(self):
        return self.limit_y_max_default

    @limit_y_max.setter
    def limit_y_max(self, value):
        self.limit_y_max_default = value

    @property
    def limit_z_min(self):
        return self.limit_z_min_default

    @limit_z_min.setter
    def limit_z_min(self, value):
        self.limit_z_min_default = value

    @property
    def limit_z_max(self):
        return self.limit_z_max_default

    @limit_z_max.setter
    def limit_z_max(self, value):
        self.limit_z_max_default = value

    # ==========================================================
    # LOAD CONFIG
    # ==========================================================
    def load(self):

        # Nếu chưa có file config thì tạo mới
        if not os.path.exists(self.path_config_iai):
            self.save()
            return

        with open(self.path_config_iai, "r", encoding="utf-8") as file:
            data = json.load(file)

        # =========================
        # LIMIT X
        # =========================
        self.limit_x_min_default = data.get(
            "limit_x_min_default",
            data.get("limit_x_min", self.limit_x_min_default)
        )

        self.limit_x_max_default = data.get(
            "limit_x_max_default",
            data.get("limit_x_max", self.limit_x_max_default)
        )

        # =========================
        # LIMIT Y
        # =========================
        self.limit_y_min_default = data.get(
            "limit_y_min_default",
            data.get("limit_y_min", self.limit_y_min_default)
        )

        self.limit_y_max_default = data.get(
            "limit_y_max_default",
            data.get("limit_y_max", self.limit_y_max_default)
        )

        # =========================
        # LIMIT Z
        # =========================
        self.limit_z_min_default = data.get(
            "limit_z_min_default",
            data.get("limit_z_min", self.limit_z_min_default)
        )

        self.limit_z_max_default = data.get(
            "limit_z_max_default",
            data.get("limit_z_max", self.limit_z_max_default)
        )

        self.move_retry_count = data.get(
            "move_retry_count", self.move_retry_count
        )
        self.capture_retry_count = data.get(
            "capture_retry_count", self.capture_retry_count
        )
        self.move_timeout = data.get("move_timeout", self.move_timeout)
        self.capture_timeout = data.get("capture_timeout", self.capture_timeout)

        # =========================
        # HOME POSITION
        # =========================
        self.home_x = data.get(
            "home_x",
            self.home_x
        )

        self.home_y = data.get(
            "home_y",
            self.home_y
        )

        self.home_z = data.get(
            "home_z",
            self.home_z
        )
        self.command_status = data.get("command_status", self.command_status)
        self.command_move_to_origin = data.get(
            "command_move_to_origin", self.command_move_to_origin
        )
        self.command_stop = data.get("command_stop", self.command_stop)
        self.command_reset_stop = data.get(
            "command_reset_stop", self.command_reset_stop
        )
        self.command_pause = data.get("command_pause", self.command_pause)
        self.command_resume = data.get("command_resume", self.command_resume)
        self.status_returned_origin = data.get(
            "status_returned_origin", self.status_returned_origin
        )
        self.input_poll_interval = data.get(
            "input_poll_interval", self.input_poll_interval
        )
        self.queue_timeout = data.get("queue_timeout", self.queue_timeout)
        self.t_settle_ms = float(data.get("t_settle_ms", self.t_settle_ms))
        self.t_hold_safety_ms = float(data.get("t_hold_safety_ms", self.t_hold_safety_ms))
        self.blur_threshold = float(data.get("blur_threshold", self.blur_threshold))
        self.auto_retrigger_on_blur = bool(data.get("auto_retrigger_on_blur", self.auto_retrigger_on_blur))
        self.max_retrigger_count = int(data.get("max_retrigger_count", self.max_retrigger_count))

    # ==========================================================
    # SAVE CONFIG
    # ==========================================================
    def save(self):

        data = {

            # =========================
            # LIMIT X
            # =========================
            "limit_x_min_default": self.limit_x_min_default,
            "limit_x_max_default": self.limit_x_max_default,

            # =========================
            # LIMIT Y
            # =========================
            "limit_y_min_default": self.limit_y_min_default,
            "limit_y_max_default": self.limit_y_max_default,

            # =========================
            # LIMIT Z
            # =========================
            "limit_z_min_default": self.limit_z_min_default,
            "limit_z_max_default": self.limit_z_max_default,

            # =========================
            # HOME POSITION
            # =========================
            "home_x": self.home_x,
            "home_y": self.home_y,
            "home_z": self.home_z,
            "command_status": self.command_status,
            "command_move_to_origin": self.command_move_to_origin,
            "command_stop": self.command_stop,
            "command_reset_stop": self.command_reset_stop,
            "command_pause": self.command_pause,
            "command_resume": self.command_resume,
            "status_returned_origin": self.status_returned_origin,
            "input_poll_interval": self.input_poll_interval,
            "queue_timeout": self.queue_timeout,
            "move_retry_count": self.move_retry_count,
            "capture_retry_count": self.capture_retry_count,
            "move_timeout": self.move_timeout,
            "capture_timeout": self.capture_timeout,
            "t_settle_ms": self.t_settle_ms,
            "t_hold_safety_ms": self.t_hold_safety_ms,
            "blur_threshold": self.blur_threshold,
            "auto_retrigger_on_blur": self.auto_retrigger_on_blur,
            "max_retrigger_count": self.max_retrigger_count,
        }

        with open(self.path_config_iai, "w", encoding="utf-8") as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )
    def get_dict(self) -> dict:
        return {

            # =========================
            # LIMIT X DEFAULT
            # =========================
            "limit_x_min_default": self.limit_x_min_default,
            "limit_x_max_default": self.limit_x_max_default,
            "limit_x_min": self.limit_x_min_default,
            "limit_x_max": self.limit_x_max_default,

            # =========================
            # LIMIT Y DEFAULT
            # =========================
            "limit_y_min_default": self.limit_y_min_default,
            "limit_y_max_default": self.limit_y_max_default,
            "limit_y_min": self.limit_y_min_default,
            "limit_y_max": self.limit_y_max_default,

            # =========================
            # LIMIT Z DEFAULT
            # =========================
            "limit_z_min_default": self.limit_z_min_default,
            "limit_z_max_default": self.limit_z_max_default,
            "limit_z_min": self.limit_z_min_default,
            "limit_z_max": self.limit_z_max_default,

            # =========================
            # HOME POSITION
            # =========================
            "home_x": self.home_x,
            "home_y": self.home_y,
            "home_z": self.home_z,
            "command_status": self.command_status,
            "command_move_to_origin": self.command_move_to_origin,
            "command_stop": self.command_stop,
            "command_reset_stop": self.command_reset_stop,
            "command_pause": self.command_pause,
            "command_resume": self.command_resume,
            "status_returned_origin": self.status_returned_origin,
            "input_poll_interval": self.input_poll_interval,
            "queue_timeout": self.queue_timeout,
            "move_retry_count": self.move_retry_count,
            "capture_retry_count": self.capture_retry_count,
            "move_timeout": self.move_timeout,
            "capture_timeout": self.capture_timeout,
            "t_settle_ms": self.t_settle_ms,
            "t_hold_safety_ms": self.t_hold_safety_ms,
            "blur_threshold": self.blur_threshold,
            "auto_retrigger_on_blur": self.auto_retrigger_on_blur,
            "max_retrigger_count": self.max_retrigger_count,
        }