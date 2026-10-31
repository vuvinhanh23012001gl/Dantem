import argparse
from io import BytesIO
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
import faiss
import cv2
import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as T
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from torchvision.models import ResNet18_Weights, resnet18
from tqdm import tqdm
from PIL import Image
from app.config import PatchCoreTrainConfig
from app.config import PatchCoreAnomalyConfig
from app.config.path_config import PATH_FILE_RESNET18_BACKBONE
from app.engines.model_AI import ModelPatchCore
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordRepository,
)
from app.engines.train.patchcore_train_model.patchcore_datasets import (
    CroppedImageFolder,
    PatchCoreImageDataset,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class TrainlerPatchCore:
    """Lớp quản lý toàn bộ quy trình huấn luyện PatchCore trong dự án.

    Kết cấu hướng đối tượng này tập trung các thành phần liên quan vào một đối tượng
    duy nhất: cấu hình, backbone, tiền xử lý ảnh, trích xuất đặc trưng và huấn luyện
    FAISS memory bank cho từng ROI.
    """

    def __init__(
        self,
        config: PatchCoreTrainConfig | None = None,
        record_manager: PatchCoreTrainRecordRepository | None = None,
    ):
        """Khởi tạo trainer PatchCore.

        Args:
            config (PatchCoreTrainConfig | None, optional): Đối tượng cấu hình huấn luyện.
                Mặc định sẽ tạo cấu hình chuẩn theo project.
            record_manager: Repository manifest dùng để lưu phiên train.
        """
        self.config = config or PatchCoreTrainConfig()
        self.data_root = None
        self.model_root = None
        self._images_are_pre_cropped = False
        self._flat_session_layout = False
        self.device = self.config.device
        self.transform = self._build_transform(self.config.img_size)
        self.backbone = None
        self.layer2 = None
        self.layer3 = None
        self.layer4 = None
        self.record_manager = record_manager or PatchCoreTrainRecordRepository()

    def _build_transform(self, img_size: int):
        """Tạo bộ tiền xử lý chuẩn cho ảnh đầu vào của ResNet18.

        Args:
            img_size (int): Kích thước ảnh sau khi resize.

        Returns:
            torchvision.transforms.Compose: Bộ biến đổi ảnh chuẩn hóa.
        """
        return T.Compose(
            [
                T.Resize((img_size, img_size)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    def _build_backbone(self):
        """Nạp Backbone ResNet18 và lấy các tầng trung gian cần trích xuất đặc trưng.

        Returns:
            tuple: Gồm model, layer2, layer3, layer4.
        """
        model = resnet18(weights=None)
        backbone_path = Path(PATH_FILE_RESNET18_BACKBONE)
        if backbone_path.exists():
            state_dict = torch.load(str(backbone_path), map_location=self.device)
            model.load_state_dict(state_dict)
        else:
            hub_cache = Path(torch.hub.get_dir()) / "checkpoints" / "resnet18-f37072fd.pth"
            if hub_cache.exists():
                state_dict = torch.load(str(hub_cache), map_location=self.device)
                model.load_state_dict(state_dict)
            else:
                model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        model.to(self.device)
        model.eval()

        self.backbone = model
        self.layer2 = torch.nn.Sequential(*list(model.children())[:5])
        self.layer3 = torch.nn.Sequential(*list(model.children())[5:6])
        self.layer4 = torch.nn.Sequential(*list(model.children())[6:7])
        return model, self.layer2, self.layer3, self.layer4

    @staticmethod
    @torch.no_grad()
    def _extract_features(batch, device: str, layer2, layer3, layer4):
        """Trích xuất đặc trưng patch-level cho batch ảnh.

        Args:
            batch (torch.Tensor): Batch ảnh đầu vào dạng (N, C, H, W).
            device (str): Thiết bị đang chạy, ví dụ cpu/cuda.
            layer2, layer3, layer4: Các tầng trung gian của ResNet.

        Returns:
            np.ndarray: Mảng đặc trưng dạng (N, P, C).
        """
        batch = batch.to(device)

        f2 = layer2(batch)
        f3 = layer3(f2)
        f4 = layer4(f3)

        f2 = F.adaptive_avg_pool2d(f2, (14, 14))
        f3 = F.adaptive_avg_pool2d(f3, (14, 14))
        f4 = F.adaptive_avg_pool2d(f4, (14, 14))

        f2 = f2.flatten(2).transpose(1, 2)
        f3 = f3.flatten(2).transpose(1, 2)
        f4 = f4.flatten(2).transpose(1, 2)

        feat = torch.cat([f2, f3, f4], dim=-1)
        feat = F.normalize(feat, dim=-1)
        return feat.cpu().numpy()

    def _get_roi_folders(self):
        """Lấy danh sách thư mục ROI từ `data_root` sắp xếp theo tên.

        Returns:
            list[Path]: Danh sách các ROI đang có dữ liệu.
        """
        data_root = self.data_root
        if data_root is None:
            raise RuntimeError("Trainer chưa được khởi tạo dữ liệu cho phiên train")
        if not data_root.exists():
            logger.warning("Data root not found: %s", data_root)
            return []

        direct_images = [
            path for path in data_root.iterdir()
            if path.is_file() and path.suffix.lower() in PatchCoreImageDataset.IMAGE_SUFFIXES
        ]
        if direct_images:
            return [data_root]

        rois = [path for path in data_root.iterdir() if path.is_dir()]
        rois.sort(key=lambda item: item.name)
        return rois

    def _get_crop_box(self):
        """Chuẩn hóa tọa độ crop từ config thành ``(left, top, right, bottom)``.

        Returns:
            tuple[int, int, int, int] | None: Vùng crop theo pixel, hoặc None để
            train toàn bộ ảnh.
        Errors:
            ValueError nếu thiếu tọa độ hoặc vùng crop có kích thước không dương.
        """
        crop_roi = self.config.crop_roi
        if not crop_roi:
            return None

        left = crop_roi.get("xStart", crop_roi.get("x", crop_roi.get("left")))
        top = crop_roi.get("yStart", crop_roi.get("y", crop_roi.get("top")))
        right = crop_roi.get("xEnd", crop_roi.get("right"))
        bottom = crop_roi.get("yEnd", crop_roi.get("bottom"))
        if right is None and left is not None and crop_roi.get("width") is not None:
            right = left + crop_roi["width"]
        if bottom is None and top is not None and crop_roi.get("height") is not None:
            bottom = top + crop_roi["height"]
        if None in (left, top, right, bottom):
            raise ValueError("crop_roi cần xStart/yStart/xEnd/yEnd hoặc x/y/width/height")

        left, right = sorted((int(left), int(right)))
        top, bottom = sorted((int(top), int(bottom)))
        if left < 0 or top < 0 or left >= right or top >= bottom:
            raise ValueError("crop_roi phải là vùng pixel hợp lệ và có kích thước lớn hơn 0")
        return left, top, right, bottom

    def _train_one_roi(self, roi_path: Path):
        """Huấn luyện một ROI và lưu index FAISS + memory bank tương ứng.

        Args:
            roi_path (Path): Đường dẫn tới thư mục dữ liệu của ROI.

        Returns:
            bool: True nếu huấn luyện thành công, False nếu bỏ qua.
        """
        roi_name = roi_path.name
        if self.model_root is None:
            raise RuntimeError("Trainer chưa được khởi tạo thư mục model cho phiên train")
        save_dir = self.model_root if self._flat_session_layout else self.model_root / roi_name
        save_dir.mkdir(parents=True, exist_ok=True)

        logger.info("\n%s", "=" * 72)
        logger.info("Training ROI: %s", roi_name)
        logger.info("Data path: %s", roi_path)
        logger.info("Save path: %s", save_dir)
        logger.info("%s", "=" * 72)

        crop_box = None if self._images_are_pre_cropped else self._get_crop_box()
        dataset_root = roi_path / "good" if (roi_path / "good").is_dir() else roi_path
        direct_images = any(
            path.is_file() and path.suffix.lower() in PatchCoreImageDataset.IMAGE_SUFFIXES
            for path in dataset_root.iterdir()
        )
        if direct_images:
            dataset = PatchCoreImageDataset(
                dataset_root,
                crop_box=crop_box,
                transform=self.transform,
            )
        else:
            dataset = (
                CroppedImageFolder(str(dataset_root), crop_box=crop_box, transform=self.transform)
                if crop_box is not None
                else ImageFolder(str(dataset_root), transform=self.transform)
            )
        if len(dataset) == 0:
            logger.warning("[SKIP] ROI %s is empty", roi_name)
            return False

        loader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=self.config.num_workers,
            pin_memory=(self.device == "cuda"),
        )

        self._build_backbone()
        all_features = []

        logger.info("Extracting features...")
        for images, _ in tqdm(loader, desc=f"ROI {roi_name}"):
            features = self._extract_features(images, self.device, self.layer2, self.layer3, self.layer4)
            all_features.append(features)

        if not all_features:
            logger.warning("[SKIP] No feature extracted from ROI %s", roi_name)
            return False

        features = np.concatenate(all_features, axis=0)
        logger.info("Raw feature shape: %s", features.shape)

        features = features.reshape(-1, features.shape[-1]).astype(np.float32)
        logger.info("Flatten feature shape: %s", features.shape)

        if len(features) == 0:
            logger.warning("[SKIP] Empty feature set for ROI %s", roi_name)
            return False

        sample_count = max(1, int(len(features) * self.config.coreset_ratio))
        sample_count = min(sample_count, len(features))
        rng = np.random.default_rng(self.config.seed)
        chosen_idx = rng.choice(len(features), size=sample_count, replace=False)
        features = features[chosen_idx]
        logger.info("After coreset: %s", features.shape)

        vector_dim = features.shape[1]
        n_list = max(1, min(self.config.n_list, len(features)))
        quantizer = faiss.IndexFlatL2(vector_dim)
        index = faiss.IndexIVFFlat(quantizer, vector_dim, n_list, faiss.METRIC_L2)

        logger.info("Training FAISS index: n_list=%s, d=%s", n_list, vector_dim)
        index.train(features)
        index.add(features)
        index.nprobe = min(self.config.n_probe, n_list)

        faiss.write_index(index, str(save_dir / "patchcore.index"))
        np.save(str(save_dir / "memory.npy"), features)

        logger.info("[DONE] %s", roi_name)
        return True

    def run_from_folder(
        self,
        images: list[Image.Image | np.ndarray | bytes],
        model_root: str | Path,
        roi_name: str = "patchcore",
        purpose: str = "train patchcore",
        model_variant: str = "the_first",
    ):
        """Thay thế session của ROI, chép ảnh đầu vào rồi train.

        Args:
            images: Danh sách ảnh dạng PIL, NumPy hoặc bytes PNG/JPEG.
            model_root: Folder gốc lưu cả ảnh train và model của session. Các
                session cũ của ROI này sẽ bị xóa trước khi tạo session mới.
            roi_name: Tên vùng train dùng để xác định các session cần thay thế.
            purpose: Mục đích được lưu trong training record.

        Returns:
            dict: Metadata của phiên train vừa hoàn tất.

        Raises:
            ValueError: Nếu danh sách ảnh rỗng, ảnh không hợp lệ hoặc roi_name
                không hợp lệ.
        """
        model_root = Path(model_root).expanduser().resolve()
        if model_variant not in {"the_first", "runtime"}:
            raise ValueError("model_variant phải là 'the_first' hoặc 'runtime'")
        if not images:
            raise ValueError("images không được rỗng")
        if not roi_name or Path(roi_name).name != roi_name:
            raise ValueError("roi_name chỉ được chứa tên thư mục đơn")

        normalized_images = []
        for image in images:
            if isinstance(image, Image.Image):
                normalized_images.append(image.convert("RGB"))
            elif isinstance(image, np.ndarray):
                if image.size == 0:
                    raise ValueError("Ảnh NumPy không được rỗng")
                normalized_images.append(Image.fromarray(image).convert("RGB"))
            elif isinstance(image, bytes):
                try:
                    with Image.open(BytesIO(image)) as decoded_image:
                        normalized_images.append(decoded_image.convert("RGB"))
                except (OSError, ValueError) as error:
                    raise ValueError("Bytes ảnh không hợp lệ") from error
            else:
                raise ValueError(
                    "Mỗi phần tử images phải là PIL.Image.Image, numpy.ndarray hoặc bytes"
                )

        session_roi_name = roi_name.strip().lower()
        existing_runtime_session = self._find_runtime_session(
            model_root,
            session_roi_name,
        )
        if existing_runtime_session is not None:
            model_variant = "runtime"
        session_id = (
            f"model_{session_roi_name}_crop_"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        )
        model_root.mkdir(parents=True, exist_ok=True)
        if existing_runtime_session is not None:
            session_root = existing_runtime_session
            session_id = session_root.name
            logger.info(
                "[PATCHCORE] Giữ session runtime hiện tại, không xóa ảnh runtime: %s",
                session_root,
            )
        else:
            old_sessions = model_root.glob(f"model_{session_roi_name}_crop_*")
            for old_session in old_sessions:
                if old_session.is_dir():
                    shutil.rmtree(old_session)
            session_root = model_root / session_id

        session_variant_root = session_root / model_variant
        runtime_root = session_root / "runtime"
        first_root = session_root / "the_first"
        roi_original_root = session_variant_root / "original"
        roi_data_root = session_variant_root / "good"
        self.data_root = roi_data_root
        self.model_root = session_variant_root
        self._flat_session_layout = True
        (runtime_root / "good").mkdir(parents=True, exist_ok=True)
        first_root.mkdir(parents=True, exist_ok=True)
        if model_variant == "the_first":
            roi_original_root.mkdir(parents=True, exist_ok=True)
        roi_data_root.mkdir(parents=True, exist_ok=True)
        self.model_root.mkdir(parents=True, exist_ok=True)

        crop_box = self._get_crop_box()
        for index, image in enumerate(normalized_images, start=1):
            image_name = f"image_{index:04d}.png"
            if model_variant == "runtime":
                image.save(roi_data_root / image_name, format="PNG")
            else:
                original_path = roi_original_root / image_name
                image.save(original_path, format="PNG")
                if crop_box is None:
                    image.save(roi_data_root / image_name, format="PNG")
                else:
                    image.crop(crop_box).save(roi_data_root / image_name, format="PNG")

        # Both branches materialize the good folder before training. Avoid a
        # second crop inside _train_one_roi.
        self._images_are_pre_cropped = True

        self.device = self.config.device
        self.transform = self._build_transform(self.config.img_size)

        rois = self._get_roi_folders()
        if not rois:
            raise FileNotFoundError(f"Không có ROI trong phiên train: {self.data_root}")

        logger.info("[PATCHCORE] Nguồn train: %s", model_variant)
        logger.info("[PATCHCORE] Số ảnh nhận vào: %s", len(normalized_images))
        logger.info("Found ROI folders: %s", [path.name for path in rois])
        for roi_path in rois:
            self._train_one_roi(roi_path)

        logger.info("ALL TRAIN DONE")

        inference_result = self._run_post_training_inference()

        model_file = self.model_root / "patchcore.index"

        record = self.record_manager.save_record(
            config=self.config,
            purpose=purpose,
            roi_list=[roi_name],
            crop_roi=self.config.crop_roi,
            model_root=session_root,
            model_file=model_file if model_file.exists() else "",
            inference_result=inference_result,
            runtime_images_root=session_root / "runtime",
            run_id=session_id,
            status="completed",
        )
        logger.info("Saved training record: %s", record["run_id"])
        return record

    def _run_post_training_inference(self) -> str:
        """Chạy inference trên ảnh train đầu tiên và lưu overlay cạnh model.

        Returns:
            str: Đường dẫn ảnh inference hoặc chuỗi rỗng nếu không có ảnh.

        Raises:
            RuntimeError: Nếu model vừa train không thể load hoặc inference lỗi.
        """
        if self.model_root is None:
            return ""
        image_paths = sorted(
            path for path in self.data_root.iterdir()
            if path.is_file() and path.suffix.lower() in PatchCoreImageDataset.IMAGE_SUFFIXES
        )
        model_file = self.model_root / "patchcore.index"
        if not image_paths or not model_file.exists():
            logger.warning("[PATCHCORE] Bỏ qua inference sau train: thiếu ảnh hoặc model")
            return ""

        image = cv2.imread(str(image_paths[0]))
        if image is None:
            return ""
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        inference_config = PatchCoreAnomalyConfig(
            index_path=str(model_file),
            nprobe=self.config.n_probe,
            img_size=self.config.img_size,
            device=self.config.device,
        )
        model = ModelPatchCore(inference_config)
        model.load_model()
        if model.index.d != 448:
            logger.warning(
                "[PATCHCORE] Bỏ qua inference kiểm chứng: index dimension=%s, "
                "backbone dimension=448",
                model.index.d,
            )
            model.unload()
            return ""
        score, overlay = model.predict(image_rgb)
        model.unload()
        output_path = self.model_root / "inference_result.png"
        if not cv2.imwrite(str(output_path), overlay):
            raise RuntimeError(f"Không thể lưu ảnh inference: {output_path}")
        logger.info("[PATCHCORE] Inference sau train: score=%.6f", score)
        logger.info("[PATCHCORE] Đã lưu inference: %s", output_path)
        return str(output_path)

    @staticmethod
    def _find_runtime_session(
        model_root: Path,
        session_roi_name: str,
    ) -> Path | None:
        """Tìm session cùng ROI đang có ảnh runtime để tái sử dụng."""
        candidates = sorted(
            (
                path
                for path in model_root.glob(
                    f"model_{session_roi_name}_crop_*/runtime/good/*"
                )
                if path.is_file()
            ),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return candidates[0].parents[2] if candidates else None

    def run(self, images, model_root, roi_name="patchcore", purpose="train patchcore"):
        """Alias public để train từ danh sách ảnh và folder model."""
        return self.run_from_folder(images, model_root, roi_name=roi_name, purpose=purpose)


def main(argv=None):
    """Entry point CLI; nhận đường dẫn ảnh sau cờ ``--images``."""
    parser = argparse.ArgumentParser(description="PatchCore trainer")
    parser.add_argument("--input-folder", required=True)
    parser.add_argument("--model-root", required=True)
    parser.add_argument("--roi-name", default="patchcore")
    args = parser.parse_args(argv)
    image_paths = sorted(
        path for path in Path(args.input_folder).expanduser().resolve().iterdir()
        if path.is_file() and path.suffix.lower() in PatchCoreImageDataset.IMAGE_SUFFIXES
    )
    images = [Image.open(path).convert("RGB") for path in image_paths]
    TrainlerPatchCore().run(
        images,
        args.model_root,
        roi_name=args.roi_name,
    )
    return 0


TrainerPatchCore = TrainlerPatchCore


if __name__ == "__main__":
    raise SystemExit(main())


