import math
from pathlib import Path
from typing import List, Tuple, Union
import cv2
import numpy as np


def read_image_unicode(image_path: Union[str, Path]) -> np.ndarray:
    """Read an image from disk supporting Unicode/Vietnamese paths on Windows."""
    path_str = str(image_path)
    raw_bytes = np.fromfile(path_str, dtype=np.uint8)
    if raw_bytes.size == 0:
        raise ValueError(f"Empty or unreadable file: {path_str}")
    img = cv2.imdecode(raw_bytes, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Failed to decode image: {path_str}")
    return img


def save_image_unicode(image_path: Union[str, Path], img: np.ndarray) -> bool:
    """Save an image to disk supporting Unicode/Vietnamese paths on Windows."""
    path_obj = Path(image_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    ext = path_obj.suffix.lower() or ".png"
    success, encoded = cv2.imencode(ext, img)
    if not success:
        return False
    encoded.tofile(str(path_obj))
    return True


def order_quad_points(pts: np.ndarray) -> np.ndarray:
    """
    Order 4 corner points as [top-left, top-right, bottom-right, bottom-left]
    based on x-sort and y-comparison.
    """
    rect = cv2.minAreaRect(pts.astype(np.float32))
    box = cv2.boxPoints(rect)
    points = sorted(list(box), key=lambda x: x[0])

    if points[1][1] > points[0][1]:
        index_a, index_d = 0, 1
    else:
        index_a, index_d = 1, 0

    if points[3][1] > points[2][1]:
        index_b, index_c = 2, 3
    else:
        index_b, index_c = 3, 2

    return np.array(
        [points[index_a], points[index_b], points[index_c], points[index_d]],
        dtype=np.float32,
    )


def compute_skew_angle_deg(ordered_pts: np.ndarray, is_vertical: bool) -> float:
    """
    Compute the continuous geometric tilt/skew angle in degrees within (-45, +45]
    relative to the nearest cardinal axis (horizontal or vertical).
    Distinguishes perspective/mounting tilt from 90/180/270 cardinal rotation.
    """
    p0, p1, p2, p3 = ordered_pts
    if not is_vertical:
        # Top edge vector from left to right
        dx = float(p1[0] - p0[0])
        dy = float(p1[1] - p0[1])
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
    else:
        # Left edge vector from top to bottom
        dx = float(p3[0] - p0[0])
        dy = float(p3[1] - p0[1])
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad) - 90.0

    # Normalize into (-45, 45]
    while angle_deg <= -45.0:
        angle_deg += 90.0
    while angle_deg > 45.0:
        angle_deg -= 90.0
    return round(angle_deg, 2)


def crop_text_region(
    img: np.ndarray,
    poly: Union[np.ndarray, List[List[float]]],
    vertical_aspect_ratio_thresh: float = 1.5,
) -> Tuple[np.ndarray, int, int, bool, float, List[int], List[List[int]]]:
    """
    Extract a perspective-rectified text line crop from the original image
    without modifying the original image's coordinate system.

    Returns:
        crop: Perspective-rectified sub-image (H x W x C)
        width: Crop width in pixels
        height: Crop height in pixels
        is_vertical: True if height / width >= vertical_aspect_ratio_thresh
        skew_angle: Continuous geometric skew/tilt angle in degrees (-45, 45]
        bbox: Axis-aligned [x_min, y_min, x_max, y_max] on the original image
        polygon: 4-point polygon [[x0, y0], ...] on the original image
    """
    pts = np.array(poly, dtype=np.float32).reshape(-1, 2)
    ordered = order_quad_points(pts)

    w = int(
        max(
            np.linalg.norm(ordered[0] - ordered[1]),
            np.linalg.norm(ordered[2] - ordered[3]),
            1.0,
        )
    )
    h = int(
        max(
            np.linalg.norm(ordered[0] - ordered[3]),
            np.linalg.norm(ordered[1] - ordered[2]),
            1.0,
        )
    )

    dst_pts = np.array(
        [[0, 0], [w, 0], [w, h], [0, h]],
        dtype=np.float32,
    )
    M = cv2.getPerspectiveTransform(ordered, dst_pts)
    crop = cv2.warpPerspective(
        img,
        M,
        (w, h),
        borderMode=cv2.BORDER_REPLICATE,
        flags=cv2.INTER_CUBIC,
    )

    is_vertical = (float(h) / float(max(w, 1))) >= vertical_aspect_ratio_thresh
    skew_angle = compute_skew_angle_deg(ordered, is_vertical)

    x_coords = pts[:, 0]
    y_coords = pts[:, 1]
    img_h, img_w = img.shape[:2]
    x_min = max(0, int(np.floor(np.min(x_coords))))
    y_min = max(0, int(np.floor(np.min(y_coords))))
    x_max = min(img_w, int(np.ceil(np.max(x_coords))))
    y_max = min(img_h, int(np.ceil(np.max(y_coords))))
    bbox = [x_min, y_min, x_max, y_max]
    polygon = [[int(round(p[0])), int(round(p[1]))] for p in ordered]

    return crop, w, h, is_vertical, skew_angle, bbox, polygon


def restore_upright_image(
    img: np.ndarray, angle: int, is_mirrored: bool = False
) -> np.ndarray:
    """
    Produce a human-readable upright version of the image for visual comparison,
    given the detected initial orientation (angle & mirror state).
    """
    out = img.copy()
    if is_mirrored:
        out = cv2.flip(out, 1)
    if angle == 90:
        out = cv2.rotate(out, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif angle == 180:
        out = cv2.rotate(out, cv2.ROTATE_180)
    elif angle == 270:
        out = cv2.rotate(out, cv2.ROTATE_90_CLOCKWISE)
    return out
