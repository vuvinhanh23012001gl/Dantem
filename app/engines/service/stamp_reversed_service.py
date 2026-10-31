import math
from typing import Any, Optional
import cv2
import numpy as np

from app.engines.model_AI.model_yolo_obb import ModelYoloOBB
from app.engines.ocr_text_service import OCRTextService


class StampReversedService:
    """
    Dịch vụ kiểm tra hướng tem và hướng chữ in trên tem (Stamp Reversed Inspection).
    Kết hợp giữa:
    1. YOLO OBB (ModelYoloOBB): Ước tính góc xoay và biên dạng hình học của tem.
    2. PaddleOCR (OCRTextService): Nhận diện chữ và phân loại hướng dòng chữ (0° vs 180°).
    """

    def __init__(
        self,
        yolo_obb: Optional[ModelYoloOBB] = None,
        ocr_service: Optional[OCRTextService] = None,
    ) -> None:
        self.yolo_obb = yolo_obb
        self.ocr_service = ocr_service or OCRTextService()

    @staticmethod
    def _crop_roi(image: np.ndarray, box: dict[str, Any]) -> tuple[np.ndarray, int, int]:
        """Cắt ảnh ROI theo tọa độ khung xStart, yStart, xEnd, yEnd (hoặc x1, y1, x2, y2)."""
        height, width = image.shape[:2]
        x1 = int(round(box.get("xStart", box.get("x1", 0))))
        y1 = int(round(box.get("yStart", box.get("y1", 0))))
        x2 = int(round(box.get("xEnd", box.get("x2", 0))))
        y2 = int(round(box.get("yEnd", box.get("y2", 0))))

        x1_clamped = max(0, min(x1, width - 1))
        y1_clamped = max(0, min(y1, height - 1))
        x2_clamped = max(x1_clamped + 1, min(x2, width))
        y2_clamped = max(y1_clamped + 1, min(y2, height))

        crop = image[y1_clamped:y2_clamped, x1_clamped:x2_clamped].copy()
        return crop, x1_clamped, y1_clamped

    def inspect_single_box(
        self,
        image: np.ndarray,
        box: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Kiểm tra hướng in tem trên một khung hình chữ nhật cụ thể.
        """
        box_id = box.get("id", 0)
        box_name = box.get("name") or f"Tem ngược {int(box_id) + 1}"
        max_deg = float(box.get("max_deg", 15.0))  # Dung sai góc xoay cho phép (độ)

        crop, roi_x, roi_y = self._crop_roi(image, box)
        if crop.size == 0 or crop.shape[0] < 5 or crop.shape[1] < 5:
            return {
                "id": box_id,
                "name": box_name,
                "status": "UNKNOWN",
                "error_code": "INVALID_ROI",
                "message": "Vùng ROI không hợp lệ hoặc quá nhỏ.",
                "text_angle": 0,
                "obb_angle": 0.0,
                "text_preview": "",
                "confidence": 0.0,
                "is_reversed": False,
            }

        # 1. Chạy OCR phân loại hướng dòng chữ (Textline Orientation)
        ocr_result = self.ocr_service.inspect_image(crop)
        lines = ocr_result.get("lines", [])
        has_text = bool(ocr_result.get("success")) and len(lines) > 0

        text_preview = ""
        text_angle = 0
        text_confidence = 0.0

        if has_text:
            text_preview = lines[0].get("text", "")
            text_confidence = float(lines[0].get("confidence", 0.0))
            # Lấy góc hướng chữ được bầu chọn nhiều nhất từ các dòng
            angles = [int(line.get("angle", 0)) for line in lines]
            # Chuẩn hóa về [0, 90, 180, 270]
            text_angle = max(set(angles), key=angles.count) if angles else 0

        # 2. Chạy YOLO OBB ước lượng hướng hình học của tem
        obb_angle = 0.0
        obb_detected = False
        obb_confidence = 0.0
        obb_box_canvas = None

        if self.yolo_obb is not None:
            try:
                obb_objects = self.yolo_obb.predict(crop)
                # Lọc nhãn class_name 'stamp' hoặc class_id == 1
                stamp_obbs = [
                    obj for obj in obb_objects
                    if str(obj.get("class_name", "")).lower() == "stamp" or obj.get("class_id") == 1
                ]
                if stamp_obbs:
                    # Lấy tem có độ tin cậy cao nhất
                    best_stamp = max(stamp_obbs, key=lambda x: float(x.get("confidence", 0.0)))
                    obb_angle = float(best_stamp.get("angle_deg", 0.0))
                    obb_confidence = float(best_stamp.get("confidence", 0.0))
                    obb_detected = True

                    # Chuyển đổi tọa độ polygon OBB sang tọa độ ảnh gốc để vẽ
                    poly = best_stamp.get("polygon")
                    if poly is not None:
                        obb_box_canvas = [
                            [float(p[0]) + roi_x, float(p[1]) + roi_y] for p in poly
                        ]
            except Exception as e:
                print(f"[StampReversedService] Lỗi chạy YOLO OBB: {e}")

        # 3. Phán định đối chiếu:
        # Bảng logic chuẩn:
        # - Nếu không phát hiện chữ:
        #     - Nếu OBB tem xoay quá ngưỡng -> NG LABEL_ROTATED
        #     - Ngược lại -> UNKNOWN (TEXT_NOT_DETECTED)
        # - Nếu có chữ:
        #     - Hướng chữ = 180° -> NG TEXT_REVERSED (Tem in ngược)
        #     - Hướng chữ = 90° hoặc 270° -> NG TEXT_ROTATED (Tem bị xoay ngang)
        #     - Hướng chữ = 0°:
        #         - Kiểm tra góc nghiêng hình học tem (nếu có OBB và độ lệch > max_deg) -> NG LABEL_ROTATED
        #         - Ngược lại -> OK (Tem đúng chiều chuẩn)

        status = "OK"
        error_code = "NONE"
        message = "Tem in đúng chiều chuẩn (0°)."

        if not has_text:
            if obb_detected and abs(obb_angle) > max_deg:
                status = "NG"
                error_code = "LABEL_ROTATED"
                message = f"Tem bị lệch góc hình học ({obb_angle:.1f}° > ±{max_deg}°), không nhận diện được chữ."
            else:
                status = "UNKNOWN"
                error_code = "TEXT_NOT_DETECTED"
                message = "Không phát hiện được nội dung chữ trên tem để xác định chiều in."
        else:
            if text_angle == 180:
                status = "NG"
                error_code = "TEXT_REVERSED"
                message = f"Tem bị in lộn ngược 180° ('{text_preview}')."
            elif text_angle in (90, 270):
                status = "NG"
                error_code = "TEXT_ROTATED"
                message = f"Tem bị xoay {text_angle}° ('{text_preview}')."
            else:
                # text_angle == 0
                if obb_detected and abs(obb_angle) > max_deg:
                    status = "NG"
                    error_code = "LABEL_ROTATED"
                    message = f"Chữ đúng chiều (0°) nhưng tem bị dán lệch góc ({obb_angle:.1f}° > ±{max_deg}°)."
                else:
                    status = "OK"
                    error_code = "NONE"
                    message = f"Tem in thuận đúng chiều 0° ('{text_preview}')."

        return {
            "id": box_id,
            "name": box_name,
            "status": status,
            "error_code": error_code,
            "message": message,
            "text_angle": text_angle,
            "obb_angle": round(obb_angle, 1),
            "obb_detected": obb_detected,
            "text_preview": text_preview,
            "confidence": round(text_confidence or obb_confidence, 2),
            "is_reversed": (text_angle == 180),
            "obb_polygon": obb_box_canvas,
        }

    def inspect_boxes(
        self,
        image: np.ndarray,
        boxes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Kiểm tra toàn bộ danh sách các khung ROI cấu hình."""
        results = [self.inspect_single_box(image, box) for box in boxes]
        all_ok = all(r["status"] == "OK" for r in results) if results else True
        return {
            "all_ok": all_ok,
            "boxes": results,
            "count_total": len(results),
            "count_ok": sum(1 for r in results if r["status"] == "OK"),
            "count_ng": sum(1 for r in results if r["status"] == "NG"),
            "count_unknown": sum(1 for r in results if r["status"] == "UNKNOWN"),
        }
