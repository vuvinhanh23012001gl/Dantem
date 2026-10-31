import json
import os
from pathlib import Path
import tempfile
from app.config import PATH_FILE_DATA_CONFIG_JUDMENT_LAW


class JudmentLawProductRepository:
    """Repository quản lý dữ liệu Product -> Face -> Item."""

    def __init__(self):
        """Khởi tạo repository, tạo file nếu chưa có và nạp dữ liệu."""
        self.path = Path(PATH_FILE_DATA_CONFIG_JUDMENT_LAW)
        self._ensure_file_exists()
        self.data = self._load()

    def _ensure_file_exists(self) -> None:
        """Tạo file JSON rỗng nếu chưa tồn tại."""
        if self.path.exists():
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({}, f)

    @staticmethod
    def clean_undefined_keys(data: dict) -> bool:
        """Kiểm tra và thay thế key 'undefined' bằng key '0' trong cấu trúc judgment law.

        Nếu trong cùng inspector có cả '0' và 'undefined', giá trị 'undefined'
        sẽ thay thế cho '0' và xóa key 'undefined'.
        Returns:
            bool: True nếu có sự thay đổi dữ liệu.
        """
        changed = False
        if not isinstance(data, dict):
            return False

        for k, v in list(data.items()):
            if isinstance(v, dict):
                if "undefined" in v:
                    undefined_val = v.pop("undefined")
                    if "0" in v and isinstance(v["0"], dict) and isinstance(undefined_val, dict):
                        v["0"].update(undefined_val)
                    else:
                        v["0"] = undefined_val
                    changed = True
                if JudmentLawProductRepository.clean_undefined_keys(v):
                    changed = True
        return changed

    def _load(self) -> dict:
        """Đọc dữ liệu từ file JSON và tự động làm sạch key 'undefined'.
        Returns:
            dict: Dữ liệu.
        """
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if self.clean_undefined_keys(data):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        return data

    def save(self) -> None:
        """Lưu dữ liệu xuống file JSON sau khi làm sạch key 'undefined'."""
        self.clean_undefined_keys(self.data)
        descriptor, temporary = tempfile.mkstemp(prefix=self.path.name, suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(self.data, stream, ensure_ascii=False, indent=4)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def exists(self, product_id: str, face_id: str, item_id: str) -> bool:
        """Kiểm tra Item có tồn tại.
        Args:
            product_id: ID sản phẩm.
            frame_id: ID Frame.
            item_id: ID Item.
        Returns:
            bool: True nếu tồn tại.
        """
        return item_id in self.data.get(product_id, {}).get(face_id, {})

    def get(self, product_id: str, face_id: str, item_id: str) -> dict | None:
        """Lấy dữ liệu Item.
        Args:
            product_id: ID sản phẩm.
            frame_id: ID Frame.
            item_id: ID Item.
        Returns:
            dict | None: Dữ liệu Item.
        """
        return self.data.get(product_id, {}).get(face_id, {}).get(item_id)

    def upsert(self, product_id: str, face_id: str, item_id: str, item_data: dict) -> None:
        """Thêm hoặc cập nhật Item.
        Args:
            product_id: ID sản phẩm.
            frame_id: ID Frame.
            item_id: ID Item.
            item_data: Dữ liệu Item.
        """
        self.data.setdefault(product_id, {})
        self.data[product_id].setdefault(face_id, {})
        self.data[product_id][face_id][item_id] = item_data
        self.save()

    def delete(self, product_id: str, face_id: str, item_id: str) -> bool:
        """Xóa Item.
        Args:
            product_id: ID sản phẩm.
            frame_id: ID Frame.
            item_id: ID Item.
        Returns:
            bool: True nếu xóa thành công.
        """
        try:
            del self.data[product_id][face_id][item_id]
            self.save()
            return True
        except KeyError:
            return False

    def delete_product(self, product_id: str) -> bool:
        """Xóa toàn bộ Product.
        Args:
            product_id: ID sản phẩm.
        Returns:
            bool: True nếu xóa thành công.
        """
        key = str(product_id)
        if key not in self.data:
            return False
        previous = self.data.pop(key)
        try:
            self.save()
            return True
        except OSError:
            self.data[key] = previous
            raise

    def get_product(self, product_id: str) -> dict:
        """Lấy dữ liệu Product.
        Args:
            product_id: ID sản phẩm.
        Returns:
            dict: Dữ liệu Product.
        """
        return self.data.get(product_id, {})

    def get_face(self, product_id: str, face_id: str) -> dict:
        """Lấy dữ liệu Frame.
        Args:
            product_id: ID sản phẩm.
            frame_id: ID Frame.
        Returns:
            dict: Dữ liệu Frame.
        """
        return self.data.get(product_id, {}).get(face_id, {})

    def get_frame(self, product_id: str, frame_id: str) -> dict:
        return self.get_face(product_id, frame_id)

    def get_product_ids(self) -> list[str]:
        """Lấy danh sách Product ID.
        Returns:
            list[str]: Danh sách Product ID.
        """
        return list(self.data.keys())

    def get_face_ids(self, product_id: str) -> list[str]:
        """Lấy danh sách Frame ID.
        Args:
            product_id: ID sản phẩm.
        Returns:
            list[str]: Danh sách Frame ID.
        """
        return list(self.data.get(product_id, {}).keys())

    def get_frame_ids(self, product_id: str) -> list[str]:
        return self.get_face_ids(product_id)

    def get_item_ids(self, product_id: str, face_id: str) -> list[str]:
        """Lấy danh sách Item ID.
        Args:
            product_id: ID sản phẩm.
            frame_id: ID Frame.
        Returns:
            list[str]: Danh sách Item ID.
        """
        return list(self.data.get(product_id, {}).get(face_id, {}).keys())

    def clear(self) -> None:
        """Xóa toàn bộ dữ liệu."""
        self.data.clear()
        self.save()

    def load_from_dict(self, raw: dict, merge: bool = False) -> None:
        """Nạp dữ liệu từ dict.

        Args:
            raw: Dữ liệu nguồn.
            merge: True để gộp, False để ghi đè.
        """
        if not merge:
            self.data = raw
        else:
            self._deep_update(self.data, raw)
        self.save()

    def _deep_update(self, target: dict, source: dict) -> dict:
        """Gộp đệ quy hai dict.
        Args:
            target: Dữ liệu đích.
            source: Dữ liệu nguồn.
        Returns:
            dict: Dữ liệu sau khi cập nhật.
        """
        for k, v in source.items():
            if isinstance(v, dict) and isinstance(target.get(k), dict):
                self._deep_update(target[k], v)
            else:
                target[k] = v
        return target
    
    def update_data(self, data: dict, merge: bool = False) -> None:
        """Cập nhật dữ liệu repository.
        Args:
            data: Dữ liệu mới.
            merge: True để gộp, False để ghi đè.
        """
        if merge:
            self._deep_update(self.data, data)
        else:
            if not isinstance(self.data, dict):
                self.data = {}
            # Cập nhật theo từng product_id để bảo toàn cấu hình của các sản phẩm khác
            for prod_id, prod_data in data.items():
                self.data[str(prod_id)] = prod_data
        self.save()