import math
from typing import Any
import cv2
import numpy as np
from app.core import Result, ErrorCode


class ColorService:
    """Dịch vụ trích xuất và đo lường sai lệch màu sắc (RGB, CIE Lab, Delta E2000)."""

    @staticmethod
    def bgr_to_lab_chuan(bgr_pixel: np.ndarray | list | tuple) -> tuple[float, float, float]:
        """Chuyển đổi 1 màu BGR (thang 0-255) sang không gian CIE L*a*b* chuẩn.

        Sử dụng chuẩn float32 trong khoảng [0, 1] trước khi chuyển đổi cvtColor
        để trả về đúng thang chuẩn:
          - L*: 0 .. 100
          - a*: khoảng -128 .. 127
          - b*: khoảng -128 .. 127
        """
        bgr = np.array([[bgr_pixel]], dtype=np.float32) / 255.0
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        L, a, b = lab[0, 0]
        return float(L), float(a), float(b)

    @staticmethod
    def delta_e76(lab1: tuple[float, float, float], lab2: tuple[float, float, float]) -> float:
        """Tính khoảng cách màu Euclid CIE76 trong không gian Lab."""
        return float(math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(lab1, lab2))))

    @staticmethod
    def delta_e2000(lab1: tuple[float, float, float], lab2: tuple[float, float, float]) -> float:
        """Tính khoảng cách sai lệch màu theo tiêu chuẩn quốc tế CIE2000 (CIEDE2000).

        Cài đặt theo công thức Sharma et al., có trọng số thích nghi theo L, C, H.
        """
        L1, a1, b1 = lab1
        L2, a2, b2 = lab2

        kL = kC = kH = 1.0

        C1 = math.hypot(a1, b1)
        C2 = math.hypot(a2, b2)
        Cbar = (C1 + C2) / 2.0

        G = 0.5 * (1.0 - math.sqrt((Cbar ** 7) / (Cbar ** 7 + 25.0 ** 7)))
        a1p = (1.0 + G) * a1
        a2p = (1.0 + G) * a2

        C1p = math.hypot(a1p, b1)
        C2p = math.hypot(a2p, b2)

        def hue_angle(ap: float, b: float) -> float:
            if ap == 0 and b == 0:
                return 0.0
            h = math.degrees(math.atan2(b, ap))
            return h + 360.0 if h < 0 else h

        h1p = hue_angle(a1p, b1)
        h2p = hue_angle(a2p, b2)

        dLp = L2 - L1
        dCp = C2p - C1p

        if C1p * C2p == 0:
            dhp = 0.0
        else:
            diff = h2p - h1p
            if diff > 180.0:
                diff -= 360.0
            elif diff < -180.0:
                diff += 360.0
            dhp = diff

        dHp = 2.0 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2.0)

        Lbar_p = (L1 + L2) / 2.0
        Cbar_p = (C1p + C2p) / 2.0

        if C1p * C2p == 0:
            Hbar_p = h1p + h2p
        else:
            s = h1p + h2p
            diff = abs(h1p - h2p)
            if diff > 180.0:
                Hbar_p = (s + 360.0) / 2.0 if s < 360.0 else (s - 360.0) / 2.0
            else:
                Hbar_p = s / 2.0

        T = (
            1.0
            - 0.17 * math.cos(math.radians(Hbar_p - 30.0))
            + 0.24 * math.cos(math.radians(2.0 * Hbar_p))
            + 0.32 * math.cos(math.radians(3.0 * Hbar_p + 6.0))
            - 0.20 * math.cos(math.radians(4.0 * Hbar_p - 63.0))
        )

        d_theta = 30.0 * math.exp(-(((Hbar_p - 275.0) / 25.0) ** 2))
        Rc = 2.0 * math.sqrt((Cbar_p ** 7) / (Cbar_p ** 7 + 25.0 ** 7))
        Sl = 1.0 + (0.015 * (Lbar_p - 50.0) ** 2) / math.sqrt(20.0 + (Lbar_p - 50.0) ** 2)
        Sc = 1.0 + 0.045 * Cbar_p
        Sh = 1.0 + 0.015 * Cbar_p * T
        Rt = -math.sin(math.radians(2.0 * d_theta)) * Rc

        dE = math.sqrt(
            (dLp / (kL * Sl)) ** 2
            + (dCp / (kC * Sc)) ** 2
            + (dHp / (kH * Sh)) ** 2
            + Rt * (dCp / (kC * Sc)) * (dHp / (kH * Sh))
        )
        return float(dE)

    @classmethod
    def compute_color_similarity(cls, delta_e: float, max_delta_e: float = 5.0) -> float:
        """Tính toán phần trăm tương đồng màu sắc trực quan (0.0% đến 100.0%).

        Khi delta_e = 0 -> 100%. Khi delta_e = max_delta_e -> đạt cận ngưỡng chấp nhận (~75%).
        Vượt quá 2 lần max_delta_e -> tiệm cận 0%.
        """
        if delta_e <= 0.0:
            return 100.0
        ref_span = max(float(max_delta_e) * 2.5, 10.0)
        sim = 100.0 * (1.0 - (delta_e / ref_span))
        return float(max(0.0, min(100.0, round(sim, 2))))

    def clip_roi(
        self, w_img: int, h_img: int, x1: float, y1: float, x2: float, y2: float
    ) -> tuple[int, int, int, int]:
        """Cắt giới hạn tọa độ khung chữ nhật nằm trọn trong kích thước ảnh."""
        left = max(0, min(int(round(min(x1, x2))), w_img))
        top = max(0, min(int(round(min(y1, y2))), h_img))
        right = max(0, min(int(round(max(x1, x2))), w_img))
        bottom = max(0, min(int(round(max(y1, y2))), h_img))
        return left, top, right, bottom

    def inspect_color_roi(
        self,
        image: np.ndarray,
        roi_box: dict[str, Any],
        width_canvas: int | None = None,
    ) -> dict[str, Any]:
        """Đo màu trung bình của vùng ROI và so sánh với màu chuẩn nếu có."""
        h_img, w_img = image.shape[:2]
        scale = (w_img / float(width_canvas)) if (width_canvas and width_canvas > 0) else 1.0

        x1 = float(roi_box.get("x1", roi_box.get("xStart", 0))) * scale
        y1 = float(roi_box.get("y1", roi_box.get("yStart", 0))) * scale
        x2 = float(roi_box.get("x2", roi_box.get("xEnd", 0))) * scale
        y2 = float(roi_box.get("y2", roi_box.get("yEnd", 0))) * scale

        rx1, ry1, rx2, ry2 = self.clip_roi(w_img, h_img, x1, y1, x2, y2)
        box_id = roi_box.get("id", 0)
        box_name = str(roi_box.get("name") or f"Màu {box_id + 1}").strip()
        max_delta_e = float(roi_box.get("max_delta_e", 5.0))

        if rx2 <= rx1 or ry2 <= ry1:
            return {
                "id": box_id,
                "name": box_name,
                "status": "NG",
                "error": "Khung ROI không hợp lệ hoặc nằm ngoài ảnh",
                "roi": [rx1, ry1, rx2, ry2],
            }

        crop = image[ry1:ry2, rx1:rx2]
        b, g, r = cv2.mean(crop)[:3]
        measured_bgr = np.array([b, g, r], dtype=np.float32)
        R, G, B = int(round(r)), int(round(g)), int(round(b))
        L, a_val, b_val = self.bgr_to_lab_chuan(measured_bgr)

        # Màu chuẩn cấu hình trước (nếu có)
        ref_rgb = roi_box.get("ref_rgb")
        if ref_rgb and len(ref_rgb) == 3:
            rr, rg, rb = [int(round(float(c))) for c in ref_rgb]
            ref_bgr = np.array([rb, rg, rr], dtype=np.float32)
            Lr, ar, br = self.bgr_to_lab_chuan(ref_bgr)
            de76 = self.delta_e76((L, a_val, b_val), (Lr, ar, br))
            de2000 = self.delta_e2000((L, a_val, b_val), (Lr, ar, br))
            sim = self.compute_color_similarity(de2000, max_delta_e)
            is_ok = bool(de2000 <= max_delta_e)
            status = "OK" if is_ok else "NG"
        else:
            # Chưa cấu hình màu chuẩn -> dùng chính màu đo được
            rr, rg, rb = R, G, B
            Lr, ar, br = L, a_val, b_val
            de76 = 0.0
            de2000 = 0.0
            sim = 100.0
            status = "OK"

        return {
            "id": box_id,
            "name": box_name,
            "status": status,
            "roi": [rx1, ry1, rx2, ry2],
            "measured_rgb": [R, G, B],
            "measured_lab": [round(L, 2), round(a_val, 2), round(b_val, 2)],
            "ref_rgb": [rr, rg, rb],
            "ref_lab": [round(Lr, 2), round(ar, 2), round(br, 2)],
            "delta_e": round(de2000, 2),
            "delta_e00": round(de2000, 2),
            "delta_e76": round(de76, 2),
            "similarity": sim,
            "similarity_percent": sim,
            "max_delta_e": max_delta_e,
        }

    def inspect_color_boxes(
        self,
        image: np.ndarray,
        boxes: list[dict[str, Any]],
        width_canvas: int | None = None,
    ) -> Result:
        """Đo và phán định màu sắc trên toàn bộ danh sách các khung ROI."""
        if not isinstance(image, np.ndarray) or image.size == 0:
            return Result.Fail(ErrorCode.IMAGE_NOT_FOUND)
        if not isinstance(boxes, list) or not boxes:
            return Result.Fail(ErrorCode.INVALID_INPUT)

        results = [
            self.inspect_color_roi(image, b, width_canvas=width_canvas)
            for b in boxes
            if isinstance(b, dict)
        ]
        h_img, w_img = image.shape[:2]
        return Result.Ok({
            "boxes": results,
            "image_width": w_img,
            "image_height": h_img,
            "overall": all(r.get("status") == "OK" for r in results),
        })


# Module-level aliases cho thuận tiện import
bgr_to_lab_chuan = ColorService.bgr_to_lab_chuan
delta_e76 = ColorService.delta_e76
delta_e2000 = ColorService.delta_e2000
compute_color_similarity = ColorService.compute_color_similarity
