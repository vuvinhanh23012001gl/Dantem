import threading
import logging
import cv2
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union

from app.engines.AI_model_process.frame_patch_core_object_detector import (
    FramePatchCoreObjectDetector,
)
from app.config.ai_config import FOREIGN_CLASS_NAME_VIETNAMESE_MAP
from app.utils.opencv_tool import Tool_OpenCv2
from .base_ai import BaseJudgerAI, JudgmentResult

logger = logging.getLogger(__name__)

class ForeignObjectDetector(BaseJudgerAI):
    """Bộ phán định dị vật (Foreign Object Detector) trên bề mặt sản phẩm.

    Kết hợp mô hình PatchCore để xác định các vùng bất thường và mô hình YOLO Object
    để nhận diện đối tượng dị vật thực sự trong vùng bất thường đó.
    """

    INSPECTOR_NAME = "ForeignObjectInspector"

    def __init__(
        self,
        foreign_object_model: Optional[FramePatchCoreObjectDetector] = None,
        foreign_service: Optional[Any] = None,
    ) -> None:
        """Khởi tạo detector phát hiện dị vật.

        Args:
            foreign_object_model (FramePatchCoreObjectDetector, optional): Instance kết hợp
                giữa PatchCore và YOLO object detector cố định.
            foreign_service (Any, optional): Service nạp động mô hình PatchCore theo
                từng point (product_id, frame_id, item_id).

        Raises:
            TypeError: Nếu cả hai tham số đều None hoặc model truyền vào không hợp lệ.
        """
        super().__init__()
        if foreign_object_model is None and foreign_service is None:
            raise TypeError("foreign_object_model hoặc foreign_service phải được cung cấp")
        if foreign_object_model is not None and not hasattr(
            foreign_object_model, "detect_anomaly_objects_with_heatmap"
        ):
            raise TypeError(
                "foreign_object_model phải có phương thức detect_anomaly_objects_with_heatmap"
            )
        self.foreign_object_model = foreign_object_model
        self.foreign_service = foreign_service
        self._runtime_save_slots = threading.BoundedSemaphore(4)

    def _save_runtime_crop(self, product_id, frame_id, item_id, image, roi_id=0) -> None:
        try:
            self.foreign_service.save_runtime_image_for_training(
                product_id, frame_id, item_id, image, roi_id=roi_id,
            )
        except (OSError, ValueError):
            logger.exception("Không lưu được ảnh runtime dị vật vùng %s", roi_id)
        finally:
            self._runtime_save_slots.release()

    def define(
        self,
        img: np.ndarray,
        x1: Union[int, List[Dict[str, Any]]],
        y1: Optional[int] = None,
        x2: Optional[int] = None,
        y2: Optional[int] = None,
        threshold: float = 0.0,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Chạy các vùng độc lập; giữ hỗ trợ lời gọi bốn tọa độ cũ."""
        if not isinstance(x1, list):
            if y1 is None or x2 is None or y2 is None:
                raise ValueError("Thiếu tọa độ ROI")
            return self._define_single(img, x1, y1, x2, y2, threshold, **kwargs)
        if not isinstance(img, np.ndarray) or img.size == 0:
            raise ValueError("img đầu vào không được rỗng")
        if not x1:
            raise ValueError("Danh sách vùng dị vật không được rỗng")
        annotated = img.copy()
        boxes = []
        for box in x1:
            left, top, right, bottom = (int(box[key]) for key in ("x1", "y1", "x2", "y2"))
            coords = (left, top, right, bottom)
            if min(left, top) < 0 or right > img.shape[1] or bottom > img.shape[0] or right <= left or bottom <= top:
                raise ValueError(f'Tọa độ vùng dị vật "{box.get("name", box["id"])}" không hợp lệ')
            name = str(box.get("name") or f'Dị vật {box["id"]}')
            options = {**kwargs, "roi_id": box["id"],
                       "saveRuntimeImages": box.get("saveRuntimeImages", False),
                       "_annotated_image": annotated, "_allow_missing_model": True}
            runtime = self._define_single(
                img, left, top, right, bottom,
                **options,
            )
            runtime.update({**box, "name": name, "bbox_roi": list(coords)})
            box_ok = not runtime.get("missing_model") and not runtime.get("detections")
            Tool_OpenCv2.draw_labeled_roi(
                annotated, coords, f"{name} [{'OK' if box_ok else 'NG'}]",
                (0, 255, 0) if box_ok else (0, 0, 255),
            )
            runtime.pop("image", None)
            boxes.append(runtime)
        return {"boxes": boxes, "image": annotated}

    def _define_single(
        self,
        img: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        threshold: float = 0.0,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Trích xuất dữ liệu bất thường và phát hiện dị vật runtime từ ảnh gốc và ROI.

        Gọi ``detect_anomaly_objects_with_heatmap`` để tính điểm số bất thường (score),
        bản đồ nhiệt (heatmap), và nhận diện dị vật (detections) trong vùng bất thường.
        Ảnh runtime đầu ra chỉ vẽ vùng lỗi và box dị vật; không phủ heatmap lên ROI
        để tránh che các lớp vẽ khác (polygon, line, ...).

        Args:
            img (np.ndarray): Mảng ảnh gốc đầu vào (định dạng BGR/RGB).
            x1 (int): Tọa độ X góc trái trên của vùng kiểm tra (ROI).
            y1 (int): Tọa độ Y góc trái trên của vùng kiểm tra (ROI).
            x2 (int): Tọa độ X góc phải dưới của vùng kiểm tra (ROI).
            y2 (int): Tọa độ Y góc phải dưới của vùng kiểm tra (ROI).
            threshold (float, optional): Tham số cũ được giữ để tương thích, không dùng.
            **kwargs: Các tham số bổ sung như product_id, frame_id, item_id.

        Returns:
            Dict[str, Any]: Dictionary chứa:
                - "score" (float): Điểm bất thường của toàn vùng ảnh ROI.
                - "heatmap" (np.ndarray | None): Bản đồ nhiệt trực quan vùng bất thường.
                - "detections" (List[Dict[str, Any]]): Danh sách các dị vật phát hiện bởi YOLO.
                - "roi" (Dict[str, int]): Tọa độ ROI x1, y1, x2, y2 đã kiểm tra.
                - "image" (np.ndarray): Ảnh đã vẽ vùng lỗi/dị vật, không phủ heatmap ROI.

        Raises:
            ValueError: Nếu ảnh rỗng, tọa độ ROI không hợp lệ hoặc thiếu thông tin point.
            RuntimeError: Nếu chưa có model khả dụng.
        """
        if not isinstance(img, np.ndarray) or img.size == 0:
            raise ValueError("img đầu vào không được rỗng")
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"Tọa độ ROI không hợp lệ: x1={x1}, y1={y1}, x2={x2}, y2={y2}")

        model = self.foreign_object_model
        if model is None and self.foreign_service is not None:
            product_id = kwargs.get("product_id")
            frame_id = kwargs.get("frame_id")
            item_id = kwargs.get("item_id")
            if product_id is None or frame_id is None or item_id is None:
                raise ValueError(
                    f"Thiếu thông tin product_id, frame_id, item_id để nạp mô hình: {kwargs}"
                )
            try:
                model = self.foreign_service.get_detector_engine(
                    product_id, frame_id, item_id, roi_id=kwargs.get("roi_id", 0)
                )
            except FileNotFoundError:
                if not kwargs.get("_allow_missing_model"):
                    raise
                return {"missing_model": True, "score": 0.0, "detections": [],
                        "anomaly_boxes": [], "roi": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}}
        if model is None:
            raise RuntimeError("Chưa có foreign_object_model để thực thi")

        result = model.detect_anomaly_objects_with_heatmap(
            img, x1, y1, x2, y2
        )

        score = float(result.get("score", 0.0))
        heatmap = result.get("heatmap")
        detections: List[Dict[str, Any]] = result.get("detections", [])
        anomaly_boxes: List[Tuple[int, int, int, int]] = result.get("anomaly_boxes", [])

        # Lưu ảnh crop ROI runtime phục vụ train PatchCore nếu cờ saveRuntimeImages được bật
        save_runtime_images = kwargs.get("saveRuntimeImages", False)
        if str(save_runtime_images).lower() == "true":
            p_id = kwargs.get("product_id")
            f_id = kwargs.get("frame_id")
            i_id = kwargs.get("item_id")
            if p_id is not None and f_id is not None and i_id is not None and self.foreign_service is not None:
                if self._runtime_save_slots.acquire(blocking=False):
                    roi_img = img[y1:y2, x1:x2].copy()
                    try:
                        threading.Thread(
                            target=self._save_runtime_crop,
                            args=(p_id, f_id, i_id, roi_img),
                            kwargs={"roi_id": kwargs.get("roi_id", 0)},
                            daemon=True,
                        ).start()
                    except RuntimeError:
                        self._runtime_save_slots.release()
                        logger.exception("Không khởi động được tác vụ lưu ảnh dị vật")
                else:
                    logger.warning("Bỏ qua ảnh runtime dị vật vùng %s: hàng đợi lưu đang đầy",
                                   kwargs.get("roi_id", 0))

        # Tạo bản sao ảnh để vẽ kết quả trực quan phục vụ UI
        annotated_image = kwargs.get("_annotated_image")
        if not isinstance(annotated_image, np.ndarray):
            annotated_image = img.copy()

        # Chỉ vẽ khung và nhãn vùng lỗi, không phủ heatmap để tránh che lớp vẽ khác.
        for idx, abox in enumerate(anomaly_boxes):
            px, py, pw, ph = (int(v) for v in abox)
            Tool_OpenCv2.draw_labeled_roi(
                annotated_image,
                (px, py, px + pw, py + ph),
                f"Vùng lỗi {idx + 1}",
                (0, 215, 255),
                thickness=2,
            )

        # Vẽ đối tượng dị vật phát hiện bởi YOLO bên trong các vùng bất thường.
        if detections:
            for det in detections:
                bbox = det.get("bbox", {})
                bx1 = int(round(bbox.get("x1", 0)))
                by1 = int(round(bbox.get("y1", 0)))
                bx2 = int(round(bbox.get("x2", 0)))
                by2 = int(round(bbox.get("y2", 0)))
                class_name = det.get("class_name", "Dị vật")
                conf = det.get("confidence", 0.0)
                label = f"{class_name} {conf:.2f}"
                # Viền màu đỏ nổi bật (0, 0, 255), độ dày 2px
                cv2.rectangle(annotated_image, (bx1, by1), (bx2, by2), (0, 0, 255), 2)
                # Vẽ nền chữ nhật màu đỏ chữ trắng
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                bg_y1 = max(0, by1 - th - 8)
                cv2.rectangle(annotated_image, (bx1, bg_y1), (bx1 + tw + 6, by1), (0, 0, 255), -1)
                cv2.putText(
                    annotated_image,
                    label,
                    (bx1 + 3, by1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

        return {
            "score": score,
            "heatmap": heatmap,
            "detections": detections,
            "objects": detections,
            "anomaly_boxes": anomaly_boxes,
            "roi": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            "image": annotated_image,
        }

    def compare(
        self,
        standard_data: Any,
        runtime_data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Phán định theo dị vật YOLO, không dùng điểm PatchCore làm ngưỡng OK/NG.

        Quy tắc phán định:
        Có dị vật: NG. Không có dị vật: OK, bất kể điểm PatchCore.
        Thiếu model là lỗi cấu hình và vẫn NG.

        Args:
            standard_data (Any): Dữ liệu cấu hình cũ vẫn được chấp nhận nhưng
                ngưỡng trong đó không tham gia phán định.
            runtime_data (Dict[str, Any]): Dữ liệu đầu ra từ phương thức ``define``.

        Returns:
            Dict[str, Any]: Dữ liệu so sánh tổng hợp gồm:
                - "runtime_score" (float): Điểm bất thường thực tế.
                - "detections" (List[Dict[str, Any]]): Danh sách đối tượng dị vật phát hiện.
                - "detections_count" (int): Số lượng dị vật phát hiện.
                - "ok" (bool): Trạng thái phán định tổng hợp.
                - "message" (str): Thông điệp mô tả chi tiết kết quả.
                - "image" (np.ndarray): Ảnh kết quả trực quan.
                - "heatmap" (np.ndarray | None): Bản đồ nhiệt bất thường.

        Raises:
            ValueError: Nếu runtime_data không phải là dict hoặc thiếu trường "score".
        """
        if isinstance(runtime_data, dict) and "boxes" in runtime_data:
            comparisons = []
            for box in runtime_data["boxes"]:
                if box.get("missing_model"):
                    comparison = {
                        "ok": False,
                        "message": f'Chưa tạo model PatchCore cho vùng "{box["name"]}"',
                        "detections_count": 0,
                    }
                else:
                    comparison = self.compare({}, box)
                    comparison["message"] = f'{box["name"]}: {comparison["message"]}'
                comparisons.append({**box, **comparison})
            if not comparisons:
                raise ValueError("Không có kết quả vùng dị vật")
            ok = all(box["ok"] for box in comparisons)
            return {
                "box_comparisons": comparisons,
                "ok": ok,
                "message": "; ".join(box["message"] for box in comparisons if not box["ok"])
                    if not ok else "Tất cả các vùng dị vật OK.",
                "image": runtime_data.get("image"),
            }
        if not isinstance(runtime_data, dict) or "score" not in runtime_data:
            raise ValueError("runtime_data phải là dict chứa ít nhất trường 'score'")

        runtime_score = float(runtime_data.get("score", 0.0))
        detections: List[Dict[str, Any]] = runtime_data.get("detections", [])
        detections_count = len(detections)

        # Lấy danh sách tên dị vật nếu có
        detected_names = []
        if detections_count > 0:
            for d in detections:
                c_name = d.get("class_name", "Không rõ")
                vn_name = FOREIGN_CLASS_NAME_VIETNAMESE_MAP.get(c_name, c_name)
                detected_names.append(vn_name)
        names_str = ", ".join(detected_names)

        ok = detections_count == 0
        message = (
            "Không phát hiện dị vật."
            if ok else f"Phát hiện {detections_count} dị vật bất thường ({names_str})."
        )

        return {
            "runtime_score": runtime_score,
            "detections": detections,
            "detections_count": detections_count,
            "anomaly_boxes": runtime_data.get("anomaly_boxes", []),
            "ok": ok,
            "message": message,
            "image": runtime_data.get("image"),
            "heatmap": runtime_data.get("heatmap"),
            "roi": runtime_data.get("roi"),
        }

    def judge(self, comparison_data: Dict[str, Any]) -> JudgmentResult:
        """Thực hiện kết luận phán định cuối cùng trả về đối tượng JudgmentResult.

        Args:
            comparison_data (Dict[str, Any]): Dữ liệu đầu ra từ phương thức ``compare``.

        Returns:
            JudgmentResult: Kết quả chuẩn hóa chứa trạng thái OK/NG, dữ liệu chuẩn,
                dữ liệu runtime, thông điệp và danh sách lỗi.

        Raises:
            ValueError: Nếu comparison_data thiếu các khóa bắt buộc.
        """
        if "box_comparisons" in comparison_data:
            boxes = comparison_data["box_comparisons"]
            return JudgmentResult(
                ok=comparison_data["ok"],
                status="OK" if comparison_data["ok"] else "NG",
                standard_data={"boxes": [
                    {"id": box["id"], "name": box["name"]}
                    for box in boxes
                ]},
                runtime_data={"boxes": boxes, "image": comparison_data.get("image")},
                comparison_data=comparison_data,
                message=comparison_data["message"],
                errors=[f'[Dị vật] NG - {box["message"]}' for box in boxes if not box["ok"]],
            )
        required_keys = {"ok", "runtime_score", "message"}
        if not required_keys.issubset(comparison_data):
            raise ValueError("comparison_data thiếu các trường bắt buộc")

        ok: bool = bool(comparison_data["ok"])
        message: str = str(comparison_data["message"])
        errors: List[str] = []
        if not ok:
            detections_count = int(comparison_data.get("detections_count", 0))
            runtime_score = float(comparison_data.get("runtime_score", 0.0))
            thuc_te = (
                f"Phát hiện {detections_count} dị vật (điểm {runtime_score:.4f})"
                if detections_count > 0
                else f"Điểm bất thường {runtime_score:.4f}"
            )
            errors.append(
                f"[Dị vật] NG - \"Dị vật\" - Quy định:\"Không có dị vật\" - Thực tế :\"{thuc_te}\""
            )

        return JudgmentResult(
            ok=ok,
            status="OK" if ok else "NG",
            standard_data={"expected": "Không có dị vật"},
            runtime_data={
                "score": comparison_data["runtime_score"],
                "detections": comparison_data.get("detections", []),
                "detections_count": comparison_data.get("detections_count", 0),
                "anomaly_boxes": comparison_data.get("anomaly_boxes", []),
                "image": comparison_data.get("image"),
                "heatmap": comparison_data.get("heatmap"),
                "roi": comparison_data.get("roi"),
            },
            comparison_data=comparison_data,
            message=message,
            errors=errors,
        )
