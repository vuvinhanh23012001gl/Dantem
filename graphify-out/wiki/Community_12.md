# Community 12

> 41 nodes

## Key Concepts

- **StagePreprocess** (26 connections) — `app/stages/stage_1_preprocess.py`
- **TestStage1Caching** (10 connections) — `app/tests/stages/test_stage_1_caching.py`
- **PreparedProduct** (8 connections) — `app/stages/stage_1_preprocess.py`
- **.run()** (7 connections) — `app/stages/stage_1_preprocess.py`
- **._load_and_cache_locked()** (6 connections) — `app/stages/stage_1_preprocess.py`
- **._load_product_data()** (5 connections) — `app/stages/stage_1_preprocess.py`
- **.test_mark_dirty_triggers_reload_and_notifies_ui()** (5 connections) — `app/tests/stages/test_stage_1_caching.py`
- **.test_mtime_guard_auto_reloads_when_file_modified_externally()** (5 connections) — `app/tests/stages/test_stage_1_caching.py`
- **.test_run_reuses_ram_cache_without_reading_disk()** (5 connections) — `app/tests/stages/test_stage_1_caching.py`
- **.mark_dirty()** (4 connections) — `app/stages/stage_1_preprocess.py`
- **.preload()** (4 connections) — `app/stages/stage_1_preprocess.py`
- **.test_preload_on_init()** (4 connections) — `app/tests/stages/test_stage_1_caching.py`
- **object** (4 connections)
- **._has_files_changed_on_disk()** (3 connections) — `app/stages/stage_1_preprocess.py`
- **.__init__()** (3 connections) — `app/stages/stage_1_preprocess.py`
- **._read_json()** (3 connections) — `app/stages/stage_1_preprocess.py`
- **.check_protocol_connect_com()** (2 connections) — `app/stages/stage_1_preprocess.py`
- **._pick_default_scale()** (2 connections) — `app/stages/stage_1_preprocess.py`
- **._read_frame_scale()** (2 connections) — `app/stages/stage_1_preprocess.py`
- **._sort_key()** (2 connections) — `app/stages/stage_1_preprocess.py`
- **.setUp()** (2 connections) — `app/tests/stages/test_stage_1_caching.py`
- **.face_calibrations()** (1 connections) — `app/stages/stage_1_preprocess.py`
- **.faces()** (1 connections) — `app/stages/stage_1_preprocess.py`
- **Lấy dữ liệu từ RAM cho chu kỳ này và chuyển sang Stage 2. Input: dữ liệu sản…** (1 connections) — `app/stages/stage_1_preprocess.py`
- **Đọc một file JSON object. Input: ``path`` là đường dẫn file JSON. Output:…** (1 connections) — `app/stages/stage_1_preprocess.py`
- *... and 16 more nodes in this community*

## Relationships

- [Community 68](Community_68.md) (10 shared connections)
- [Community 90](Community_90.md) (2 shared connections)
- [Community 175](Community_175.md) (2 shared connections)

## Source Files

- `app/stages/stage_1_preprocess.py`
- `app/tests/stages/test_stage_1_caching.py`

## Audit Trail

- EXTRACTED: 63 (86%)
- INFERRED: 10 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*