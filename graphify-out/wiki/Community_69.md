# Community 69

> 32 nodes

## Key Concepts

- **OCRTextDetector** (20 connections) — `app/judger/ocr_text_detector.py`
- **.evaluate_roi()** (10 connections) — `app/judger/ocr_text_detector.py`
- **OCRTextService** (9 connections) — `app/engines/ocr_text_service.py`
- **test_ocr_text_detector.py** (9 connections) — `app/tests/judger/test_ocr_text_detector.py`
- **FakeOCRService** (8 connections) — `app/tests/judger/test_ocr_text_detector.py`
- **TestOCRTextDetector** (7 connections) — `app/tests/judger/test_ocr_text_detector.py`
- **.inspect_image()** (6 connections) — `app/engines/ocr_text_service.py`
- **ocr_result()** (6 connections) — `app/tests/judger/test_ocr_text_detector.py`
- **.test_stage2_runs_each_configured_roi_and_requires_every_match()** (6 connections) — `app/tests/judger/test_ocr_text_detector.py`
- **Any** (6 connections)
- **.define()** (5 connections) — `app/judger/ocr_text_detector.py`
- **.test_empty_expected_text_and_no_text_are_always_ng()** (5 connections) — `app/tests/judger/test_ocr_text_detector.py`
- **.test_exact_text_match_ignores_only_outer_whitespace_and_rotation()** (5 connections) — `app/tests/judger/test_ocr_text_detector.py`
- **.compare()** (4 connections) — `app/judger/ocr_text_detector.py`
- **.judge()** (4 connections) — `app/judger/ocr_text_detector.py`
- **.test_comparison_is_case_sensitive_and_preserves_internal_spaces()** (4 connections) — `app/tests/judger/test_ocr_text_detector.py`
- **.test_multiline_text_is_compared_with_newline_order_preserved()** (4 connections) — `app/tests/judger/test_ocr_text_detector.py`
- **._crop_text_region()** (3 connections) — `app/engines/ocr_text_service.py`
- **._get_models()** (3 connections) — `app/engines/ocr_text_service.py`
- **._average_confidence()** (3 connections) — `app/judger/ocr_text_detector.py`
- **._standard_regions()** (3 connections) — `app/judger/ocr_text_detector.py`
- **Any** (3 connections)
- **.__init__()** (2 connections) — `app/engines/ocr_text_service.py`
- **.__init__()** (2 connections) — `app/judger/ocr_text_detector.py`
- **ndarray** (2 connections)
- *... and 7 more nodes in this community*

## Relationships

- [Community 40](Community_40.md) (12 shared connections)
- [Community 14](Community_14.md) (2 shared connections)
- [Community 80](Community_80.md) (1 shared connections)
- [Community 134](Community_134.md) (1 shared connections)
- [Community 52](Community_52.md) (1 shared connections)

## Source Files

- `app/engines/ocr_text_service.py`
- `app/judger/ocr_text_detector.py`
- `app/tests/judger/test_ocr_text_detector.py`

## Audit Trail

- EXTRACTED: 77 (94%)
- INFERRED: 5 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*