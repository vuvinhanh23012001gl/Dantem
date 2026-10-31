# Community 63

> 23 nodes

## Key Concepts

- **.inspect_image()** (16 connections) — `app_demo_ocr_reverses/app/services/ocr_service.py`
- **OCRInspectionResult** (14 connections) — `app_demo_ocr_reverses/app/schemas/ocr_schema.py`
- **DocumentOrientationInfo** (10 connections) — `app_demo_ocr_reverses/app/schemas/ocr_schema.py`
- **TextLineResult** (10 connections) — `app_demo_ocr_reverses/app/schemas/ocr_schema.py`
- **ocr_schema.py** (10 connections) — `app_demo_ocr_reverses/app/schemas/ocr_schema.py`
- **.aggregate_document_orientation()** (5 connections) — `app_demo_ocr_reverses/app/services/orientation_service.py`
- **schemas/__init__.py** (5 connections) — `app_demo_ocr_reverses/app/schemas/__init__.py`
- **.classify_document()** (4 connections) — `app_demo_ocr_reverses/app/models/orientation_engine.py`
- **.classify_textline_batch()** (4 connections) — `app_demo_ocr_reverses/app/models/orientation_engine.py`
- **.resolve_line_orientation()** (4 connections) — `app_demo_ocr_reverses/app/services/orientation_service.py`
- **BaseModel** (3 connections)
- **ndarray** (2 connections)
- **ndarray** (1 connections)
- **Path** (1 connections)
- **Predict whole-document cardinal orientation (0, 90, 180, 270) on the raw input…** (1 connections) — `app_demo_ocr_reverses/app/models/orientation_engine.py`
- **Classify a batch of rectified horizontal text-line crops into 0° or 180°.…** (1 connections) — `app_demo_ocr_reverses/app/models/orientation_engine.py`
- **Data schemas for OCR and Orientation results.** (1 connections) — `app_demo_ocr_reverses/app/schemas/__init__.py`
- **OCR and orientation result for an individual text line on the original image.** (1 connections) — `app_demo_ocr_reverses/app/schemas/ocr_schema.py`
- **Orientation information of the original image BEFORE any automatic rotation.…** (1 connections) — `app_demo_ocr_reverses/app/schemas/ocr_schema.py`
- **Complete output schema for industrial OCR and orientation inspection.** (1 connections) — `app_demo_ocr_reverses/app/schemas/ocr_schema.py`
- **Run full OCR and orientation analysis on an image path or BGR numpy array.…** (1 connections) — `app_demo_ocr_reverses/app/services/ocr_service.py`
- **Aggregate per-line orientations and the whole-document classifier prediction…** (1 connections) — `app_demo_ocr_reverses/app/services/orientation_service.py`
- **Evaluate 4 candidate hypotheses for a single cropped text line: - c0: Direct 0°…** (1 connections) — `app_demo_ocr_reverses/app/services/orientation_service.py`

## Relationships

- [Community 58](Community_58.md) (13 shared connections)
- [Community 54](Community_54.md) (8 shared connections)
- [Community 61](Community_61.md) (4 shared connections)
- [Community 64](Community_64.md) (3 shared connections)
- [Community 89](Community_89.md) (2 shared connections)
- [Community 96](Community_96.md) (2 shared connections)
- [Community 40](Community_40.md) (1 shared connections)
- [Community 36](Community_36.md) (1 shared connections)

## Source Files

- `app_demo_ocr_reverses/app/models/orientation_engine.py`
- `app_demo_ocr_reverses/app/schemas/__init__.py`
- `app_demo_ocr_reverses/app/schemas/ocr_schema.py`
- `app_demo_ocr_reverses/app/services/ocr_service.py`
- `app_demo_ocr_reverses/app/services/orientation_service.py`

## Audit Trail

- EXTRACTED: 51 (77%)
- INFERRED: 15 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*