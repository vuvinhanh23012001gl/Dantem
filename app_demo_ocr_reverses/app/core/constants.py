from enum import Enum


class OrientationStatus(str, Enum):
    """Standardized orientation statuses for industrial label inspection."""
    NORMAL = "NORMAL"                    # 0° upright
    ROTATED_90 = "ROTATED_90"            # 90° clockwise
    INVERTED = "INVERTED"                # 180° upside-down
    ROTATED_270 = "ROTATED_270"          # 270° clockwise (90° counter-clockwise)
    MIRROR = "MIRROR"                    # Left-right horizontal mirror
    MIXED = "MIXED_ORIENTATION"          # Multiple lines with conflicting orientations
    UNKNOWN = "UNKNOWN"                  # No text detected or unreadable


class InspectionJudgement(str, Enum):
    """Industrial inspection pass/fail judgement."""
    OK = "OK"
    NG = "NG"


SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")

ANGLE_TO_STATUS = {
    0: OrientationStatus.NORMAL.value,
    90: OrientationStatus.ROTATED_90.value,
    180: OrientationStatus.INVERTED.value,
    270: OrientationStatus.ROTATED_270.value,
}

STATUS_LABELS_VI = {
    OrientationStatus.NORMAL.value: "Đúng chiều (0°)",
    OrientationStatus.ROTATED_90.value: "Xoay 90° (90° CW)",
    OrientationStatus.INVERTED.value: "Bị ngược (180°)",
    OrientationStatus.ROTATED_270.value: "Xoay 270° (270° CW)",
    OrientationStatus.MIRROR.value: "Lật gương trái-phải (Mirror)",
    OrientationStatus.MIXED.value: "Nhiều hướng chữ lẫn lộn (Mixed)",
    OrientationStatus.UNKNOWN.value: "Không xác định (Unknown)",
}
