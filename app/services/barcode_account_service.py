import re
from typing import Dict, List, Optional, Any, Tuple
from app.repository.barcode_account_repository import BarcodeAccountRepository


class BarcodeAccountService:
    """
    Service xử lý nghiệp vụ quản lý tài khoản Barcode và tài khoản Admin:
    - Kiểm tra tính hợp lệ của mã Barcode (chỉ chữ và số, không khoảng trắng, không tiếng Việt).
    - Tạo, lưu trữ tài khoản vào file JSON và cập nhật dữ liệu.
    - Trả về danh sách hiển thị: nhóm Manager trước, User sau, Admin không show.
    """

    def __init__(self, repository: Optional[BarcodeAccountRepository] = None):
        self.repository = repository or BarcodeAccountRepository()

    @staticmethod
    def validate_barcode(barcode: str) -> Tuple[bool, str]:
        """
        Kiểm tra mã barcode có hợp lệ không:
        - Chỉ có chữ và số (a-z, A-Z, 0-9).
        - Không tiếng Việt có dấu.
        - Không khoảng trắng.
        - Không rỗng.
        """
        if barcode is None:
            return False, "Mã barcode không được để trống."

        raw_code = str(barcode)

        # Kiểm tra khoảng trắng
        if re.search(r"\s", raw_code):
            return False, "Mã barcode không được chứa khoảng trắng."

        trimmed = raw_code.strip()
        if not trimmed:
            return False, "Mã barcode không được để trống."

        # Kiểm tra chỉ chứa chữ và số ASCII (a-z, A-Z, 0-9)
        # Bác bỏ hoàn toàn ký tự có dấu tiếng Việt, dấu cách và ký tự đặc biệt
        if not re.match(r"^[a-zA-Z0-9]+$", trimmed):
            return False, "Mã barcode chỉ được chứa chữ và số, không dấu tiếng Việt và không ký tự đặc biệt."

        return True, ""

    def validate_account_data(
        self,
        operator: str,
        factory: str,
        line: str,
        role: str,
        barcode: str,
        check_duplicate: bool = True
    ) -> Tuple[bool, str]:
        """
        Xác thực dữ liệu form tạo tài khoản Barcode:
        - Tên người thao tác không được để trống.
        - Nhà máy không được để trống.
        - Chuyền không được để trống.
        - Loại tài khoản phải là Manager hoặc User.
        - Mã barcode phải hợp lệ và chưa tồn tại.
        """
        if not operator or not operator.strip():
            return False, "Vui lòng nhập tên người thao tác."

        if not factory or not factory.strip():
            return False, "Vui lòng nhập tên nhà máy."

        if not line or not line.strip():
            return False, "Vui lòng nhập tên chuyền."

        normalized_role = role.strip().capitalize() if role else ""
        if normalized_role not in ["Manager", "User"]:
            return False, "Loại tài khoản phải là 'Manager' hoặc 'User'."

        is_valid_code, err_msg = self.validate_barcode(barcode)
        if not is_valid_code:
            return False, err_msg

        if check_duplicate:
            existing = self.repository.find_by_barcode(barcode.strip())
            if existing:
                return False, f"Mã barcode '{barcode.strip()}' đã tồn tại trên hệ thống."

        return True, ""

    def get_barcode_accounts(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tài khoản barcode:
        - Chỉ lấy Manager và User, Admin không cần show.
        - Sắp xếp nhóm: Manager trước, User sau.
        """
        return self.repository.get_barcode_accounts()

    def create_account(
        self,
        operator: str,
        factory: str,
        line: str,
        role: str,
        barcode: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Tạo tài khoản mới và lưu vào file storage:
        - Kiểm tra hợp lệ barcode và dữ liệu đầu vào.
        - Lưu vào file.
        - Trả về kết quả và đối tượng tài khoản đã tạo.
        """
        is_valid, err_msg = self.validate_account_data(
            operator=operator,
            factory=factory,
            line=line,
            role=role,
            barcode=barcode,
            check_duplicate=True
        )
        if not is_valid:
            return False, err_msg, None

        normalized_role = "Manager" if role.strip().lower() == "manager" else "User"
        new_account = self.repository.add_account(
            operator=operator,
            factory=factory,
            line=line,
            role=normalized_role,
            barcode=barcode
        )
        return True, "Tạo tài khoản thành công!", new_account

    def delete_account(self, barcode: str) -> Tuple[bool, str]:
        """Xóa tài khoản theo mã barcode."""
        if not barcode or not barcode.strip():
            return False, "Mã barcode không hợp lệ."

        success = self.repository.delete_account(barcode.strip())
        if success:
            return True, "Xóa tài khoản thành công!"
        return False, "Không tìm thấy tài khoản với mã barcode này."

    def get_admin(self) -> Dict[str, str]:
        """Lấy thông tin tài khoản admin (chỉ cần username và password)."""
        return self.repository.get_admin()

    def update_admin(self, username: str, password: Optional[str] = None) -> Tuple[bool, str]:
        """Cập nhật thông tin tài khoản admin."""
        if not username or not username.strip():
            return False, "Tài khoản admin không được để trống."
        self.repository.update_admin(username=username, password=password)
        return True, "Cập nhật tài khoản admin thành công!"
