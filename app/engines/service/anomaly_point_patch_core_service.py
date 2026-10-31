import base64
from pathlib import Path
import threading
import cv2
import faiss
# pyrefly: ignore [missing-import]
import torch
from app.config import (
    PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST,
    PatchCoreAnomalyConfig,
)
from app.core import ErrorCode, Result
from app.engines.AI_model_process.frame_patch_core_process import FrameModelPatchCore
from app.engines.model_AI import ModelPatchCore
from app.engines.service.patchcore_inspection_service import PatchCoreInspectionService
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordRepository,
)


class AnomalyPointPatchCoreService(PatchCoreInspectionService):
    """Dịch vụ PatchCore đa vùng (Multi-ROI) cho công cụ Kiểm tra điểm bất thường."""
    training_inspector_name = "AnomalyPointInspector"

    def __init__(self, point_service):
        """Khởi tạo service Kiểm tra điểm bất thường với manifest riêng."""
        super().__init__(
            point_service=point_service,
            roi_name="anomaly_point",
            purpose="train patchcore anomaly point",
            record_repository=PatchCoreTrainRecordRepository(
                manifest_path=PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST,
            ),
        )
        self._cache_lock = threading.Lock()
        self._patchcore_cache: dict[tuple[str, str, str, str], tuple[Path, int, FrameModelPatchCore]] = {}

    def invalidate_cache(
        self,
        product_id: int | str,
        frame_id: int | str,
        item_id: int | str,
        roi_id: int | str | None = None,
    ) -> None:
        """Xóa cache model trong RAM cho 1 khung roi_id cụ thể hoặc toàn bộ item."""
        p_key, f_key, i_key = str(product_id), str(frame_id), str(item_id)
        with self._cache_lock:
            if roi_id is not None:
                entry = self._patchcore_cache.pop((p_key, f_key, i_key, str(roi_id)), None)
                if entry is not None:
                    try:
                        entry[2].model.unload()
                    except Exception:
                        pass
            else:
                keys_to_remove = [
                    k for k in self._patchcore_cache
                    if k[0] == p_key and k[1] == f_key and k[2] == i_key
                ]
                for k in keys_to_remove:
                    entry = self._patchcore_cache.pop(k, None)
                    if entry is not None:
                        try:
                            entry[2].model.unload()
                        except Exception:
                            pass

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
        """Tạo model PatchCore cho đúng khung roi_id trên item."""
        self.invalidate_cache(product_id, frame_id, item_id, roi_id=roi_id)
        return super().create_model(
            product_id=product_id,
            frame_id=frame_id,
            item_id=item_id,
            crop_roi=crop_roi,
            image_count=image_count,
            width_canvas=width_canvas,
            roi_id=roi_id,
        )

    def delete_model(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        roi_id: int | str = 0,
    ) -> dict:
        """Xóa model PatchCore và dọn cache RAM của riêng khung roi_id."""
        self.invalidate_cache(product_id, frame_id, item_id, roi_id=roi_id)
        return super().delete_model(
            product_id=product_id,
            frame_id=frame_id,
            item_id=item_id,
            roi_id=roi_id,
        )

    def get_patchcore_frame(
        self,
        product_id: int | str,
        frame_id: int | str,
        item_id: int | str,
        roi_id: int | str = 0,
    ) -> FrameModelPatchCore:
        """Lấy hoặc nạp cached FrameModelPatchCore cho một khung roi_id trên item.

        Raises:
            FileNotFoundError: Nếu chưa tạo file index mô hình cho khung roi_id này.
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
        with self._cache_lock:
            self._patchcore_cache[key] = (model_file, mtime_ns, patchcore_frame)
        return patchcore_frame

    def run_model(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        crop_roi: dict,
        width_canvas: int | None = None,
        roi_id: int | str = 0,
    ) -> dict:
        """Chạy inference model PatchCore của một khung roi_id trên item và vẽ viền vàng cam vùng lỗi."""
        if self.worker._thread is not None and self.worker._thread.is_alive():
            raise ValueError("Đang bận tạo model, vui lòng chờ hoàn tất")
        if not self._inference_lock.acquire(blocking=False):
            raise ValueError("Đang bận chạy inference")
        try:
            image_result = self.point_service.get_path_img_point(product_id, frame_id, item_id)
            if not image_result.ok:
                return Result.Fail(image_result.error).to_dict()
            image_bgr = cv2.imread(str(image_result.data))
            if image_bgr is None:
                return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()

            converted_roi = self._convert_crop_roi(crop_roi, image_bgr.shape, width_canvas)
            x1 = int(converted_roi["xStart"])
            y1 = int(converted_roi["yStart"])
            x2 = int(converted_roi["xEnd"])
            y2 = int(converted_roi["yEnd"])

            cropped_bgr = image_bgr[y1:y2, x1:x2]
            self._save_retrain_input(cropped_bgr)

            try:
                patchcore_frame = self.get_patchcore_frame(product_id, frame_id, item_id, roi_id=roi_id)
            except FileNotFoundError:
                return Result.Fail(ErrorCode.PATCHCORE_MODEL_NOT_FOUND).to_dict()

            threshold_val = (
                float(crop_roi.get("threshold", 0.2))
                if isinstance(crop_roi, dict) and "threshold" in crop_roi
                else 0.2
            )

            score, overlay_bgr, anomaly_boxes = patchcore_frame.predict_with_anomaly_boxes(
                image_bgr, x1, y1, x2, y2, threshold=threshold_val
            )

            for idx, abox in enumerate(anomaly_boxes):
                bx = abox[0] - x1
                by = abox[1] - y1
                bw = abox[2]
                bh = abox[3]
                cv2.rectangle(overlay_bgr, (bx, by), (bx + bw, by + bh), (0, 215, 255), 2)
                label_anom = f"Vung loi #{idx + 1}"
                (tw, th), _ = cv2.getTextSize(label_anom, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                bg_y1 = max(0, by - th - 6)
                cv2.rectangle(overlay_bgr, (bx, bg_y1), (bx + tw + 6, by), (0, 215, 255), -1)
                cv2.putText(
                    overlay_bgr,
                    label_anom,
                    (bx + 3, by - 3),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    1,
                    cv2.LINE_AA,
                )

            ok, encoded = cv2.imencode(".png", overlay_bgr)
            if not ok:
                raise ValueError("Không thể mã hóa ảnh inference")

            boxes_crop = [
                {"x": int(b[0] - x1), "y": int(b[1] - y1), "width": int(b[2]), "height": int(b[3])}
                for b in anomaly_boxes
            ]
            score_float = float(score)
            is_ng = score_float > threshold_val
            return Result.Ok({
                "image": "data:image/png;base64," + base64.b64encode(bytes(encoded)).decode("ascii"),
                "score": score_float,
                "threshold": threshold_val,
                "boxes": boxes_crop,
                "status": "NG" if is_ng else "OK",
                "roi_id": int(roi_id) if str(roi_id).isdigit() else roi_id,
            }).to_dict()
        finally:
            self._inference_lock.release()
