from typing import Dict
from pathlib import Path
from app.config import PATH_COUNT_PRODUCT
from app.utils import Folder


class ProductCountRepository:
    """
    Repository quản lý đọc và ghi file lưu trữ số lượng sản phẩm OK, NG và Tổng.
    """

    def __init__(self, path_file: str = PATH_COUNT_PRODUCT) -> None:
        self.path_file = path_file
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """
        Khởi tạo file json mặc định nếu file chưa tồn tại trên ổ cứng.
        """
        target_path = Path(self.path_file)
        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            default_data = {"ok": 0, "ng": 0, "total": 0}
            Folder.write_json_in_file(self.path_file, default_data)

    def read_counts(self) -> Dict[str, int]:
        """
        Đọc số lượng sản phẩm OK, NG và Tổng từ file JSON.

        Returns:
            Dict[str, int]: Dictionary chứa {"ok": int, "ng": int, "total": int}.
        """
        data = Folder.read_json_from_file(self.path_file)
        if not isinstance(data, dict):
            data = {}
        ok = int(data.get("ok", 0))
        ng = int(data.get("ng", 0))
        total = int(data.get("total", ok + ng))
        return {"ok": ok, "ng": ng, "total": total}

    def save_counts(self, counts: Dict[str, int]) -> bool:
        """
        Lưu dữ liệu số lượng sản phẩm vào file JSON.

        Args:
            counts (Dict[str, int]): Dictionary số lượng cần lưu.

        Returns:
            bool: True nếu ghi file thành công, False nếu thất bại.
        """
        data = {
            "ok": int(counts.get("ok", 0)),
            "ng": int(counts.get("ng", 0)),
            "total": int(counts.get("total", 0)),
        }
        Folder.write_json_in_file(self.path_file, data)
        return True

    def reset_counts(self) -> Dict[str, int]:
        """
        Đặt lại toàn bộ số đếm OK, NG, Tổng về 0 và lưu vào file.

        Returns:
            Dict[str, int]: Số đếm đã reset {"ok": 0, "ng": 0, "total": 0}.
        """
        initial = {"ok": 0, "ng": 0, "total": 0}
        self.save_counts(initial)
        return initial

    def increment_count(self, is_ok: bool) -> Dict[str, int]:
        """
        Tăng số lượng sản phẩm theo kết quả phán định (OK hoặc NG) và cộng vào Tổng.

        Args:
            is_ok (bool): True nếu toàn bộ sản phẩm OK, False nếu NG.

        Returns:
            Dict[str, int]: Dữ liệu số đếm mới nhất sau khi tăng.
        """
        counts = self.read_counts()
        if is_ok:
            counts["ok"] += 1
        else:
            counts["ng"] += 1
        counts["total"] = counts["ok"] + counts["ng"]
        self.save_counts(counts)
        return counts
