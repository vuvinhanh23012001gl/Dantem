# Community 18

> 62 nodes

## Key Concepts

- **MultiRegionDetectorTests** (18 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **.compare()** (13 connections) — `app/judger/foreign_object_detector.py`
- **TestForeignObjectDetectorLogic** (12 connections) — `app/tests/judger/test_foreign_object_detector.py`
- **.evaluate_regions()** (11 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **.define()** (10 connections) — `app/judger/foreign_object_detector.py`
- **.judge()** (9 connections) — `app/judger/foreign_object_detector.py`
- **config_region()** (7 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **.test_config_tasks_and_overlay_cover_both_regions()** (7 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **region()** (7 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **.draw_labeled_roi()** (7 connections) — `app/utils/opencv_tool.py`
- **.save_training_input()** (7 connections) — `app/utils/opencv_tool.py`
- **._define_single()** (6 connections) — `app/judger/foreign_object_detector.py`
- **Any** (5 connections)
- **.__init__()** (4 connections) — `app/judger/foreign_object_detector.py`
- **.test_empty_and_invalid_regions_are_rejected()** (4 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **.test_legacy_coordinate_and_keyword_calls()** (4 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **.test_case_1_score_less_than_or_equal_threshold_is_ok()** (4 connections) — `app/tests/judger/test_foreign_object_detector.py`
- **.test_case_2_score_greater_than_threshold_without_yolo_detections_is_ok()** (4 connections) — `app/tests/judger/test_foreign_object_detector.py`
- **.test_case_3_score_greater_than_threshold_with_yolo_detections_is_ng()** (4 connections) — `app/tests/judger/test_foreign_object_detector.py`
- **ndarray** (4 connections)
- **.test_legacy_config_normalizes_id_zero()** (3 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **.test_runtime_images_are_saved_only_for_enabled_region()** (3 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **.test_runtime_save_concurrency_is_bounded_and_reports_saturation()** (3 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **.test_summary_is_ng_with_missing_region_name()** (3 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- **.test_training_input_crops_support_multi_region_and_legacy_calls()** (3 connections) — `app/tests/inspection/test_foreign_object_multi_roi.py`
- *... and 37 more nodes in this community*

## Relationships

- [Community 40](Community_40.md) (13 shared connections)
- [Community 14](Community_14.md) (5 shared connections)
- [Community 52](Community_52.md) (3 shared connections)
- [Community 122](Community_122.md) (2 shared connections)
- [Community 22](Community_22.md) (1 shared connections)
- [Community 66](Community_66.md) (1 shared connections)
- [Community 126](Community_126.md) (1 shared connections)
- [Community 175](Community_175.md) (1 shared connections)
- [Community 28](Community_28.md) (1 shared connections)
- [Community 9](Community_9.md) (1 shared connections)
- [Community 39](Community_39.md) (1 shared connections)

## Source Files

- `app/judger/foreign_object_detector.py`
- `app/tests/inspection/test_foreign_object_multi_roi.py`
- `app/tests/judger/test_foreign_object_detector.py`
- `app/utils/opencv_tool.py`

## Audit Trail

- EXTRACTED: 108 (86%)
- INFERRED: 18 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*