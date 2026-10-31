import argparse
import json
import os
from pathlib import Path
import sys

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

from app.core.constants import SUPPORTED_IMAGE_EXTENSIONS
from app.core.geometry import save_image_unicode
from app.core.logger import get_logger
from app.services.ocr_service import OCRService
from app.services.visualization_service import VisualizationService
from config import load_settings

logger = get_logger("main")


def run_cli_inspection(
    ocr_service: OCRService,
    target_path: Path,
    output_dir: Path,
) -> int:
    """Run headless CLI OCR & Orientation inspection on a single image or directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if target_path.is_dir():
        images = sorted(
            [
                p
                for p in target_path.iterdir()
                if p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            ]
        )
    elif target_path.is_file():
        images = [target_path]
    else:
        logger.error("Path does not exist: %s", target_path)
        return 1

    if not images:
        logger.warning("No supported images found in %s", target_path)
        return 1

    all_summaries = []
    for img_path in images:
        logger.info("Inspecting image: %s", img_path.name)
        res, raw_bgr = ocr_service.inspect_image(img_path)
        compact = res.to_compact_dict()
        all_summaries.append(compact)

        print("\n" + "=" * 72)
        print(json.dumps(compact, ensure_ascii=False, indent=4))

        stem = img_path.stem
        json_out = output_dir / f"{stem}_result.json"
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(compact, f, ensure_ascii=False, indent=4)

        if raw_bgr is not None:
            vis_bgr = VisualizationService.draw_inspection_result(raw_bgr, res)
            img_out = output_dir / f"{stem}_annotated.png"
            save_image_unicode(img_out, vis_bgr)

    if len(all_summaries) > 1:
        summary_file = output_dir / "batch_inspection_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(all_summaries, f, ensure_ascii=False, indent=4)
        logger.info("Saved batch summary to %s", summary_file)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Industrial Label OCR & Orientation Inspector (0°, 90°, 180°, 270°, Mirror)"
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Path to an image file to inspect",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Path to a directory of images for batch inspection",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "output"),
        help="Directory to save JSON and annotated image outputs",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run in CLI headless mode without opening the PySide6 GUI window",
    )
    args = parser.parse_args()

    settings = load_settings()
    ocr_service = OCRService(config=settings)

    if args.no_gui or args.dir:
        target = Path(args.dir if args.dir else (args.image or (PROJECT_ROOT / "data" / "test_images")))
        return run_cli_inspection(ocr_service, target, Path(args.output))

    # Launch PySide6 Desktop GUI
    from PySide6.QtWidgets import QApplication
    from app.ui.main_window import MainWindow

    qt_app = QApplication(sys.argv)
    window = MainWindow(ocr_service=ocr_service)
    window.show()

    if args.image:
        img_p = Path(args.image)
        if img_p.exists():
            window.load_and_inspect(img_p)

    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
