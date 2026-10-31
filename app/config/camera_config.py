from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, ClassVar

@dataclass
class CameraConfig:
    """Cấu hình runtime ánh xạ trực tiếp vào camera feature file.

    Input: dictionary field cần cập nhật từ web.
    Output: object cấu hình và dictionary JSON-compatible để gửi tới camera.
    Errors: ``ValueError`` khi giá trị không hợp lệ.
    """

    acquisition_frame_rate: float = 30.0
    exposure_time: float = 10000.0
    gain: float = 0.0
    exposure_auto: str = "Off"
    trigger_mode: str = "Off"
    trigger_selector: str = "FrameStart"
    gamma: float = 1.0
    black_level: float = 0.0
    balance_white_auto: str = "Off"
    balance_ratio_red: float = 229.0
    balance_ratio_green: float = 128.0
    balance_ratio_blue: float = 272.0

    OPERATOR_FIELDS: ClassVar[frozenset[str]] = frozenset({
        "acquisition_frame_rate", "exposure_time", "gain", "exposure_auto",
        "trigger_mode", "trigger_selector", "gamma", "black_level",
    })

    @classmethod
    def from_feature_file(cls, path: str) -> "CameraConfig":
        """Đọc các giá trị camera từ file GenApi ``features.cfg``.

        Input: đường dẫn file feature dạng tab-separated.
        Output: ``CameraConfig`` chứa các giá trị đã đọc được.
        Errors: ``ValueError`` nếu file không tồn tại hoặc có giá trị sai.
        """
        config = cls()
        try:
            lines = Path(path).read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise ValueError(f"Cannot read feature file: {error}") from error

        for line in lines:
            parts = line.split("\t")
            if not parts or len(parts) < 2:
                continue
            node_name = parts[0]
            value = parts[-1].strip()
            try:
                if node_name == "AcquisitionFrameRate" and len(parts) == 2:
                    config.acquisition_frame_rate = float(value)
                elif node_name == "ExposureTime" and "ExposureTimeSelector=Common" in line:
                    config.exposure_time = float(value)
                elif node_name == "Gain" and "GainSelector=AnalogAll" in line:
                    config.gain = float(value)
                elif node_name == "BlackLevel" and "BlackLevelSelector=AnalogAll" in line:
                    config.black_level = float(value)
                elif node_name == "Gamma" and len(parts) == 2:
                    config.gamma = float(value)
                elif node_name == "ExposureAuto" and len(parts) == 2:
                    config.exposure_auto = value
                elif node_name == "TriggerMode" and "TriggerSelector=FrameStart" in line:
                    config.trigger_mode = value
                elif node_name == "TriggerSelector" and len(parts) == 2:
                    config.trigger_selector = value
                elif node_name == "BalanceWhiteAuto" and len(parts) == 2:
                    config.balance_white_auto = value
                elif node_name == "BalanceRatio" and "BalanceRatioSelector=Red" in line:
                    config.balance_ratio_red = float(value)
                elif node_name == "BalanceRatio" and "BalanceRatioSelector=Green" in line:
                    config.balance_ratio_green = float(value)
                elif node_name == "BalanceRatio" and "BalanceRatioSelector=Blue" in line:
                    config.balance_ratio_blue = float(value)
            except ValueError as error:
                raise ValueError(f"Invalid {node_name} value: {value}") from error
        config.validate()
        return config

    def update_operator_values(self, values: dict[str, Any]) -> None:
        """Cập nhật field vận hành, không cho operator sửa white balance.

        Input: dictionary chỉ chứa ``OPERATOR_FIELDS``.
        Output: object được cập nhật tại chỗ.
        Errors: ``ValueError`` nếu có field bảo vệ hoặc giá trị sai.
        """
        protected_fields = set(values) - self.OPERATOR_FIELDS
        if protected_fields:
            raise ValueError(
                "Protected or unknown camera fields: "
                + ", ".join(sorted(protected_fields))
            )
        for field, value in values.items():
            setattr(self, field, value)
        self.validate()

    def validate(self) -> None:
        """Kiểm tra miền giá trị số cơ bản trước khi áp dụng camera.

        Input: không có.
        Output: không trả về nếu hợp lệ.
        Errors: ``ValueError`` nếu giá trị âm hoặc gamma không dương.
        """
        if self.acquisition_frame_rate <= 0:
            raise ValueError("acquisition_frame_rate must be greater than 0")
        if self.exposure_time < 0 or self.gain < 0 or self.black_level < 0:
            raise ValueError("exposure_time, gain and black_level must be non-negative")
        if self.gamma <= 0:
            raise ValueError("gamma must be greater than 0")
        if min(self.balance_ratio_red, self.balance_ratio_green, self.balance_ratio_blue) < 0:
            raise ValueError("white balance ratios must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển cấu hình thành dictionary để trả về API hoặc ghi JSON.

        Input: không có.
        Output: dictionary gồm cả field vận hành và calibration.
        Errors: không phát sinh.
        """
        return asdict(self)