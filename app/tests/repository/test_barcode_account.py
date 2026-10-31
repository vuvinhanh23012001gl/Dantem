import os
import tempfile
import unittest
from app.repository.barcode_account_repository import BarcodeAccountRepository
from app.services.barcode_account_service import BarcodeAccountService


class TestBarcodeAccount(unittest.TestCase):
    def setUp(self):
        # Sử dụng file tạm trong thư mục temp
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.repo = BarcodeAccountRepository(file_path=self.temp_file.name)
        self.service = BarcodeAccountService(repository=self.repo)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except Exception:
                pass

    def test_default_structure(self):
        data = self.repo.load_data()
        self.assertIn("admin", data)
        self.assertIn("accounts", data)
        self.assertEqual(data["admin"]["username"], "admin")
        self.assertEqual(data["admin"]["password"], "123")

    def test_validate_barcode_valid(self):
        valid_barcodes = ["BARCODE123", "abc123XYZ", "1234567890", "MNG001"]
        for code in valid_barcodes:
            is_valid, msg = self.service.validate_barcode(code)
            self.assertTrue(is_valid, f"Barcode '{code}' should be valid, but got: {msg}")

    def test_validate_barcode_invalid_vietnamese(self):
        invalid_barcodes = ["BARCODE_việt", "mã123", "quảnlý", "đườnghàn"]
        for code in invalid_barcodes:
            is_valid, msg = self.service.validate_barcode(code)
            self.assertFalse(is_valid, f"Barcode '{code}' should be invalid due to Vietnamese accents")

    def test_validate_barcode_invalid_spaces(self):
        invalid_barcodes = ["BARCODE 123", " 123456", "123456 ", "MNG 001", "abc\t123"]
        for code in invalid_barcodes:
            is_valid, msg = self.service.validate_barcode(code)
            self.assertFalse(is_valid, f"Barcode '{code}' should be invalid due to spaces")

    def test_validate_barcode_invalid_special_chars(self):
        invalid_barcodes = ["BAR-CODE", "MNG_001", "CODE@123", "BC#99"]
        for code in invalid_barcodes:
            is_valid, msg = self.service.validate_barcode(code)
            self.assertFalse(is_valid, f"Barcode '{code}' should be invalid due to special chars")

    def test_create_and_group_sorting(self):
        # Tạo tài khoản User trước
        ok1, msg1, acc1 = self.service.create_account(
            operator="Tran Van User",
            factory="Factory 1",
            line="Line A",
            role="User",
            barcode="USR001"
        )
        self.assertTrue(ok1)

        # Tạo tài khoản Manager sau
        ok2, msg2, acc2 = self.service.create_account(
            operator="Nguyen Van Manager",
            factory="Factory 1",
            line="Line A",
            role="Manager",
            barcode="MNG001"
        )
        self.assertTrue(ok2)

        # Tạo tài khoản User thứ 2
        ok3, msg3, acc3 = self.service.create_account(
            operator="Le Thi User2",
            factory="Factory 2",
            line="Line B",
            role="User",
            barcode="USR002"
        )
        self.assertTrue(ok3)

        # Lấy danh sách barcode accounts
        barcode_list = self.service.get_barcode_accounts()

        # Kiểm tra: Manager phải đứng đầu tiên!
        self.assertEqual(len(barcode_list), 3)
        self.assertEqual(barcode_list[0]["role"], "Manager")
        self.assertEqual(barcode_list[0]["barcode"], "MNG001")

        # Các tài khoản tiếp theo là User
        self.assertEqual(barcode_list[1]["role"], "User")
        self.assertEqual(barcode_list[2]["role"], "User")

        # Kiểm tra Admin không có trong barcode_list
        roles = [acc.get("role", "").lower() for acc in barcode_list]
        self.assertNotIn("admin", roles)

    def test_duplicate_barcode_prevention(self):
        ok1, _, _ = self.service.create_account(
            operator="Op 1",
            factory="F1",
            line="L1",
            role="Manager",
            barcode="DUPLICATE123"
        )
        self.assertTrue(ok1)

        # Tạo tài khoản khác nhưng cùng mã barcode
        ok2, msg2, _ = self.service.create_account(
            operator="Op 2",
            factory="F2",
            line="L2",
            role="User",
            barcode="DUPLICATE123"
        )
        self.assertFalse(ok2)
        self.assertIn("đã tồn tại", msg2)

    def test_delete_account(self):
        self.service.create_account(
            operator="To Delete",
            factory="F1",
            line="L1",
            role="User",
            barcode="DEL123"
        )
        self.assertEqual(len(self.service.get_barcode_accounts()), 1)

        del_ok, _ = self.service.delete_account("DEL123")
        self.assertTrue(del_ok)
        self.assertEqual(len(self.service.get_barcode_accounts()), 0)


if __name__ == "__main__":
    unittest.main()
