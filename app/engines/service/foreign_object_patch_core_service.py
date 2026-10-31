"""PatchCore service cho workflow kiểm tra dị vật (hỗ trợ nhiều vùng ROI trên 1 item)."""

import base64
from pathlib import Path
import threading
import logging
import shutil
from queue import Empty
from datetime import datetime
import cv2
import faiss
# pyrefly: ignore [missing-import]
import torch

from app.config import PATH_FOLDER_MODEL_DETECT_PATCH_CORE
from app.config import PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST
from app.config import PatchCoreAnomalyConfig
from app.config.path_config import WORKSPACE_DIR
from app.core import ErrorCode, Result
from app.engines.AI_model_process import FrameModelPatchCore, FramePatchCoreObjectDetector
from app.engines.model_AI import ModelPatchCore
from app.engines.service.patchcore_inspection_service import PatchCoreInspectionService
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordRepository,
)

logger = logging.getLogger(__name__)

class ForeignObjectPatchCoreService(PatchCoreInspectionService):
    """Tạo model PatchCore Dị vật với manifest riêng và session foreign.

    Mỗi vùng ROI (``roi_id``) trên cùng 1 item có model PatchCore độc lập, lưu tại
    ``{product_id}/{face_id}/{item_id}/roi_{roi_id}/model_foreign_crop_*``.
    Với dữ liệu cũ (1 vùng, model nằm trực tiếp trong thư mục item), vùng ``roi_id=0``
    tự động dùng lại model cũ để đảm bảo tương thích ngược.
    """
    training_inspector_name = "ForeignObjectInspector"

    def __init__(self, point_service, yolo_object_model=None):
        """Khởi tạo service kiểm tra dị vật.

        Args:
            point_service: Service truy xuất ảnh product/frame/item.
            yolo_object_model: Model YOLO object dùng để nhận diện trong vùng
                bất thường PatchCore.

        Returns:
            None.

        Raises:
            OSError: Nếu không thể tạo thư mục chứa manifest.
        """
        super().__init__(
            point_service=point_service,
            roi_name="foreign",
            purpose="train patchcore foreign object",
            record_repository=PatchCoreTrainRecordRepository(
                manifest_path=PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST,
            ),
        )
        self.yolo_object_model = yolo_object_model
        self._cache_lock = threading.Lock()
        self._patchcore_cache: dict[
            tuple[str, str, str, str], tuple[Path, int, FrameModelPatchCore]
        ] = {}
        self._training_context: tuple[str, ...] | None = None
        self._training_result: dict | None = None

    # ------------------------------------------------------------------
    # Quản lý thư mục model theo vùng ROI
    # ------------------------------------------------------------------
    def _resolve_model_root(
        self,
        product_id: int | str,
        frame_id: int | str,
        item_id: int | str,
        roi_id: int | str | None = None,
    ) -> Path:
        """Xác định thư mục chứa session PatchCore của item hoặc của một vùng ROI.

        Args:
            product_id: Mã sản phẩm.
            frame_id: Mã mặt (face).
            item_id: Mã item/point.
            roi_id: Mã vùng ROI; None trả về thư mục gốc của item.

        Returns:
            Path: Thư mục ``.../roi_{roi_id}`` để ghi model mới. Đọc model cũ
            của vùng 0 được xử lý riêng khi không có model trong roi_0.
        """
        item_root = (
            Path(PATH_FOLDER_MODEL_DETECT_PATCH_CORE)
            / str(product_id)
            / str(frame_id)
            / str(item_id)
        )
        if roi_id is None:
            return item_root
        if isinstance(roi_id, bool) or not str(roi_id).isdigit():
            raise ValueError("roi_id phải là số nguyên không âm")
        return item_root / f"roi_{int(roi_id)}"

    def _find_latest_model(self, model_root: Path) -> Path | None:
        model = super()._find_latest_model(model_root)
        if model is None and model_root.name == "roi_0":
            model = super()._find_latest_model(model_root.parent)
        return model

    def _get_record_session_root(self, product_id, frame_id, item_id, roi_id=0) -> Path | None:
        root = self._resolve_model_root(product_id, frame_id, item_id, roi_id)
        model = self._find_latest_model(root)
        if model is None:
            return None
        return next(parent for parent in model.parents
                    if parent.name.startswith("model_foreign_crop_"))

    def _find_runtime_images(self, model_root):
        images = super()._find_runtime_images(model_root)
        if not images and model_root.name == "roi_0":
            images = super()._find_runtime_images(model_root.parent)
        return images

    def save_runtime_image_for_training(
        self, product_id: int, frame_id: int, item_id: int,
        cropped_image, roi_id: int | str | None = 0,
    ) -> None:
        session = self._get_record_session_root(product_id, frame_id, item_id, roi_id)
        if session is None:
            raise FileNotFoundError(f"Không có model dị vật vùng {roi_id} để lưu ảnh train")
        folder = session / "runtime" / "good"
        folder.mkdir(parents=True, exist_ok=True)
        filename = folder / f"runtime_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        if not cv2.imwrite(str(filename), cropped_image):
            raise OSError(f"Không ghi được ảnh runtime dị vật tại {filename}")

    def invalidate_cache(
        self,
        product_id: int | str,
        frame_id: int | str,
        item_id: int | str,
        roi_id: int | str | None = None,
    ) -> None:
        """Giải phóng model PatchCore đã cache trong RAM của một vùng hoặc toàn item."""
        p_key, f_key, i_key = str(product_id), str(frame_id), str(item_id)
        with self._cache_lock:
            if roi_id is not None:
                keys = [(p_key, f_key, i_key, str(roi_id))]
            else:
                keys = [
                    key for key in self._patchcore_cache
                    if key[0] == p_key and key[1] == f_key and key[2] == i_key
                ]
            for key in keys:
                entry = self._patchcore_cache.pop(key, None)
                if entry is not None:
                    try:
                        entry[2].model.unload()
                    except (RuntimeError, OSError):
                        logger.exception("Không giải phóng được cache PatchCore %s", key)
                        raise

    def create_model(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        crop_roi: dict,
        image_count: int,
        width_canvas: int | None = None,
        roi_id: int | str = 0,
    ) -> dict:
        """Tạo model PatchCore cho đúng một vùng ROI và xóa cache RAM của vùng đó."""
        if self.worker._thread is not None and self.worker._thread.is_alive():
            raise ValueError("Đang bận tạo model, vui lòng chờ hoàn tất")
        self.invalidate_cache(product_id, frame_id, item_id, roi_id=roi_id)
        result = super().create_model(
            product_id=product_id,
            frame_id=frame_id,
            item_id=item_id,
            crop_roi=crop_roi,
            image_count=image_count,
            width_canvas=width_canvas,
            roi_id=roi_id,
        )
        if result["ok"]:
            self._training_context = tuple(map(str, (product_id, frame_id, item_id, roi_id)))
            self._training_result = None
        return result

    def training_status(self, product_id, frame_id, item_id, roi_id=0) -> dict:
        status = super().training_status(product_id, frame_id, item_id, roi_id)
        context = tuple(map(str, (product_id, frame_id, item_id, roi_id)))
        if context == self._training_context and not status["data"]["busy"]:
            if self._training_result is None and self.worker.result_queue is not None:
                try:
                    self._training_result = self.worker.result_queue.get_nowait()
                except Empty:
                    return Result.Fail("Phiên train kết thúc nhưng không có kết quả.").to_dict()
            if self._training_result is not None and not self._training_result["ok"]:
                logger.error("Train PatchCore %s thất bại: %s", context, self._training_result["error"])
                return Result.Fail(f'Tạo model thất bại: {self._training_result["error"]}').to_dict()
        return status

    def delete_model(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        roi_id: int | str = 0,
    ) -> dict:
        """Xóa model PatchCore của một vùng ROI, giữ nguyên các vùng khác của item."""
        if self.worker._thread is not None and self.worker._thread.is_alive():
            raise ValueError("Đang bận tạo model, vui lòng chờ hoàn tất")
        root = self._resolve_model_root(product_id, frame_id, item_id, roi_id)
        roots = [root, root.parent] if str(roi_id) == "0" else [root]
        self.invalidate_cache(product_id, frame_id, item_id, roi_id=roi_id)
        deleted_sessions = 0
        deleted_records = 0
        for folder in roots:
            for session in folder.glob("model_foreign_crop_*"):
                if session.is_dir():
                    shutil.rmtree(session)
                    deleted_sessions += 1
                    deleted_records += self.record_repository.delete_records_under_dir(session)
        for record in self.record_repository.load_manifest():
            raw_path = record.get("model_root")
            if not raw_path:
                continue
            session = Path(raw_path)
            if not session.is_absolute():
                session = WORKSPACE_DIR / session
            if session.resolve().parent in {folder.resolve() for folder in roots} and session.name.startswith("model_foreign_crop_"):
                deleted_records += self.record_repository.delete_records_under_dir(session)
        if root.is_dir() and not any(root.iterdir()):
            root.rmdir()
        if not deleted_sessions and not deleted_records:
            return Result.Fail(ErrorCode.PATCHCORE_MODEL_NOT_FOUND).to_dict()
        if self._training_context == tuple(map(str, (product_id, frame_id, item_id, roi_id))):
            self._training_context = None
            self._training_result = None
        return Result.Ok({"deleted_model_root": str(root), "deleted_records": deleted_records}).to_dict()

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def run_model(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        crop_roi: dict,
        width_canvas: int | None = None,
        roi_id: int | str = 0,
    ) -> dict:
        """Khoanh vùng PatchCore; bước này chưa phán định dị vật OK/NG."""
        if not isinstance(crop_roi, dict):
            raise ValueError("ROI dị vật phải là một object")
        crop = {key: value for key, value in crop_roi.items() if key != "threshold"}
        result = super().run_model(product_id, frame_id, item_id, crop, width_canvas, roi_id)
        if result["ok"]:
            result["data"].pop("status", None)
            result["data"]["stage"] = "anomaly_localization"
        return result

    def run_model_with_object_detection(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        crop_roi: dict,
        width_canvas: int | None = None,
        roi_id: int | str = 0,
    ) -> dict:
        """Chạy PatchCore và nhận diện YOLO trên từng vùng bất thường của một vùng ROI.

        Args:
            product_id: Mã sản phẩm.
            frame_id: Mã frame.
            item_id: Mã item/point.
            crop_roi: ROI cần kiểm tra theo ảnh hoặc canvas.
            width_canvas: Chiều rộng canvas nếu ROI dùng tọa độ canvas.
            roi_id: Mã vùng ROI (mỗi vùng có model PatchCore riêng).

        Returns:
            dict: Kết quả PatchCore gồm ảnh overlay, score, box bất thường,
                ảnh crop từng vùng bất thường và detection YOLO.

        Raises:
            ValueError: Nếu model đang bận, ROI không hợp lệ hoặc chưa có YOLO.
            OSError: Nếu không đọc được ảnh hoặc model PatchCore.
        """
        if self.yolo_object_model is None:
            raise ValueError("Chưa cấu hình model YOLO object cho foreign object")
        if self.worker._thread is not None and self.worker._thread.is_alive():
            raise ValueError("Đang bận tạo model, vui lòng chờ hoàn tất")
        if not self._inference_lock.acquire(blocking=False):
            raise ValueError("Đang bận chạy inference")

        model = None
        try:
            image_result = self.point_service.get_path_img_point(product_id, frame_id, item_id)
            if not image_result.ok:
                return Result.Fail(image_result.error).to_dict()
            image_bgr = cv2.imread(str(image_result.data))
            if image_bgr is None:
                return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()

            converted_roi = self._convert_crop_roi(crop_roi, image_bgr.shape, width_canvas)
            cropped_bgr = image_bgr[
                converted_roi["yStart"]:converted_roi["yEnd"],
                converted_roi["xStart"]:converted_roi["xEnd"],
            ]
            self._save_retrain_input(
                cropped_bgr,
            )
            model_root = self._resolve_model_root(product_id, frame_id, item_id, roi_id)
            model_file = self._find_latest_model(model_root)
            if model_file is None:
                return Result.Fail(ErrorCode.PATCHCORE_MODEL_NOT_FOUND).to_dict()

            image_rgb = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
            index_probe = faiss.read_index(str(model_file))
            config = PatchCoreAnomalyConfig(
                index_path=str(model_file),
                nprobe=max(1, int(index_probe.nlist)),
                img_size=256,
                device="cuda" if torch.cuda.is_available() else "cpu",
            )
            model = ModelPatchCore(config)
            model.load_model()
            score, overlay_bgr = model.predict(image_rgb)
            boxes = [
                (int(x), int(y), int(width), int(height))
                for x, y, width, height in model.get_bounding_boxes(image_rgb)
            ]

            detector = FramePatchCoreObjectDetector(
                FrameModelPatchCore(model),
                self.yolo_object_model,
            )
            detections = detector.detect_anomaly_objects(
                cropped_bgr,
                0,
                0,
                cropped_bgr.shape[1],
                cropped_bgr.shape[0],
                anomaly_boxes=boxes,
            )
            anomaly_regions = self._encode_anomaly_regions(cropped_bgr, boxes)

            ok, encoded = cv2.imencode(".png", overlay_bgr)
            if not ok:
                raise ValueError("Không thể mã hóa ảnh inference")
            return Result.Ok({
                "image": "data:image/png;base64," + base64.b64encode(bytes(encoded)).decode("ascii"),
                "score": float(score),
                "boxes": [self._box_to_dict(box) for box in boxes],
                "anomaly_regions": anomaly_regions,
                "detections": detections,
                "status": "NG" if detections else "OK",
                "model_file": str(model_file),
                "roi_id": roi_id,
            }).to_dict()
        finally:
            if model is not None:
                model.unload()
            self._inference_lock.release()

    @staticmethod
    def _box_to_dict(box: tuple[int, int, int, int]) -> dict[str, int]:
        """Chuyển box ``(x, y, width, height)`` thành object response."""
        x, y, width, height = box
        return {"x": x, "y": y, "width": width, "height": height}

    @staticmethod
    def _encode_anomaly_regions(
        image_bgr,
        boxes: list[tuple[int, int, int, int]],
    ) -> list[dict]:
        """Crop và mã hóa PNG từng vùng PatchCore bất thường."""
        regions = []
        image_height, image_width = image_bgr.shape[:2]
        for index, (x, y, width, height) in enumerate(boxes, start=1):
            left = max(0, x)
            top = max(0, y)
            right = min(image_width, x + width)
            bottom = min(image_height, y + height)
            crop = image_bgr[top:bottom, left:right]
            if crop.size == 0:
                continue
            ok, encoded = cv2.imencode(".png", crop)
            if not ok:
                continue
            regions.append({
                "index": index,
                "box": {
                    "x": left,
                    "y": top,
                    "width": right - left,
                    "height": bottom - top,
                },
                "image": "data:image/png;base64," + base64.b64encode(bytes(encoded)).decode("ascii"),
            })
        return regions

    def get_patchcore_frame(
        self,
        product_id: int | str,
        frame_id: int | str,
        item_id: int | str,
        roi_id: int | str = 0,
    ) -> FrameModelPatchCore:
        """Lấy hoặc nạp cached FrameModelPatchCore cho một vùng ROI của point.

        Args:
            product_id: Mã sản phẩm.
            frame_id: Mã frame.
            item_id: Mã item/point.
            roi_id: Mã vùng ROI trên item.

        Returns:
            FrameModelPatchCore: Instance xử lý mô hình PatchCore.

        Raises:
            FileNotFoundError: Nếu không tìm thấy file index mô hình.
        """
        key = (str(product_id), str(frame_id), str(item_id), str(roi_id))
        model_root = self._resolve_model_root(product_id, frame_id, item_id, roi_id)
        model_file = self._find_latest_model(model_root)
        if model_file is None:
            raise FileNotFoundError(
                f"Không tìm thấy mô hình PatchCore tại {model_root} "
                f"cho sản phẩm {product_id}, frame {frame_id}, item {item_id}, roi {roi_id}"
            )
        mtime_ns = model_file.stat().st_mtime_ns

        with self._cache_lock:
            if key in self._patchcore_cache:
                cached_path, cached_mtime, cached_frame = self._patchcore_cache[key]
                if cached_path == model_file and cached_mtime == mtime_ns:
                    return cached_frame

        # Nạp mô hình mới và lưu cache
        index_probe = faiss.read_index(str(model_file))
        try:
            nlist = int(faiss.extract_index_ivf(index_probe).nlist)
        except Exception:
            nlist = getattr(index_probe, "nlist", 1)
        config = PatchCoreAnomalyConfig(
            index_path=str(model_file),
            nprobe=max(1, nlist),
            img_size=256,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        model = ModelPatchCore(config)
        model.load_model()
        model.warmup()
        patchcore_frame = FrameModelPatchCore(model)
        self.invalidate_cache(product_id, frame_id, item_id, roi_id)
        with self._cache_lock:
            self._patchcore_cache[key] = (model_file, mtime_ns, patchcore_frame)
        return patchcore_frame

    def get_detector_engine(
        self,
        product_id: int | str,
        frame_id: int | str,
        item_id: int | str,
        roi_id: int | str = 0,
    ) -> FramePatchCoreObjectDetector:
        """Lấy hoặc nạp FramePatchCoreObjectDetector cho một vùng ROI của point.

        Args:
            product_id: Mã sản phẩm.
            frame_id: Mã frame.
            item_id: Mã item/point.
            roi_id: Mã vùng ROI trên item.

        Returns:
            FramePatchCoreObjectDetector: Detector kết hợp PatchCore và YOLO.

        Raises:
            ValueError: Nếu chưa cấu hình mô hình YOLO.
            FileNotFoundError: Nếu không tìm thấy mô hình PatchCore.
        """
        if self.yolo_object_model is None:
            raise ValueError("Chưa cấu hình model YOLO object cho foreign object")
        patchcore_frame = self.get_patchcore_frame(product_id, frame_id, item_id, roi_id=roi_id)
        return FramePatchCoreObjectDetector(
            patch_core_frame=patchcore_frame,
            yolo_object_model=self.yolo_object_model,
        )
