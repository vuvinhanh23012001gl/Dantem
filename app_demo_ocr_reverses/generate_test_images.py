import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent
TEST_IMAGES_DIR = PROJECT_ROOT / "data" / "test_images"


def _load_font(size: int = 28) -> ImageFont.FreeTypeFont:
    for candidate in [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
    ]:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def create_base_industrial_label() -> np.ndarray:
    """Create a realistic industrial carton inspection label (BGR)."""
    w, h = 760, 440
    pil_img = Image.new("RGB", (w, h), (238, 240, 244))
    draw = ImageDraw.Draw(pil_img)

    # Outer border & header bar
    draw.rectangle([(16, 16), (w - 16, h - 16)], outline=(30, 41, 59), width=3)
    draw.rectangle([(16, 16), (w - 16, 86)], fill=(30, 41, 59))

    font_header = _load_font(30)
    font_body = _load_font(27)
    font_small = _load_font(24)

    draw.text(
        (36, 33),
        "INSPECTOR CARTON QA-2026",
        fill=(255, 255, 255),
        font=font_header,
    )
    draw.text(
        (36, 110),
        "MODEL: IC-9800 PRO",
        fill=(15, 23, 42),
        font=font_body,
    )
    draw.text(
        (36, 170),
        "LOT: VN20261030-A1",
        fill=(15, 23, 42),
        font=font_body,
    )
    draw.text(
        (36, 230),
        "MFG: 2026-10-30 EXP: 2028-10-30",
        fill=(15, 23, 42),
        font=font_small,
    )

    # Simulated barcode stripes
    rng = np.random.default_rng(42)
    bx = 36
    while bx < 520:
        bw = int(rng.choice([2, 3, 5, 7]))
        draw.rectangle([(bx, 285), (bx + bw, 345)], fill=(15, 23, 42))
        bx += bw + int(rng.choice([2, 4, 6]))

    draw.text(
        (36, 365),
        "MADE IN VIETNAM",
        fill=(15, 23, 42),
        font=font_body,
    )

    return cv2.cvtColor(np.array(pil_img, dtype=np.uint8), cv2.COLOR_RGB2BGR)


def create_mixed_orientation_label() -> np.ndarray:
    """Create a label where one text line is inverted 180° while others are upright 0°."""
    w, h = 760, 400
    pil_img = Image.new("RGB", (w, h), (242, 244, 247))
    draw = ImageDraw.Draw(pil_img)
    draw.rectangle([(16, 16), (w - 16, h - 16)], outline=(30, 41, 59), width=3)

    font_body = _load_font(28)
    draw.text(
        (40, 50),
        "INSPECTOR CARTON QA-2026",
        fill=(15, 23, 42),
        font=font_body,
    )
    draw.text(
        (40, 290),
        "MADE IN VIETNAM",
        fill=(15, 23, 42),
        font=font_body,
    )

    # Render an inverted 180° line in the middle
    line_img = Image.new("RGB", (520, 60), (242, 244, 247))
    line_draw = ImageDraw.Draw(line_img)
    line_draw.text(
        (10, 12),
        "LOT: VN20261030-A1",
        fill=(185, 28, 28),
        font=font_body,
    )
    line_inverted = line_img.rotate(180)
    pil_img.paste(line_inverted, (40, 165))

    return cv2.cvtColor(np.array(pil_img, dtype=np.uint8), cv2.COLOR_RGB2BGR)


def create_symmetric_edgecase_180_label() -> np.ndarray:
    """
    Create an upside-down (180°) label containing strictly symmetric/ambiguous characters
    ('80808' and 'HOXOH') to test & illustrate when OCR reads glyphs but orientation is ambiguous.
    """
    w, h = 600, 260
    pil_img = Image.new("RGB", (w, h), (245, 245, 245))
    draw = ImageDraw.Draw(pil_img)
    font_body = _load_font(34)
    draw.text((120, 55), "80808", fill=(20, 20, 20), font=font_body)
    draw.text((120, 145), "HOXOH", fill=(20, 20, 20), font=font_body)
    pil_rot = pil_img.rotate(180)
    return cv2.cvtColor(np.array(pil_rot, dtype=np.uint8), cv2.COLOR_RGB2BGR)


def rotate_slight_tilt(img: np.ndarray, angle_deg: float = -8.0) -> np.ndarray:
    """Rotate image by a slight tilt angle (e.g. 8°) with white border padding."""
    h, w = img.shape[:2]
    center = (w / 2.0, h / 2.0)
    M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    cos = abs(M[0, 0])
    sin = abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    M[0, 2] += (new_w / 2.0) - center[0]
    M[1, 2] += (new_h / 2.0) - center[1]
    return cv2.warpAffine(
        img,
        M,
        (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(238, 240, 244),
    )


def degrade_blur_noisy_lowlight(img: np.ndarray) -> np.ndarray:
    """Simulate a blurry, noisy, low-light industrial camera capture."""
    # Reduce brightness & contrast (low-light)
    dark = cv2.convertScaleAbs(img, alpha=0.42, beta=-15)
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(dark, (5, 5), sigmaX=1.3)
    # Add sensor Gaussian noise
    rng = np.random.default_rng(123)
    noise = rng.normal(0, 9.0, blurred.shape).astype(np.float32)
    noisy = np.clip(blurred.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return noisy


def main() -> None:
    TEST_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    base_label = create_base_industrial_label()
    expected_Lines = [
        "INSPECTOR CARTON QA-2026",
        "MODEL: IC-9800 PRO",
        "LOT: VN20261030-A1",
        "MFG: 2026-10-30 EXP: 2028-10-30",
        "MADE IN VIETNAM",
    ]

    dataset_manifest = []

    # 1. Normal 0°
    p1 = TEST_IMAGES_DIR / "01_normal_0deg.png"
    cv2.imwrite(str(p1), base_label)
    dataset_manifest.append(
        {
            "file": p1.name,
            "category": "Chữ đúng chiều (0°)",
            "expected_angle": 0,
            "expected_status": "NORMAL",
            "expected_result": "OK",
            "expected_keywords": ["INSPECTOR", "IC-9800", "VN20261030", "2026-10-30", "VIETNAM"],
        }
    )

    # 2. Rotated 90° CW
    p2 = TEST_IMAGES_DIR / "02_rotated_90deg.png"
    cv2.imwrite(str(p2), cv2.rotate(base_label, cv2.ROTATE_90_CLOCKWISE))
    dataset_manifest.append(
        {
            "file": p2.name,
            "category": "Chữ xoay 90° CW",
            "expected_angle": 90,
            "expected_status": "ROTATED_90",
            "expected_result": "NG",
            "expected_keywords": ["INSPECTOR", "IC-9800", "VN20261030", "2026-10-30", "VIETNAM"],
        }
    )

    # 3. Inverted 180°
    p3 = TEST_IMAGES_DIR / "03_inverted_180deg.png"
    cv2.imwrite(str(p3), cv2.rotate(base_label, cv2.ROTATE_180))
    dataset_manifest.append(
        {
            "file": p3.name,
            "category": "Chữ xoay ngược 180°",
            "expected_angle": 180,
            "expected_status": "INVERTED",
            "expected_result": "NG",
            "expected_keywords": ["INSPECTOR", "IC-9800", "VN20261030", "2026-10-30", "VIETNAM"],
        }
    )

    # 4. Rotated 270° CW
    p4 = TEST_IMAGES_DIR / "04_rotated_270deg.png"
    cv2.imwrite(str(p4), cv2.rotate(base_label, cv2.ROTATE_90_COUNTERCLOCKWISE))
    dataset_manifest.append(
        {
            "file": p4.name,
            "category": "Chữ xoay 270° CW",
            "expected_angle": 270,
            "expected_status": "ROTATED_270",
            "expected_result": "NG",
            "expected_keywords": ["INSPECTOR", "IC-9800", "VN20261030", "2026-10-30", "VIETNAM"],
        }
    )

    # 5. Horizontal Mirror
    p5 = TEST_IMAGES_DIR / "05_mirror_horizontal.png"
    cv2.imwrite(str(p5), cv2.flip(base_label, 1))
    dataset_manifest.append(
        {
            "file": p5.name,
            "category": "Chữ lật gương trái-phải (Mirror)",
            "expected_angle": 0,
            "expected_status": "MIRROR",
            "expected_result": "NG",
            "expected_keywords": ["INSPECTOR", "IC-9800", "VN20261030", "2026-10-30", "VIETNAM"],
        }
    )

    # 6. Slight Tilt (+8°)
    p6 = TEST_IMAGES_DIR / "06_tilted_8deg.png"
    cv2.imwrite(str(p6), rotate_slight_tilt(base_label, angle_deg=-8.0))
    dataset_manifest.append(
        {
            "file": p6.name,
            "category": "Chữ bị nghiêng nhẹ (+8° Skew, vẫn đúng chiều 0°)",
            "expected_angle": 0,
            "expected_status": "NORMAL",
            "expected_result": "OK",
            "expected_keywords": ["INSPECTOR", "IC-9800", "VN20261030", "2026-10-30", "VIETNAM"],
        }
    )

    # 7. Blurry, Noisy, Low-light
    p7 = TEST_IMAGES_DIR / "07_blur_noisy_lowlight.png"
    cv2.imwrite(str(p7), degrade_blur_noisy_lowlight(base_label))
    dataset_manifest.append(
        {
            "file": p7.name,
            "category": "Chữ mờ, nhiễu và thiếu sáng (0°)",
            "expected_angle": 0,
            "expected_status": "NORMAL",
            "expected_result": "OK",
            "expected_keywords": ["INSPECTOR", "IC-9800", "VN20261030", "2026-10-30", "VIETNAM"],
        }
    )

    # 8. Mixed Orientation Label (0° + 180° on same label)
    p8 = TEST_IMAGES_DIR / "08_mixed_orientation.png"
    cv2.imwrite(str(p8), create_mixed_orientation_label())
    dataset_manifest.append(
        {
            "file": p8.name,
            "category": "Tem nhiều dòng chữ ngược hướng nhau (0° + 180°)",
            "expected_angle": 0,
            "expected_status": "MIXED_ORIENTATION",
            "expected_result": "NG",
            "expected_keywords": ["INSPECTOR", "VN20261030", "VIETNAM"],
        }
    )

    # 9-13. Real Industrial Camera Label (Lenovo M7605D) in 0°, 90°, 180°, 270°, Mirror
    real_src = Path(r"C:\Disk D\Project\VIS\demo\reader_barcode\000037_M000_OK.jpg")
    if real_src.exists():
        raw_real = cv2.imread(str(real_src))
        # Crop ROI around the industrial sticker for faster & cleaner benchmarking
        h_r, w_r = raw_real.shape[:2]
        roi = raw_real[int(h_r * 0.20) : int(h_r * 0.74), int(w_r * 0.22) : int(w_r * 0.96)]
        roi_resized = cv2.resize(roi, (0, 0), fx=0.75, fy=0.75, interpolation=cv2.INTER_AREA)

        real_variants = [
            ("09_real_label_0deg.jpg", roi_resized, "Tem thực tế công nghiệp (0°)", 0, "NORMAL", "OK"),
            (
                "10_real_label_90deg.jpg",
                cv2.rotate(roi_resized, cv2.ROTATE_90_CLOCKWISE),
                "Tem thực tế công nghiệp xoay 90°",
                90,
                "ROTATED_90",
                "NG",
            ),
            (
                "11_real_label_180deg.jpg",
                cv2.rotate(roi_resized, cv2.ROTATE_180),
                "Tem thực tế công nghiệp xoay 180°",
                180,
                "INVERTED",
                "NG",
            ),
            (
                "12_real_label_270deg.jpg",
                cv2.rotate(roi_resized, cv2.ROTATE_90_COUNTERCLOCKWISE),
                "Tem thực tế công nghiệp xoay 270°",
                270,
                "ROTATED_270",
                "NG",
            ),
            (
                "13_real_label_mirror.jpg",
                cv2.flip(roi_resized, 1),
                "Tem thực tế công nghiệp lật gương (Mirror)",
                0,
                "MIRROR",
                "NG",
            ),
        ]
        for fname, img_var, cat, exp_ang, exp_st, exp_res in real_variants:
            out_p = TEST_IMAGES_DIR / fname
            cv2.imwrite(str(out_p), img_var)
            dataset_manifest.append(
                {
                    "file": fname,
                    "category": cat,
                    "expected_angle": exp_ang,
                    "expected_status": exp_st,
                    "expected_result": exp_res,
                    "expected_keywords": ["Lenovo", "M7605D", "WP04635295", "LASER"],
                }
            )

    # 14. Symmetric 180° edge case
    p14 = TEST_IMAGES_DIR / "14_edgecase_symmetric_180deg.png"
    cv2.imwrite(str(p14), create_symmetric_edgecase_180_label())
    dataset_manifest.append(
        {
            "file": p14.name,
            "category": "Edge-case ký tự đối xứng tâm 180° (80808 / HOXOH)",
            "expected_angle": 180,
            "expected_status": "INVERTED",
            "expected_result": "NG",
            "expected_keywords": ["80808", "HOXOH"],
            "is_symmetric_edgecase": True,
        }
    )

    manifest_path = TEST_IMAGES_DIR / "ground_truth.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(dataset_manifest, f, ensure_ascii=False, indent=4)

    print(f"Generated {len(dataset_manifest)} test images in {TEST_IMAGES_DIR}")


if __name__ == "__main__":
    main()
