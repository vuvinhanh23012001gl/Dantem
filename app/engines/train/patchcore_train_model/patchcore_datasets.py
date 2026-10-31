from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset
from torchvision.datasets import ImageFolder


class CroppedImageFolder(ImageFolder):
    """ImageFolder crop ảnh trước khi áp dụng transform.

    Args:
        root: Thư mục dữ liệu theo cấu trúc ImageFolder.
        crop_box: Tọa độ ``(left, top, right, bottom)`` theo pixel ảnh gốc.
        transform: Bộ tiền xử lý sau khi crop.

    Raises:
        ValueError: Nếu crop_box không có bốn tọa độ hoặc vùng crop không hợp lệ.
    """

    def __init__(self, root, crop_box, transform=None):
        """Khởi tạo dataset ImageFolder có crop ảnh.

        Args:
            root: Thư mục dữ liệu theo cấu trúc ImageFolder.
            crop_box: Tọa độ ``(left, top, right, bottom)``.
            transform: Transform áp dụng sau khi crop.

        Returns:
            None.

        Raises:
            FileNotFoundError: Nếu root không tồn tại.
            ValueError: Nếu crop_box không hợp lệ khi đọc ảnh.
        """
        self.crop_box = crop_box
        super().__init__(root, transform=transform)

    def __getitem__(self, index):
        """Đọc, crop và transform một ảnh theo chỉ số dataset.

        Args:
            index: Vị trí ảnh trong dataset.

        Returns:
            tuple: ``(image, target)`` theo chuẩn ImageFolder.

        Raises:
            IndexError: Nếu index nằm ngoài dataset.
            OSError: Nếu file ảnh không thể đọc.
        """
        path, target = self.samples[index]
        image = self.loader(path).crop(self.crop_box)
        if self.transform is not None:
            image = self.transform(image)
        if self.target_transform is not None:
            target = self.target_transform(target)
        return image, target


class PatchCoreImageDataset(Dataset):
    """Dataset đọc ảnh trực tiếp trong folder PatchCore.

    Args:
        root: Folder chứa ảnh train trực tiếp.
        crop_box: Tọa độ ``(left, top, right, bottom)`` hoặc None.
        transform: Bộ tiền xử lý ảnh.

    Raises:
        FileNotFoundError: Nếu folder không tồn tại hoặc không có ảnh hỗ trợ.
    """

    IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    def __init__(self, root: str | Path, crop_box=None, transform=None):
        """Khởi tạo dataset ảnh phẳng của PatchCore.

        Args:
            root: Folder chứa ảnh train trực tiếp.
            crop_box: Tọa độ crop hoặc None nếu không crop.
            transform: Transform áp dụng sau crop.

        Returns:
            None.

        Raises:
            FileNotFoundError: Nếu root không tồn tại hoặc không có ảnh hỗ trợ.
        """
        self.root = Path(root)
        if not self.root.exists():
            raise FileNotFoundError(f"Không tìm thấy folder ảnh: {self.root}")
        self.samples = sorted(
            path
            for path in self.root.iterdir()
            if path.is_file() and path.suffix.lower() in self.IMAGE_SUFFIXES
        )
        if not self.samples:
            raise FileNotFoundError(f"Không có ảnh train trong folder: {self.root}")
        self.crop_box = crop_box
        self.transform = transform

    def __len__(self):
        """Trả về số lượng ảnh train hợp lệ.

        Returns:
            int: Số file ảnh được dataset thu thập.
        """
        return len(self.samples)

    def __getitem__(self, index):
        """Đọc, crop tùy chọn và transform một ảnh train.

        Args:
            index: Vị trí ảnh trong dataset.

        Returns:
            tuple: ``(image_tensor, 0)``; nhãn luôn bằng 0 vì PatchCore
                học ảnh tốt thay vì phân loại nhãn.

        Raises:
            IndexError: Nếu index nằm ngoài dataset.
            OSError: Nếu file ảnh không thể đọc.
            ValueError: Nếu crop_box không hợp lệ.
        """
        image = Image.open(self.samples[index]).convert("RGB")
        if self.crop_box is not None:
            image = image.crop(self.crop_box)
        if self.transform is not None:
            image = self.transform(image)
        return image, 0