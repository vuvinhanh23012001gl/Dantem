import json
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

from app.core.geometry import save_image_unicode
from app.services.ocr_service import OCRService
from app.services.visualization_service import VisualizationService
from config import load_settings


def evaluate_all() -> None:
    test_dir = PROJECT_ROOT / "data" / "test_images"
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = test_dir / "ground_truth.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Ground truth manifest not found at {manifest_path}. Run generate_test_images.py first."
        )

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    ocr_service = OCRService(config=load_settings())

    report_rows = []
    standard_cases = [m for m in manifest if not m.get("is_symmetric_edgecase", False)]
    edge_cases = [m for m in manifest if m.get("is_symmetric_edgecase", False)]

    correct_status_std = 0
    correct_judgement_std = 0
    total_keyword_hits_std = 0
    total_keywords_std = 0

    for item in manifest:
        img_path = test_dir / item["file"]
        res, raw_bgr = ocr_service.inspect_image(img_path)
        compact = res.to_compact_dict()

        # Save individual JSON and annotated image
        stem = img_path.stem
        with open(output_dir / f"{stem}_result.json", "w", encoding="utf-8") as jf:
            json.dump(compact, jf, ensure_ascii=False, indent=4)

        if raw_bgr is not None:
            vis_bgr = VisualizationService.draw_inspection_result(raw_bgr, res)
            save_image_unicode(output_dir / f"{stem}_annotated.png", vis_bgr)

        joined_text = " | ".join(t.text for t in res.texts)
        joined_upper = joined_text.upper()
        kw_list = item.get("expected_keywords", [])
        kw_hits = sum(1 for kw in kw_list if kw.upper() in joined_upper)
        kw_acc = (kw_hits / len(kw_list) * 100.0) if kw_list else 100.0

        status_match = res.orientation.status == item["expected_status"]
        judgement_match = res.result == item["expected_result"]

        if not item.get("is_symmetric_edgecase", False):
            if status_match:
                correct_status_std += 1
            if judgement_match:
                correct_judgement_std += 1
            total_keyword_hits_std += kw_hits
            total_keywords_std += len(kw_list)

        row = {
            "file": item["file"],
            "category": item["category"],
            "expected_angle": item["expected_angle"],
            "predicted_angle": res.orientation.angle,
            "expected_status": item["expected_status"],
            "predicted_status": res.orientation.status,
            "status_correct": status_match,
            "expected_result": item["expected_result"],
            "predicted_result": res.result,
            "judgement_correct": judgement_match,
            "skew_angle": res.orientation.skew_angle,
            "orientation_confidence": round(res.orientation.confidence, 4),
            "keyword_hit_rate": f"{kw_hits}/{len(kw_list)} ({kw_acc:.1f}%)",
            "total_lines": res.total_lines,
            "processing_time_ms": round(res.processing_time_ms, 1),
            "recognized_texts": [t.text for t in res.texts],
            "is_symmetric_edgecase": bool(item.get("is_symmetric_edgecase", False)),
        }
        report_rows.append(row)
        print(
            f"[{item['file']}] Exp={item['expected_status']}({item['expected_result']}) | "
            f"Pred={res.orientation.status}({res.result}) Angle={res.orientation.angle}° "
            f"Skew={res.orientation.skew_angle:+.1f}° | KW={kw_hits}/{len(kw_list)} | "
            f"Time={res.processing_time_ms:.1f}ms"
        )

    n_std = max(len(standard_cases), 1)
    summary = {
        "total_images_tested": len(manifest),
        "standard_industrial_cases": len(standard_cases),
        "symmetric_edge_cases": len(edge_cases),
        "standard_orientation_accuracy_pct": round(
            correct_status_std / n_std * 100.0, 2
        ),
        "standard_ok_ng_judgement_accuracy_pct": round(
            correct_judgement_std / n_std * 100.0, 2
        ),
        "standard_content_keyword_recall_pct": round(
            total_keyword_hits_std / max(total_keywords_std, 1) * 100.0, 2
        ),
        "details": report_rows,
    }

    report_path = output_dir / "benchmark_evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)

    print("\n================ BENCHMARK SUMMARY ================")
    print(
        f"Standard Cases ({len(standard_cases)} images): "
        f"Orientation Accuracy = {summary['standard_orientation_accuracy_pct']}%, "
        f"OK/NG Accuracy = {summary['standard_ok_ng_judgement_accuracy_pct']}%, "
        f"Content Keyword Recall = {summary['standard_content_keyword_recall_pct']}%"
    )
    print(f"Saved full report to {report_path}")


if __name__ == "__main__":
    evaluate_all()
