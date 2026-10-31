import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.config import PATH_FILE_BARCODE_ACCOUNT
from app.utils import Folder


class BarcodeAccountRepository:
    """
    Repository phụ trách lưu trữ và truy xuất cấu hình tài khoản Barcode và Admin.
    Dữ liệu được lưu trữ tại file JSON: app/storage/barcode_accounts.json
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or PATH_FILE_BARCODE_ACCOUNT
        self._ensure_file_exists()

    def _get_default_data(self) -> Dict[str, Any]:
        """Tạo dữ liệu mặc định ban đầu nếu file chưa tồn tại."""
        return {
            "admin": {
                "username": "admin",
                "password": "123"
            },
            "accounts": []
        }

    def _ensure_file_exists(self) -> None:
        """Đảm bảo thư mục cha và file JSON tồn tại."""
        p = Path(self.file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            self.save_data(self._get_default_data())

    def load_data(self) -> Dict[str, Any]:
        """Đọc toàn bộ dữ liệu cấu hình tài khoản từ file JSON."""
        try:
            data = Folder.read_json_from_file(self.file_path)
            if not isinstance(data, dict):
                return self._get_default_data()
            if "admin" not in data:
                data["admin"] = {"username": "admin", "password": "123"}
            if "accounts" not in data or not isinstance(data["accounts"], list):
                data["accounts"] = []
            return data
        except Exception as e:
            print(f"❌ [BarcodeAccountRepository] Lỗi đọc dữ liệu: {e}")
            return self._get_default_data()

    def save_data(self, data: Dict[str, Any]) -> None:
        """Ghi dữ liệu cấu hình vào file JSON với định dạng UTF-8."""
        Folder.write_json_in_file(self.file_path, data)

    def get_admin(self) -> Dict[str, str]:
        """Lấy thông tin tài khoản admin (chỉ gồm username và password)."""
        data = self.load_data()
        return data.get("admin", {"username": "admin", "password": "123"})

    def update_admin(self, username: str, password: Optional[str] = None) -> bool:
        """Cập nhật thông tin tài khoản admin."""
        data = self.load_data()
        if "admin" not in data:
            data["admin"] = {}
        data["admin"]["username"] = username.strip()
        if password is not None:
            data["admin"]["password"] = password.strip()
        self.save_data(data)
        return True

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Lấy toàn bộ danh sách tài khoản trong mảng accounts."""
        data = self.load_data()
        return data.get("accounts", [])

    def get_barcode_accounts(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các tài khoản barcode để hiển thị lên bảng:
        - Admin KHÔNG cần show (loại bỏ hoàn toàn tài khoản admin).
        - Sắp xếp theo nhóm: Quản lý (Manager) hiển thị trước, sau đó đến User.
        """
        accounts = self.get_all_accounts()
        # Lọc bỏ mọi tài khoản có role là Admin
        barcode_accounts = [
            acc for acc in accounts
            if str(acc.get("role", "")).strip().lower() != "admin"
        ]
        # Sắp xếp theo nhóm: Manager (0) trước, User (1) sau, tiếp theo theo tên người thao tác
        barcode_accounts.sort(
            key=lambda acc: (
                0 if str(acc.get("role", "")).strip().lower() == "manager" else 1,
                acc.get("operator", "").lower()
            )
        )
        return barcode_accounts

    def find_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Tìm tài khoản theo mã barcode."""
        accounts = self.get_all_accounts()
        target = barcode.strip()
        for acc in accounts:
            if acc.get("barcode", "").strip() == target:
                return acc
        return None

    def add_account(
        self,
        operator: str,
        factory: str,
        line: str,
        role: str,
        barcode: str
    ) -> Dict[str, Any]:
        """Thêm mới một tài khoản barcode vào danh sách và lưu vào file."""
        data = self.load_data()
        accounts = data.get("accounts", [])

        normalized_role = "Manager" if role.strip().lower() == "manager" else "User"

        new_account = {
            "operator": operator.strip(),
            "factory": factory.strip(),
            "line": line.strip(),
            "role": normalized_role,
            "barcode": barcode.strip(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        accounts.append(new_account)
        data["accounts"] = accounts
        self.save_data(data)
        return new_account

    def delete_account(self, barcode: str) -> bool:
        """Xóa tài khoản theo mã barcode và cập nhật file."""
        data = self.load_data()
        accounts = data.get("accounts", [])
        initial_count = len(accounts)
        target = barcode.strip()
        filtered = [acc for acc in accounts if acc.get("barcode", "").strip() != target]
        if len(filtered) < initial_count:
            data["accounts"] = filtered
            self.save_data(data)
            return True
        return False
