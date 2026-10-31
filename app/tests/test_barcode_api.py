import unittest
from fastapi.testclient import TestClient
from app.main import fastapi_app


class TestBarcodeAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(fastapi_app)

    def test_get_barcode_accounts(self):
        response = self.client.get("/barcode/accounts")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["status"])
        self.assertIsInstance(json_data["data"], list)

    def test_create_barcode_account_invalid_code(self):
        # Kiểm tra gửi barcode có dấu tiếng Việt
        payload = {
            "operator": "Test User",
            "factory": "Test Factory",
            "line": "Test Line",
            "role": "Manager",
            "barcode": "MÃ_LỖI_123"
        }
        response = self.client.post("/barcode/account", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("chữ và số", response.json()["detail"])

    def test_create_barcode_account_with_spaces(self):
        # Kiểm tra gửi barcode có khoảng trắng
        payload = {
            "operator": "Test User",
            "factory": "Test Factory",
            "line": "Test Line",
            "role": "User",
            "barcode": "CODE 123"
        }
        response = self.client.post("/barcode/account", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("khoảng trắng", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
