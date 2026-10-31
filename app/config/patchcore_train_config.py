from dataclasses import dataclass, field
# pyrefly: ignore [missing-import]
import torch

@dataclass
class PatchCoreTrainConfig:
    """Tham số train PatchCore, không chứa đường dẫn dữ liệu của phiên train."""

    img_size: int = 256
    batch_size: int = 32
    coreset_ratio: float = 0.2
    n_list: int = 32
    n_probe: int = 8
    num_workers: int = 0
    seed: int = 42
    device: str = field(default_factory=lambda: "cuda" if torch.cuda.is_available() else "cpu")
    crop_roi: dict | None = None

    def resolve(self):
        return self
