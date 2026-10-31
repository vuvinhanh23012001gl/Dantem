import cv2
import numpy as np
import pytest
import zxingcpp

from app.engines.service.barcode_qr_service import BarcodeQRService
from app.judger.barcode_detector import BarcodeDetector
from app.judger.qr_detector import QRDetector


def _generate_barcode_image(text: str = "BARCODE123") -> np.ndarray:
    """Tạo ảnh chứa barcode 1D Code 128 trên nền trắng."""
    barcode = zxingcpp.create_barcode(text, zxingcpp.BarcodeFormat.Code128)
    img_pil = zxingcpp.write_barcode_to_image(barcode)
    arr = np.array(img_pil)  # 2D grayscale
    # Đưa vào canvas lớn hơn
    canvas = np.full((120, 250, 3), 255, dtype=np.uint8)
    h, w = arr.shape[:2]
    # Copy vào giữa canvas
    arr_bgr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR) if len(arr.shape) == 2 else arr
    canvas[20 : 20 + h, 20 : 20 + w] = arr_bgr
    return canvas


def _generate_qr_image(text: str = "QRTEST_SAMPLE") -> np.ndarray:
    """Tạo ảnh chứa mã QR trên nền trắng."""
    qr = zxingcpp.create_barcode(text, zxingcpp.BarcodeFormat.QRCode)
    img_pil = zxingcpp.write_barcode_to_image(qr)
    arr = np.array(img_pil)
    canvas = np.full((150, 150, 3), 255, dtype=np.uint8)
    h, w = arr.shape[:2]
    arr_bgr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR) if len(arr.shape) == 2 else arr
    canvas[10 : 10 + h, 10 : 10 + w] = arr_bgr
    return canvas


def test_barcode_service_scan_success():
    service = BarcodeQRService()
    img = _generate_barcode_image("123456789")
    roi = {"x1": 10, "y1": 10, "x2": 240, "y2": 110}

    result = service.scan_barcode_roi(img, roi)
    assert result["success"] is True
    assert result["text"] == "123456789"
    assert "Code 128" in result["format"]


def test_barcode_service_scan_missing():
    service = BarcodeQRService()
    # Ảnh trắng hoàn toàn
    blank = np.full((100, 100, 3), 255, dtype=np.uint8)
    roi = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}

    result = service.scan_barcode_roi(blank, roi)
    assert result["success"] is False
    assert result["text"] == ""


def test_qr_service_scan_success():
    service = BarcodeQRService()
    img = _generate_qr_image("HELLO_ZXING_QR")
    roi = {"x1": 5, "y1": 5, "x2": 145, "y2": 145}

    result = service.scan_qr_roi(img, roi)
    assert result["success"] is True
    assert result["text"] == "HELLO_ZXING_QR"
    assert "QR" in result["format"]


def test_barcode_detector_evaluate_roi():
    detector = BarcodeDetector()
    img = _generate_barcode_image("CODE_A1")

    # Match case
    roi_match = {
        "name": "Mã vạch thùng",
        "x1": 10,
        "y1": 10,
        "x2": 240,
        "y2": 110,
        "expected_text": "CODE_A1",
    }
    eval_match = detector.evaluate_roi(img, roi_match)
    assert eval_match.ok is True
    assert eval_match.status == "OK"
    assert eval_match.runtime_data["boxes"][0]["text"] == "CODE_A1"

    # Mismatch case
    roi_mismatch = {
        "name": "Mã vạch thùng",
        "x1": 10,
        "y1": 10,
        "x2": 240,
        "y2": 110,
        "expected_text": "CODE_DIFFERENT",
    }
    eval_mismatch = detector.evaluate_roi(img, roi_mismatch)
    assert eval_mismatch.ok is False
    assert eval_mismatch.status == "NG"


def test_qr_detector_evaluate_roi():
    detector = QRDetector()
    img = _generate_qr_image("CARTON_BATCH_2026")

    # Match case
    roi_match = {
        "name": "Mã QR thùng",
        "x1": 5,
        "y1": 5,
        "x2": 145,
        "y2": 145,
        "expected_text": "CARTON_BATCH_2026",
    }
    eval_match = detector.evaluate_roi(img, roi_match)
    assert eval_match.ok is True
    assert eval_match.status == "OK"
    assert eval_match.runtime_data["boxes"][0]["text"] == "CARTON_BATCH_2026"

    # Mismatch case
    roi_mismatch = {
        "name": "Mã QR thùng",
        "x1": 5,
        "y1": 5,
        "x2": 145,
        "y2": 145,
        "expected_text": "WRONG_BATCH",
    }
    eval_mismatch = detector.evaluate_roi(img, roi_mismatch)
    assert eval_mismatch.ok is False
    assert eval_mismatch.status == "NG"
