import gc
import threading
from typing import Any
import numpy as np
import torch
from ultralytics import YOLO

from app.config import YoloDetectObjectConfig
from app.model import BaseAI

CLASS_FRAME = 0
CLASS_STAMP = 1


def normalize_obb(
    x: float, y: float, w: float, h: float, theta_rad: float
) -> tuple[float, float, float, float, float]:
    """Chuẩn hóa OBB sao cho w luôn là cạnh dài, h luôn là cạnh ngắn.
    Đưa góc về khoảng [-pi/2, pi/2) để đồng bộ hệ quy chiếu.
    """
    if w < h:
        w, h = h, w
        theta_rad += np.pi / 2.0

    theta_rad = ((theta_rad + np.pi / 2.0) % np.pi) - (np.pi / 2.0)
    return float(x), float(y), float(w), float(h), float(theta_rad)


def inspect_stamp_alignment(
    frame_obb: tuple[float, float, float, float, float] | np.ndarray,
    stamp_obb: tuple[float, float, float, float, float] | np.ndarray,
    stamp_corners: np.ndarray,
    tolerances: dict[str, Any],
) -> dict[str, Any]:
    """Tính toán độ lệch hình học giữa Khung (0: frame) và Tem (1: stamp) trong hệ tọa độ cục bộ của Khung.
    Tất cả các thông số khoảng cách tính theo đơn vị Pixel (px), góc tính theo độ (°).
    """
    # 1. Chuẩn hóa OBB
    xf, yf, wf, hf, theta_f = normalize_obb(*frame_obb)
    xs, ys, ws, hs, theta_s = normalize_obb(*stamp_obb)

    # 2. Vector lệch tâm trong hệ tọa độ ảnh
    dx = xs - xf
    dy = ys - yf

    # 3. Chiếu vector lệch tâm sang hệ tọa độ cục bộ của Frame
    cos_f = np.cos(theta_f)
    sin_f = np.sin(theta_f)

    du = dx * cos_f + dy * sin_f
    dv = -dx * sin_f + dy * cos_f
    magnitude = np.hypot(du, dv)
    direction_deg = np.degrees(np.arctan2(dv, du))

    # 4. Độ lệch góc xoay tương đối (chuẩn hóa [-90, 90])
    d_theta_rad = theta_s - theta_f
    d_theta_deg = ((np.degrees(d_theta_rad) + 90.0) % 180.0) - 90.0

    # 5. Kiểm tra bao hàm đa giác (Containment Check với margin)
    shifted_corners = stamp_corners - np.array([xf, yf], dtype=np.float32)
    rotation_matrix = np.array(
        [[cos_f, -sin_f], [sin_f, cos_f]], dtype=np.float32
    )
    local_corners = np.dot(shifted_corners, rotation_matrix)

    margin = float(tolerances.get("margin", 5.0))
    half_wf = (wf / 2.0) - margin
    half_hf = (hf / 2.0) - margin

    if half_wf <= 0 or half_hf <= 0:
        is_contained = False
    else:
        is_inside_u = bool(np.all(np.abs(local_corners[:, 0]) <= half_wf))
        is_inside_v = bool(np.all(np.abs(local_corners[:, 1]) <= half_hf))
        is_contained = bool(is_inside_u and is_inside_v)

    # 6. Đánh giá ngưỡng dung sai
    max_du = float(tolerances.get("max_du", 15.0))
    max_dv = float(tolerances.get("max_dv", 15.0))
    max_deg = float(tolerances.get("max_deg", 3.0))

    pass_u = bool(abs(du) <= max_du)
    pass_v = bool(abs(dv) <= max_dv)
    pass_angle = bool(abs(d_theta_deg) <= max_deg)

    is_ok = bool(pass_u and pass_v and pass_angle and is_contained)

    return {
        "status": "OK" if is_ok else "NG",
        "metrics": {
            "du": round(float(du), 2),
            "dv": round(float(dv), 2),
            "magnitude": round(float(magnitude), 2),
            "direction_deg": round(float(direction_deg), 2),
            "delta_angle_deg": round(float(d_theta_deg), 2),
            "is_contained": is_contained,
            "unit": "pixel",
        },
        "details": {
            "pass_position_u": pass_u,
            "pass_position_v": pass_v,
            "pass_rotation": pass_angle,
            "pass_containment": is_contained,
        },
        "frame_normalized": {
            "x": float(xf),
            "y": float(yf),
            "w": float(wf),
            "h": float(hf),
            "theta_deg": round(float(np.degrees(theta_f)), 2),
        },
        "stamp_normalized": {
            "x": float(xs),
            "y": float(ys),
            "w": float(ws),
            "h": float(hs),
            "theta_deg": round(float(np.degrees(theta_s)), 2),
        },
    }


def process_yolo_obb_result(
    result: Any, tolerances: dict[str, Any]
) -> dict[str, Any]:
    """Bóc tách kết quả OBB từ Ultralytics YOLO cho 2 nhãn 0: frame và 1: stamp."""
    obb = getattr(result, "obb", None)
    if obb is None or len(obb) == 0:
        return {
            "status": "NG",
            "error": "Không phát hiện đối tượng OBB nào",
            "metrics": {
                "du": 0.0,
                "dv": 0.0,
                "magnitude": 0.0,
                "direction_deg": 0.0,
                "delta_angle_deg": 0.0,
                "is_contained": False,
                "unit": "pixel",
            },
            "details": {
                "pass_position_u": False,
                "pass_position_v": False,
                "pass_rotation": False,
                "pass_containment": False,
            },
            "counts": {"frame": 0, "stamp": 0},
            "raw_detections": [],
        }

    classes = obb.cls.cpu().numpy().astype(int)
    xywhr = obb.xywhr.cpu().numpy()  # (N, 5) [x, y, w, h, rad]
    xyxyxyxy = obb.xyxyxyxy.cpu().numpy()  # (N, 4, 2)
    conf = obb.conf.cpu().numpy() if hasattr(obb, "conf") else np.ones(len(classes))

    frame_indices = np.where(classes == CLASS_FRAME)[0]
    stamp_indices = np.where(classes == CLASS_STAMP)[0]

    raw_detections: list[dict[str, Any]] = []
    for i in range(len(classes)):
        raw_detections.append(
            {
                "class_id": int(classes[i]),
                "class_name": "frame" if classes[i] == CLASS_FRAME else "stamp",
                "conf": float(conf[i]),
                "xywhr": [float(v) for v in xywhr[i]],
                "corners": xyxyxyxy[i].tolist(),
            }
        )

    count_frame = len(frame_indices)
    count_stamp = len(stamp_indices)

    if count_frame != 1 or count_stamp != 1:
        return {
            "status": "NG",
            "error": (
                f"Số lượng đối tượng không hợp lệ: "
                f"frame={count_frame} (cần 1), stamp={count_stamp} (cần 1)"
            ),
            "metrics": {
                "du": 0.0,
                "dv": 0.0,
                "magnitude": 0.0,
                "direction_deg": 0.0,
                "delta_angle_deg": 0.0,
                "is_contained": False,
                "unit": "pixel",
            },
            "details": {
                "pass_position_u": False,
                "pass_position_v": False,
                "pass_rotation": False,
                "pass_containment": False,
            },
            "counts": {"frame": count_frame, "stamp": count_stamp},
            "raw_detections": raw_detections,
        }

    frame_idx = frame_indices[0]
    stamp_idx = stamp_indices[0]

    eval_result = inspect_stamp_alignment(
        frame_obb=xywhr[frame_idx],
        stamp_obb=xywhr[stamp_idx],
        stamp_corners=xyxyxyxy[stamp_idx],
        tolerances=tolerances,
    )
    eval_result["counts"] = {"frame": 1, "stamp": 1}
    eval_result["raw_detections"] = raw_detections
    eval_result["frame_corners"] = xyxyxyxy[frame_idx].tolist()
    eval_result["stamp_corners"] = xyxyxyxy[stamp_idx].tolist()
    return eval_result


class ModelYoloOBB(BaseAI):
    """Mô hình YOLO OBB chuyên dụng phát hiện và đánh giá độ lệch tem."""

    def __init__(self, config: YoloDetectObjectConfig):
        self.config = config
        self.model: YOLO | None = None
        self._predict_lock = threading.Lock()
        self.load_model()
        self.warmup()

    def load_model(self) -> None:
        """Nạp YOLO OBB model."""
        if self.model is None:
            self.model = YOLO(self.config.path_model)

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        return image

    def predict(self, image: np.ndarray):
        """Thực thi inference YOLO OBB."""
        if self.model is None:
            raise RuntimeError("Mô hình YOLO OBB chưa được nạp.")
        image = self.preprocess(image)
        with self._predict_lock:
            return self.model.predict(
                source=image,
                imgsz=self.config.image_size,
                conf=self.config.confidence,
                iou=self.config.iou,
                device=self.config.device,
                verbose=False,
            )

    def warmup(self) -> None:
        """Khởi động mô hình."""
        if self.model is None:
            raise RuntimeError("Mô hình YOLO OBB chưa được nạp.")
        dummy = np.zeros(
            (self.config.image_size, self.config.image_size, 3), dtype=np.uint8
        )
        self.predict(dummy)

    def unload(self) -> None:
        """Giải phóng bộ nhớ."""
        self.model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def inspect_alignment(
        self, image: np.ndarray, tolerances: dict[str, Any]
    ) -> dict[str, Any]:
        """Thực hiện phát hiện và đánh giá độ lệch tem trên ảnh đầu vào."""
        preds = self.predict(image)
        if not preds or len(preds) == 0:
            return {
                "status": "NG",
                "error": "Mô hình không trả về kết quả",
                "metrics": {
                    "du": 0.0,
                    "dv": 0.0,
                    "magnitude": 0.0,
                    "direction_deg": 0.0,
                    "delta_angle_deg": 0.0,
                    "is_contained": False,
                    "unit": "pixel",
                },
                "details": {
                    "pass_position_u": False,
                    "pass_position_v": False,
                    "pass_rotation": False,
                    "pass_containment": False,
                },
                "counts": {"frame": 0, "stamp": 0},
                "raw_detections": [],
            }
        return process_yolo_obb_result(preds[0], tolerances)
