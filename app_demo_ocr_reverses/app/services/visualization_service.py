import os
from typing import Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.core.constants import InspectionJudgement, OrientationStatus
from app.schemas.ocr_schema import OCRInspectionResult


STATUS_COLORS_RGB = {
    OrientationStatus.NORMAL.value: (22, 163, 74),       # Green (0° Normal)
    OrientationStatus.ROTATED_90.value: (234, 88, 12),   # Orange (90° CW)
    OrientationStatus.INVERTED.value: (220, 38, 38),     # Red (180° Inverted)
    OrientationStatus.ROTATED_270.value: (217, 119, 6),  # Amber/Orange (270° CW)
    OrientationStatus.MIRROR.value: (147, 51, 234),      # Purple (Mirror)
    OrientationStatus.MIXED.value: (220, 38, 38),        # Red (Mixed)
    OrientationStatus.UNKNOWN.value: (107, 114, 128),    # Gray
}


class VisualizationService:
    """
    Renders rich OCR & Orientation inspection overlays directly on a copy of the
    ORIGINAL image (preserving original orientation and bounding box positions).
    Supports Multilingual Unicode text (Vietnamese, English, Chinese) via Pillow.
    """

    @staticmethod
    def _has_cjk(text: str) -> bool:
        return any("\u4e00" <= ch <= "\u9fff" for ch in text)

    @classmethod
    def _load_font(cls, size: int = 18, prefer_cjk: bool = False) -> ImageFont.FreeTypeFont:
        """
        Load a system font supporting Vietnamese/Latin (segoeui/arial/tahoma)
        or CJK (msyh/simsun) when Chinese/Japanese characters are present.
        """
        if prefer_cjk:
            candidates = [
                r"C:\Windows\Fonts\msyh.ttc",
                r"C:\Windows\Fonts\simsun.ttc",
                r"C:\Windows\Fonts\arial.ttf",
            ]
        else:
            candidates = [
                r"C:\Windows\Fonts\segoeui.ttf",
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\tahoma.ttf",
                r"C:\Windows\Fonts\msyh.ttc",
            ]
        for font_path in candidates:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size=size)
                except Exception:
                    continue
        return ImageFont.load_default()

    @classmethod
    def draw_inspection_result(
        cls,
        original_bgr: np.ndarray,
        inspection: OCRInspectionResult,
    ) -> np.ndarray:
        """
        Draw oriented polygons, bounding boxes, line IDs, orientation angles,
        confidences, and a summary header bar onto the original image.
        """
        img_h, img_w = original_bgr.shape[:2]
        banner_h = max(68, int(img_h * 0.10))
        canvas_h = img_h + banner_h

        rgb_orig = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)
        pil_canvas = Image.new("RGB", (img_w, canvas_h), (24, 24, 36))
        pil_canvas.paste(Image.fromarray(rgb_orig), (0, banner_h))

        draw = ImageDraw.Draw(pil_canvas, "RGBA")

        font_scale = max(13, min(24, int(min(img_w, img_h) / 34)))
        font_banner = cls._load_font(size=max(16, int(font_scale * 1.15)), prefer_cjk=False)
        font_sub = cls._load_font(size=max(13, int(font_scale * 0.90)), prefer_cjk=False)
        font_box_latin = cls._load_font(size=max(12, int(font_scale * 0.85)), prefer_cjk=False)
        font_box_cjk = cls._load_font(size=max(12, int(font_scale * 0.85)), prefer_cjk=True)

        # Draw top header banner
        is_ok = inspection.result == InspectionJudgement.OK.value
        header_bg = (21, 128, 61, 255) if is_ok else (185, 28, 28, 255)
        draw.rectangle([(0, 0), (img_w, banner_h)], fill=header_bg)

        ori = inspection.orientation
        mirror_tag = " | MIRROR: YES" if ori.is_mirrored else ""
        tilt_tag = f" | Skew: {ori.skew_angle:+.1f}°" if abs(ori.skew_angle) > 0.5 else ""
        title_line = (
            f"[{inspection.result}] Status: {ori.status} | "
            f"Angle: {ori.angle}°{mirror_tag}{tilt_tag} | "
            f"Conf: {ori.confidence:.2f} | Lines: {inspection.total_lines}"
        )
        draw.text((14, 8), title_line, fill=(255, 255, 255, 255), font=font_banner)
        draw.text(
            (14, int(banner_h * 0.52)),
            inspection.reason,
            fill=(240, 249, 255, 255),
            font=font_sub,
        )

        # Draw each text line polygon and label in original image coordinates
        for line in inspection.texts:
            rgb_color = STATUS_COLORS_RGB.get(
                line.orientation_status, (59, 130, 246)
            )
            fill_rgba = (*rgb_color, 45)
            outline_rgba = (*rgb_color, 240)

            if line.polygon and len(line.polygon) == 4:
                poly_pts: list[Tuple[int, int]] = [
                    (int(p[0]), int(p[1]) + banner_h) for p in line.polygon
                ]
                draw.polygon(poly_pts, fill=fill_rgba, outline=outline_rgba, width=3)
            else:
                x1, y1, x2, y2 = line.bbox
                draw.rectangle(
                    [(x1, y1 + banner_h), (x2, y2 + banner_h)],
                    fill=fill_rgba,
                    outline=outline_rgba,
                    width=3,
                )

            x1, y1, x2, y2 = line.bbox
            tag_angle = "MIRROR" if line.is_mirrored else f"{line.angle}°"
            short_txt = (
                line.text if len(line.text) <= 22 else line.text[:20] + "…"
            )
            label_str = f"#{line.line_id + 1} [{tag_angle} | {line.confidence:.2f}] {short_txt}"
            box_font = font_box_cjk if cls._has_cjk(short_txt) else font_box_latin

            bbox_text = draw.textbbox((0, 0), label_str, font=box_font)
            tw = bbox_text[2] - bbox_text[0] + 10
            th = bbox_text[3] - bbox_text[1] + 6

            tx = max(4, min(x1, img_w - tw - 4))
            ty = y1 + banner_h - th - 2
            if ty < banner_h + 2:
                ty = min(y2 + banner_h + 2, canvas_h - th - 2)

            draw.rectangle(
                [(tx, ty), (tx + tw, ty + th)],
                fill=(*rgb_color, 225),
            )
            draw.text(
                (tx + 5, ty + 2),
                label_str,
                fill=(255, 255, 255, 255),
                font=box_font,
            )

        out_rgb = np.array(pil_canvas, dtype=np.uint8)
        return cv2.cvtColor(out_rgb, cv2.COLOR_RGB2BGR)
