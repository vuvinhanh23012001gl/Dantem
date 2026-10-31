import time
import logging
from typing import Any, Dict, List, Optional
import cv2
import numpy as np
import zxingcpp

logger = logging.getLogger(__name__)


class BarcodeQRService:
    """Dịch vụ nhận diện mã vạch Barcode 1D và mã QR 2D sử dụng thư viện ZXing-C++."""

    BARCODE_FORMATS = [zxingcpp.BarcodeFormat.AllLinear]
    QR_FORMATS = [
        zxingcpp.BarcodeFormat.QRCode,
        zxingcpp.BarcodeFormat.MicroQRCode,
        zxingcpp.BarcodeFormat.RMQRCode,
    ]

    def __init__(self) -> None:
        pass

    def _crop_roi(
        self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int
    ) -> Optional[np.ndarray]:
        """Cắt ảnh an toàn theo tọa độ ROI."""
        if not isinstance(image, np.ndarray) or image.size == 0:
            return None
        height, width = image.shape[:2]
        x1_clamped = max(0, min(x1, width - 1))
        y1_clamped = max(0, min(y1, height - 1))
        x2_clamped = max(x1_clamped + 1, min(x2, width))
        y2_clamped = max(y1_clamped + 1, min(y2, height))

        crop = image[y1_clamped:y2_clamped, x1_clamped:x2_clamped]
        if crop.size == 0:
            return None
        return crop

    def _decode_with_fallback(
        self, crop: np.ndarray, formats: zxingcpp.BarcodeFormat
    ) -> Optional[zxingcpp.Barcode]:
        """Thử đọc mã trực tiếp trên ảnh gốc, nếu không thành công thì thử tăng cường độ tương phản."""
        # Lần 1: Đọc trực tiếp
        try:
            results = zxingcpp.read_barcodes(crop, formats=formats)
            if results:
                return results[0]
        except Exception as e:
            logger.debug(f"ZXing decode trực tiếp lỗi: {e}")

        # Lần 2: Chuyển xám và cân bằng tương phản (CLAHE)
        try:
            gray = (
                cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                if len(crop.shape) == 3
                else crop
            )
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            results = zxingcpp.read_barcodes(enhanced, formats=formats)
            if results:
                return results[0]
        except Exception as e:
            logger.debug(f"ZXing decode CLAHE lỗi: {e}")

        # Lần 3: Nhị phân Otsu
        try:
            gray = (
                cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                if len(crop.shape) == 3
                else crop
            )
            _, thresh = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            results = zxingcpp.read_barcodes(thresh, formats=formats)
            if results:
                return results[0]
        except Exception as e:
            logger.debug(f"ZXing decode Otsu lỗi: {e}")

        return None

    def scan_barcode_roi(
        self, image: np.ndarray, roi: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Nhận diện mã vạch Barcode 1D trong vùng ROI."""
        start_time = time.perf_counter()
        x1 = int(roi.get("x1", roi.get("xStart", 0)))
        y1 = int(roi.get("y1", roi.get("yStart", 0)))
        x2 = int(roi.get("x2", roi.get("xEnd", 0)))
        y2 = int(roi.get("y2", roi.get("yEnd", 0)))

        crop = self._crop_roi(image, x1, y1, x2, y2)
        if crop is None:
            return {
                "success": False,
                "text": "",
                "format": "",
                "processing_time_ms": round(
                    (time.perf_counter() - start_time) * 1000, 2
                ),
                "error_message": "Vùng ROI không hợp lệ hoặc nằm ngoài phạm vi ảnh",
            }

        barcode = self._decode_with_fallback(crop, self.BARCODE_FORMATS)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if barcode is not None:
            return {
                "success": True,
                "text": str(barcode.text).strip(),
                "format": str(barcode.format),
                "position": str(barcode.position),
                "processing_time_ms": elapsed_ms,
                "error_message": None,
            }
        else:
            return {
                "success": False,
                "text": "",
                "format": "",
                "processing_time_ms": elapsed_ms,
                "error_message": "Không tìm thấy mã barcode trong vùng chỉ định",
            }

    def scan_qr_roi(
        self, image: np.ndarray, roi: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Nhận diện mã QR 2D trong vùng ROI."""
        start_time = time.perf_counter()
        x1 = int(roi.get("x1", roi.get("xStart", 0)))
        y1 = int(roi.get("y1", roi.get("yStart", 0)))
        x2 = int(roi.get("x2", roi.get("xEnd", 0)))
        y2 = int(roi.get("y2", roi.get("yEnd", 0)))

        crop = self._crop_roi(image, x1, y1, x2, y2)
        if crop is None:
            return {
                "success": False,
                "text": "",
                "format": "",
                "processing_time_ms": round(
                    (time.perf_counter() - start_time) * 1000, 2
                ),
                "error_message": "Vùng ROI không hợp lệ hoặc nằm ngoài phạm vi ảnh",
            }

        qr = self._decode_with_fallback(crop, self.QR_FORMATS)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        if qr is not None:
            return {
                "success": True,
                "text": str(qr.text).strip(),
                "format": str(qr.format),
                "position": str(qr.position),
                "processing_time_ms": elapsed_ms,
                "error_message": None,
            }
        else:
            return {
                "success": False,
                "text": "",
                "format": "",
                "processing_time_ms": elapsed_ms,
                "error_message": "Không tìm thấy mã QR trong vùng chỉ định",
            }
