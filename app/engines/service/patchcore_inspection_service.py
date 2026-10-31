"""Logic dùng chung để train và chạy inference PatchCore theo từng loại kiểm tra."""
from pathlib import Path
import shutil
import base64
import threading
import cv2
# pyrefly: ignore [missing-import]
import torch
import faiss
import numpy as np
from PIL import Image

from app.config import (
    PATH_FOLDER_MODEL_DETECT_PATCH_CORE,
    PATCHCORE_RUNTIME_DIR_NAME,
    PATCHCORE_INITIAL_DIR_NAME,
    PATCHCORE_INDEX_FILE_NAME,
    PatchCoreTrainConfig,
)
from app.config.path_config import WORKSPACE_DIR
from app.core import ErrorCode, Result
from app.engines.train.patchcore_train_model import TrainWorkerPatchCore
from app.config import PatchCoreAnomalyConfig
from app.engines.model_AI import ModelPatchCore
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordRepository,
)
from app.utils.opencv_tool import Tool_OpenCv2


class PatchCoreInspectionService:
    """Chuẩn bị ảnh Point và điều phối PatchCore cho một loại kiểm tra cấu hình sẵn."""
    training_inspector_name = "PatchCoreInspector"

    def __init__(
        self,
        point_service,
        roi_name: str,
        purpose: str,
        record_repository: PatchCoreTrainRecordRepository,
        worker: TrainWorkerPatchCore | None = None,
    ):
        """Khởi tạo facade với PointService và worker train.

        Args:
            point_service: Service truy xuất ảnh theo product/frame/item.
            roi_name: Tên ROI, dùng làm tiền tố session PatchCore.
            purpose: Mô tả phiên train được lưu trong manifest.
            record_repository: Repository manifest bắt buộc của loại kiểm tra.
            worker: Worker PatchCore dùng cho các phiên train.
        """
        self.point_service = point_service
        self._inference_lock = threading.Lock()
        self.roi_name = roi_name
        self.purpose = purpose
        self.record_repository = record_repository
        self.worker = worker or TrainWorkerPatchCore(self.record_repository)

    @staticmethod
    def _resolve_model_root(
        product_id: int | str,
        frame_id: int | str,
        item_id: int | str,
        roi_id: int | str | None = None,
    ) -> Path:
        """Xác định thư mục gốc chứa các session PatchCore của item hoặc của từng khung ROI."""
        base = (
            Path(PATH_FOLDER_MODEL_DETECT_PATCH_CORE)
            / str(product_id)
            / str(frame_id)
            / str(item_id)
        )
        if roi_id is not None:
            return base / f"roi_{roi_id}"
        return base

    def get_runtime_images(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        roi_id: int | str | None = None,
    ) -> dict:
        """Lấy toàn bộ ảnh runtime/good của session mới nhất."""
        session_root = self._get_record_session_root(product_id, frame_id, item_id, roi_id=roi_id)
        if session_root is None:
            return Result.Ok({"status": "no_model", "images": []}).to_dict()
        image_root = session_root / "runtime" / "good"
        images = []
        for image_path in sorted(image_root.glob("*.png")):
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            images.append({
                "name": image_path.name,
                "image": f"data:image/png;base64,{encoded}",
            })
        return Result.Ok({
            "status": "runtime_images" if images else "no_runtime_images",
            "images": images,
            "model_root": str(session_root),
        }).to_dict()

    def delete_runtime_image(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        image_name: str,
        roi_id: int | str | None = None,
    ) -> dict:
        """Xóa một ảnh runtime/good trong session được ghi nhận."""
        if Path(image_name).name != image_name or not image_name.lower().endswith(".png"):
            return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()
        session_root = self._get_record_session_root(product_id, frame_id, item_id, roi_id=roi_id)
        if session_root is None:
            return Result.Fail(ErrorCode.PATCHCORE_MODEL_NOT_FOUND).to_dict()
        image_path = session_root / "runtime" / "good" / image_name
        if not image_path.is_file():
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()
        image_path.unlink()
        return Result.Ok({"deleted": image_name}).to_dict()

    def delete_model(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        roi_id: int | str | None = None,
    ) -> dict:
        """Xóa session model và đúng các record manifest của item (hoặc của khung roi_id)."""
        expected_root = self._resolve_model_root(product_id, frame_id, item_id, roi_id).resolve()
        session_root = self._get_record_session_root(product_id, frame_id, item_id, roi_id=roi_id)

        if session_root is None:
            # Dự phòng trường hợp thư mục model tồn tại trên đĩa nhưng thiếu record manifest
            latest_model = self._find_latest_model(expected_root)
            if latest_model is None:
                return Result.Fail(ErrorCode.PATCHCORE_MODEL_NOT_FOUND).to_dict()
            for parent in [latest_model.parent, latest_model.parent.parent]:
                if parent.parent.resolve() == expected_root:
                    session_root = parent.resolve()
                    break
            if session_root is None:
                return Result.Fail(ErrorCode.PATCHCORE_MODEL_NOT_FOUND).to_dict()

        if session_root.parent != expected_root:
            return Result.Fail(ErrorCode.INVALID_INPUT).to_dict()

        if roi_id is not None:
            # Với chế độ đa vùng (mỗi roi_id 1 thư mục riêng), dọn sạch toàn bộ thư mục roi_{roi_id}
            shutil.rmtree(expected_root, ignore_errors=True)
            deleted_records = self.record_repository.delete_records_under_dir(expected_root)
            return Result.Ok({
                "deleted_model_root": str(expected_root),
                "deleted_records": deleted_records,
            }).to_dict()

        shutil.rmtree(session_root)
        deleted_records = self.record_repository.delete_records_by_model_root(session_root)
        return Result.Ok({
            "deleted_model_root": str(session_root),
            "deleted_records": deleted_records,
        }).to_dict()

    def save_runtime_image_for_training(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        cropped_image: np.ndarray,
        roi_id: int | str | None = None,
    ) -> None:
        """Lưu ảnh crop vào thư mục runtime/good của session hiện tại để phục vụ train lại mô hình."""
        session_root = self._get_record_session_root(product_id, frame_id, item_id, roi_id=roi_id)
        if session_root is None:
            return  # Không có session model nào để lưu (có thể chưa train The First)

        good_dir = session_root / "runtime" / "good"
        good_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime
        now = datetime.now()
        filename = good_dir / f"runtime_{now.strftime('%Y%m%d_%H%M%S_%f')}.png"
        cv2.imwrite(str(filename), cropped_image)
        print(f"[PATCHCORE] Đã lưu ảnh runtime train tại: {filename}")

    def _get_record_session_root(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        roi_id: int | str | None = None,
    ) -> Path | None:
        """Resolve đúng session từ record mới nhất của Point (hoặc khung roi_id)."""
        expected_root = self._resolve_model_root(product_id, frame_id, item_id, roi_id).resolve()

        manifest = self.record_repository.load_manifest()
        for record in manifest:
            if not record or not record.get("model_root"):
                continue
            model_root = Path(record["model_root"])
            if not model_root.is_absolute():
                model_root = WORKSPACE_DIR / model_root
            model_root = model_root.resolve()
            if model_root.parent == expected_root and model_root.exists():
                return model_root
        return None

    def create_model(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        crop_roi: dict,
        image_count: int,
        width_canvas: int | None = None,
        roi_id: int | str | None = None,
    ) -> dict:
        """Tạo yêu cầu train PatchCore từ ảnh Point cho item hoặc cho riêng một khung roi_id."""
        if image_count < 1:
            raise ValueError("image_count phải lớn hơn 0")
        if width_canvas is not None and width_canvas <= 0:
            raise ValueError("width_canvas phải lớn hơn 0")

        image_result = self.point_service.get_path_img_point(product_id, frame_id, item_id)
        if not image_result.ok:
            return Result.Fail(image_result.error).to_dict()

        image_path = Path(image_result.data)
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND).to_dict()
        crop_roi = self._convert_crop_roi(crop_roi, image_bgr.shape, width_canvas)
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image_rgb)

        model_root = self._resolve_model_root(product_id, frame_id, item_id, roi_id)
        self.point_service.attach_patchcore_paths(
            int(product_id),
            int(frame_id),
            int(item_id),
        )
        config = PatchCoreTrainConfig(
            crop_roi=crop_roi,
            coreset_ratio=1.0,
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        runtime_images = self._find_runtime_images(model_root)
        if runtime_images:
            train_images = runtime_images
            model_variant = "runtime"
            print(
                f"[PATCHCORE] Nguồn train: runtime, số ảnh: {len(train_images)}, "
                f"folder: {model_root}"
            )
        else:
            train_images = [image.copy() for _ in range(image_count)]
            model_variant = "the_first"
            print(
                f"[PATCHCORE] Nguồn train: ảnh Point mẫu lặp {image_count} lần, "
                f"runtime chưa có ảnh: {model_root}"
            )
        try:
            self.worker.start(
                model_root=model_root,
                roi_name=self.roi_name,
                purpose=self.purpose,
                image_count=len(train_images),
                config=config,
                model_variant=model_variant,
            )
            for train_image in train_images:
                self.worker.submit_image(train_image.copy())
        except Exception:
            self.worker.stop()
            raise

        payload = {
            "status": "training_started",
            "product_id": product_id,
            "frame_id": frame_id,
            "item_id": item_id,
            "image_count": image_count,
            "model_root": str(model_root),
        }
        if roi_id is not None:
            payload["roi_id"] = roi_id
        return Result.Ok(payload).to_dict()

    def run_model(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        crop_roi: dict,
        width_canvas: int | None = None,
        roi_id: int | str | None = None,
    ) -> dict:
        """Chạy inference model PatchCore mới nhất của một Point (hoặc khung roi_id)."""
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
                nprobe=max(1, int(faiss.extract_index_ivf(index_probe).nlist)),
                img_size=256,
                device="cuda" if torch.cuda.is_available() else "cpu",
            )
            model = ModelPatchCore(config)
            model.load_model()
            threshold_val = float(crop_roi.get("threshold", 0.1)) if isinstance(crop_roi, dict) and "threshold" in crop_roi else 0.1
            score, overlay_bgr = model.predict(image_rgb, threshold=threshold_val)
            boxes = [
                {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
                for x, y, w, h in model.get_bounding_boxes(image_rgb)
            ]
            model.unload()

            ok, encoded = cv2.imencode(".png", overlay_bgr)
            if not ok:
                raise ValueError("Không thể mã hóa ảnh inference")
            return Result.Ok({
                "image": "data:image/png;base64," + base64.b64encode(bytes(encoded)).decode("ascii"),
                "score": float(score),
                "boxes": boxes,
                "status": "NG" if boxes else "OK",
                "model_file": str(model_file),
            }).to_dict()
        finally:
            self._inference_lock.release()

    def _save_retrain_input(
        self,
        cropped_image: np.ndarray,
    ) -> None:
        """Lưu crop PatchCore trước inference mà không làm gián đoạn judgment."""
        try:
            path = Tool_OpenCv2.save_training_input(
                cropped_image,
                self.training_inspector_name,
                "roi",
            )
            print(f"[PATCHCORE][{self.training_inspector_name}] TRAIN_INPUT saved={path}")
        except Exception as error:
            print(
                f"[PATCHCORE][{self.training_inspector_name}] "
                f"TRAIN_INPUT_SAVE_WARNING: {error!r}"
            )

    def training_status(
        self,
        product_id: int,
        frame_id: int,
        item_id: int,
        roi_id: int | str | None = None,
    ) -> dict:
        """Trả trạng thái worker và model PatchCore của một Point (hoặc khung roi_id)."""
        model_root = self._resolve_model_root(product_id, frame_id, item_id, roi_id)
        worker_thread = getattr(self.worker, "_thread", None)
        busy = worker_thread is not None and worker_thread.is_alive()
        model_file = self._find_latest_model(model_root)
        return Result.Ok({
            "busy": busy,
            "completed": model_file is not None and not busy,
            "model_file": str(model_file) if model_file else "",
        }).to_dict()

    def _find_runtime_images(self, model_root: Path) -> list[Image.Image]:
        """Đọc toàn bộ ảnh crop runtime của session mới nhất nếu có."""
        if not model_root.exists():
            return []
        candidates = sorted(model_root.glob(f"model_{self.roi_name}_crop_*/runtime/good/*.png"))
        images = []
        for path in candidates:
            try:
                with Image.open(path) as image:
                    images.append(image.convert("RGB"))
            except OSError:
                print(f"[PATCHCORE] Bỏ qua ảnh runtime lỗi: {path}")
        return images

    def _find_latest_model(self, model_root: Path) -> Path | None:
        """Tìm model trong session mới nhất, ưu tiên runtime rồi the_first."""
        if not model_root.exists():
            return None
        sessions = [
            path for path in model_root.glob(f"model_{self.roi_name}_crop_*")
            if path.is_dir()
        ]
        sessions.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        for session in sessions:
            for relative_model in (
                Path(PATCHCORE_RUNTIME_DIR_NAME) / PATCHCORE_INDEX_FILE_NAME,
                Path(PATCHCORE_INITIAL_DIR_NAME) / PATCHCORE_INDEX_FILE_NAME,
                Path(PATCHCORE_INDEX_FILE_NAME),
            ):
                candidate = session / relative_model
                if candidate.is_file():
                    return candidate
        return None

    @staticmethod
    def _validate_crop_roi(crop_roi: dict) -> None:
        """Kiểm tra crop ROI có đủ bốn tọa độ và kích thước hợp lệ."""
        try:
            left = int(crop_roi["xStart"])
            top = int(crop_roi["yStart"])
            right = int(crop_roi["xEnd"])
            bottom = int(crop_roi["yEnd"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("crop_roi cần xStart, yStart, xEnd, yEnd") from error
        if left >= right or top >= bottom or min(left, top) < 0:
            raise ValueError("crop_roi không hợp lệ")

    @classmethod
    def _convert_crop_roi(
        cls,
        crop_roi: dict,
        image_shape: tuple[int, ...],
        width_canvas: int | None,
    ) -> dict:
        """Quy đổi ROI canvas sang pixel ảnh nếu width_canvas được cung cấp."""
        cls._validate_crop_roi(crop_roi)
        if not width_canvas:
            converted = {key: int(crop_roi[key]) for key in ("xStart", "yStart", "xEnd", "yEnd")}
        else:
            image_height, image_width = image_shape[:2]
            scale = image_width / int(width_canvas)
            converted = {
                "xStart": int(crop_roi["xStart"] * scale),
                "yStart": int(crop_roi["yStart"] * scale),
                "xEnd": int(crop_roi["xEnd"] * scale),
                "yEnd": int(crop_roi["yEnd"] * scale),
            }
        image_height, image_width = image_shape[:2]
        converted["xStart"] = max(0, min(converted["xStart"], image_width - 1))
        converted["yStart"] = max(0, min(converted["yStart"], image_height - 1))
        converted["xEnd"] = max(1, min(converted["xEnd"], image_width))
        converted["yEnd"] = max(1, min(converted["yEnd"], image_height))
        cls._validate_crop_roi(converted)
        return converted
