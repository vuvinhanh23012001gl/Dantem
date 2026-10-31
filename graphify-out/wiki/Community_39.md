# Community 39

> 59 nodes

## Key Concepts

- **FaceModelPatchCore** (15 connections) — `app/engines/AI_model_process/face_patch_core_process.py`
- **FaceModelYoloObject** (14 connections) — `app/engines/AI_model_process/face_yolo_object_process.py`
- **.crop_image()** (9 connections) — `app/utils/opencv_tool.py`
- **.get_bounding_boxes()** (8 connections) — `app/engines/AI_model_process/face_patch_core_process.py`
- **.get_objects()** (8 connections) — `app/engines/AI_model_process/face_yolo_object_process.py`
- **FacePatchCoreObjectDetector** (7 connections) — `app/engines/AI_model_process/face_patch_core_object_detector.py`
- **.draw()** (7 connections) — `app/engines/AI_model_process/face_yolo_object_process.py`
- **.search()** (7 connections) — `app/engines/AI_model_process/face_yolo_object_process.py`
- **test_get_bounding_boxes_crops_roi_and_restores_coordinates()** (7 connections) — `app/tests/engines/AI_model_process/test_face_patch_core_process.py`
- **test_predict_crops_roi_before_model_call()** (7 connections) — `app/tests/engines/AI_model_process/test_face_patch_core_process.py`
- **test_rejects_invalid_roi()** (7 connections) — `app/tests/engines/AI_model_process/test_face_patch_core_process.py`
- **ndarray** (7 connections)
- **.predict()** (6 connections) — `app/engines/AI_model_process/face_patch_core_process.py`
- **.predict_with_anomaly_boxes()** (6 connections) — `app/engines/AI_model_process/face_patch_core_process.py`
- **._validate_roi()** (6 connections) — `app/engines/AI_model_process/face_patch_core_process.py`
- **.search_negative()** (6 connections) — `app/engines/AI_model_process/face_yolo_object_process.py`
- **.detect_anomaly_objects()** (5 connections) — `app/engines/AI_model_process/face_patch_core_object_detector.py`
- **.convert_boxes_to_original_image()** (5 connections) — `app/engines/AI_model_process/face_patch_core_process.py`
- **.search_all_negative()** (5 connections) — `app/engines/AI_model_process/face_yolo_object_process.py`
- **main()** (5 connections) — `app/tests/engines/AI_model_process/test_face_patch_core_process.py`
- **ndarray** (5 connections)
- **.detect_anomaly_objects_with_heatmap()** (4 connections) — `app/engines/AI_model_process/face_patch_core_object_detector.py`
- **.__init__()** (4 connections) — `app/engines/AI_model_process/face_patch_core_object_detector.py`
- **.draw_rectangle()** (4 connections) — `app/engines/AI_model_process/face_yolo_object_process.py`
- **.filter_objects_by_class_name()** (4 connections) — `app/engines/AI_model_process/face_yolo_object_process.py`
- *... and 34 more nodes in this community*

## Relationships

- [Community 22](Community_22.md) (13 shared connections)
- [Community 40](Community_40.md) (7 shared connections)
- [Community 21](Community_21.md) (1 shared connections)
- [Community 52](Community_52.md) (1 shared connections)
- [Community 128](Community_128.md) (1 shared connections)
- [Community 45](Community_45.md) (1 shared connections)
- [Community 27](Community_27.md) (1 shared connections)
- [Community 18](Community_18.md) (1 shared connections)

## Source Files

- `app/engines/AI_model_process/face_patch_core_object_detector.py`
- `app/engines/AI_model_process/face_patch_core_process.py`
- `app/engines/AI_model_process/face_yolo_object_process.py`
- `app/engines/AI_model_process/frame_yolo_object_process.py`
- `app/tests/engines/AI_model_process/test_face_patch_core_process.py`
- `app/utils/opencv_tool.py`

## Audit Trail

- EXTRACTED: 110 (92%)
- INFERRED: 9 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*