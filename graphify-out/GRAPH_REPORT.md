# Graph Report - Inspector_carton  (2026-11-02)

## Corpus Check
- 323 files · ~29,293,154 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 52 file(s) not represented in the graph (top: .css 10, .npy 9, .index 9)

## Summary
- 3853 nodes · 8938 edges · 176 communities (72 shown, 104 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 623 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `aa2102d9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- trainler.py
- summary_tool.js
- ColorService
- Config_SoftWare
- drawRoi
- .__init__
- container.py
- ModelPatchCore
- config_software.js
- StampReversedService
- ItemsInspector
- anomaly_point_tool.js
- StagePreprocess
- color_tool.js
- Judment
- home.js
- foreign_object_tool.js
- JudmentLawProductSevice
- .compare
- PointService
- JudmentLawProductRepository
- pathlib
- numpy
- test_anti_blur_logic.py
- api_captureproduct.py
- IAIControl
- retired_inspectors_migration.py
- model_AI/__init__.py
- AnomalyPointDetector
- capture_face.js
- PatchCoreTrainConfig
- .save_training_input
- ModelUnet
- PLCTCPServer
- MotionSimulator
- handler_work_detect.py
- model/__init__.py
- ocr_tool.js
- RectangleDrawer
- FaceModelPatchCore
- JudgmentResult
- add_new_product.js
- numpy
- MainWindow
- RegionApiTests
- CaptureItemDeleteService
- cnd_lybrary.js
- IAIConfig
- app_demorobot/ui/main_window.py
- ForeignObjectPatchCoreService
- StructureFaceYoloService
- barcode_tool.js
- app/config/__init__.py
- common_value.js
- OCRService
- stamp_tool.js
- .Ok
- BarcodeAccountRepository
- ocr_service.py
- RobotState
- Point
- OCRService
- RuntimeState
- .inspect_image
- ScalableImageLabel
- RobotControl
- ModelStorageTests
- stamp_reversed_tool.js
- OCRTextDetector
- Log_CSV
- CanvasManager
- Senior Python & Computer Vision Web Engineer
- Folder
- Log_Txt
- RobotConfig
- Infor_Software
- Worker
- AnomalyPointInspector
- barcode_config.js
- PoseCardWidget
- api_robot_config.py
- FaceHandlers
- ProductCountRepository
- api_barcode.py
- ocr_service.py
- geometry.py
- threading
- api_product.py
- TestCameraConfigAPI
- ForeignObjectInspector
- Project Standards — Python & Computer Vision
- OCREngine
- ProductRepository
- BarcodeAccountService
- TestAntiBlurAPI
- PHẦN MỀM GIẢ LẬP PLC ROBOT (APP_DEMOROBOT)
- StampAlignmentItemInspector
- Logic
- stamp_alignment_tool.js
- TrainWorkerPatchCore
- service/__init__.py
- TestPackagedPathConfig
- Manager_Log
- Hệ Thống OCR Nhận Diện Nội Dung & Xác Định Hướng Chữ Công Nghiệp (`app_demo_ocr_reverses`)
- get
- ColorItemInspector
- PatchCoreTrainRecordRepository
- Camera
- MultiRegionDetectorTests
- RectangleDrawer
- FakePointService
- Change_Disk
- TestAnomalyPointRoiIsolation
- Product
- test_trainler_patchcore_runtime_with_workspace_images
- Line
- StampReversedItemInspector
- load_settings
- FilmBorder
- ModelSlit
- Dantem
- .test_config_software_max_workers_validation
- TestBarcodeAPI
- .update
- ProductCountService
- .test_manager_log_pipeline_integration
- instruct_fix_erro.js
- instruct_staff_ee.js
- instruct_worker.js
- StampAlignmentDetector
- TestBarcodeAccount
- FakeOCRDetector
- get_instruct_fix_erro
- get_instruct_staff_ee
- get_instruct_worker
- ServiceContainer
- test_crop.py
- .is_pose_safe
- validate/__init__.py
- ForeignObjectPatchCoreService

## God Nodes (most connected - your core abstractions)
1. `ServiceContainer` - 79 edges
2. `Config_SoftWare` - 73 edges
3. `PatchCoreTrainRecordRepository` - 62 edges
4. `IAIControl` - 60 edges
5. `StageTransform` - 57 edges
6. `Result` - 52 edges
7. `JudgmentResult` - 52 edges
8. `ModelPatchCore` - 44 edges
9. `PointService` - 44 edges
10. `MainWindow` - 43 edges

## Surprising Connections (you probably didn't know these)
- `TestStage2AntiBlurIntegration` --uses--> `IAIConfig`  [INFERRED]
  app/tests/inspection/test_anti_blur_logic.py → app/config/iai_config.py
- `ServiceContainer` --uses--> `RobotConfig`  [INFERRED]
  app/container.py → app/config/robot_config.py
- `RobotControl` --uses--> `RobotConfig`  [INFERRED]
  app/machine/robot_control.py → app/config/robot_config.py
- `get_robot_config()` --uses--> `RobotConfig`  [INFERRED]
  app/routers/api_robot_config.py → app/config/robot_config.py
- `get_robot_defaults()` --uses--> `RobotConfig`  [INFERRED]
  app/routers/api_robot_config.py → app/config/robot_config.py

## Import Cycles
- None detected.

## Communities (176 total, 104 thin omitted)

### Community 0 - "trainler.py"
Cohesion: 0.05
Nodes (6): CroppedImageFolder, PatchCoreImageDataset, main(), TrainlerPatchCore, main(), test_find_runtime_session_preserves_existing_session()

### Community 1 - "summary_tool.js"
Cohesion: 0.06
Nodes (50): openOptionPanel(), boxContentAnomalyPoint, boxContentColor, boxContentForeignObject, boxContentQR, checkSelected(), dict_callbacks, getNameEventActivate() (+42 more)

### Community 4 - "drawRoi"
Cohesion: 0.10
Nodes (15): drawRoi(), ROI_STYLE, ModelRectangle, BarcodeItemInspector, OCRItemInspector, QRItemInspector, StampItemInspector, drawPendingRectangle() (+7 more)

### Community 5 - ".__init__"
Cohesion: 0.08
Nodes (10): BarcodeQRService, BarcodeDetector, QRDetector, _generate_barcode_image(), _generate_qr_image(), test_barcode_detector_evaluate_roi(), test_barcode_service_scan_missing(), test_barcode_service_scan_success() (+2 more)

### Community 6 - "container.py"
Cohesion: 0.03
Nodes (13): EnumMode, AppContext, RuntimePipelineState, InspectionTaskItem, StageTransform, StageExport, TestStage2AntiBlurIntegration, DummyPreparedProduct (+5 more)

### Community 7 - "ModelPatchCore"
Cohesion: 0.07
Nodes (6): PatchCoreAnomalyConfig, ModelPatchCore, build_patchcore_model(), _crop_image(), main(), test_run_patchcore_inference_from_latest_record()

### Community 8 - "config_software.js"
Cohesion: 0.07
Nodes (49): applyLogConfigToForm(), applyRobotConfigToForm(), btn_antiblur_auto_calc, btn_antiblur_reload_features, btn_antiblur_reset_defaults, btn_apply_settings, btn_browse_log_dir, btn_browse_output_dir (+41 more)

### Community 9 - "StampReversedService"
Cohesion: 0.11
Nodes (7): StampReversedService, StampReversedDetector, create_ocr_line(), FakeOCRService, FakeYoloOBB, TestStampReversedDetector, TestStampReversedService

### Community 10 - "ItemsInspector"
Cohesion: 0.06
Nodes (5): Face, Frame, Measurement, Product, ItemsInspector

### Community 11 - "anomaly_point_tool.js"
Cohesion: 0.09
Nodes (44): activatePanel(), anomalyPanels, baseQuery(), btnCreateModel, btnDeleteModel, btnExit, btnRunModel, btnRuntimeImages (+36 more)

### Community 12 - "StagePreprocess"
Cohesion: 0.06
Nodes (4): Pipeline, PreparedProduct, StagePreprocess, TestStage1Caching

### Community 13 - "color_tool.js"
Cohesion: 0.19
Nodes (16): closeButton, createConfigRow(), deltaE2000(), deltaE76(), event_transition_items(), extractAverageRgb(), getInspector(), judgmentButton (+8 more)

### Community 15 - "home.js"
Cohesion: 0.07
Nodes (40): set_camera_connection(), set_tcp_connection(), SocketLog, btn_left, btn_reset_count_total, btn_right, circle_status_connect_camera, circle_status_connect_tcp (+32 more)

### Community 16 - "foreign_object_tool.js"
Cohesion: 0.12
Nodes (43): write_log_append(), activateForeignObjectPanel(), btnCreateModel, btnDeleteModel, btnDetectObject, btnExitForeignObject, btnRunModel, btnRuntimeImages (+35 more)

### Community 19 - "PointService"
Cohesion: 0.05
Nodes (3): Result, PointService, test_point_service()

### Community 22 - "numpy"
Cohesion: 0.06
Nodes (19): ClassNameForeignObjectConfig, ClassNameObjectStructureDetectConfig, YoloDetectObjectConfig, FacePatchCoreObjectDetector, ModelYoloObject, ForeignObjectDetector, build_yolo_model(), draw_heatmap() (+11 more)

### Community 23 - "test_anti_blur_logic.py"
Cohesion: 0.07
Nodes (9): AntiBlurService, calculate_anti_blur_timers(), get_anti_blur_config(), get_anti_blur_defaults(), reload_features_config(), save_anti_blur_config(), TestAntiBlurConfigCache, TestAntiBlurFormulas (+1 more)

### Community 24 - "api_captureproduct.py"
Cohesion: 0.04
Nodes (34): TypeSend, create_container(), get_services(), get_services_ws(), create_app(), lifespan(), camera_ws(), capture() (+26 more)

### Community 26 - "retired_inspectors_migration.py"
Cohesion: 0.18
Nodes (6): _atomic_json(), _is_link(), main(), migrate_retired_inspectors(), _read_json(), RetirementTests

### Community 27 - "model_AI/__init__.py"
Cohesion: 0.07
Nodes (5): YoloSegmentConfig, FaceModelYoloSegment, ModelYoloSegment, main(), main()

### Community 28 - "AnomalyPointDetector"
Cohesion: 0.10
Nodes (5): AnomalyPointDetector, FakeAnomalyService, FakePatchCoreFrame, _item_config(), TestAnomalyPointDetector

### Community 29 - "capture_face.js"
Cohesion: 0.09
Nodes (45): anonymous, btn_add_point, btn_robot_home, btn_robot_reset, btn_robot_stop, btn_run_product, btn_stream_video, clampWithSafety() (+37 more)

### Community 30 - "PatchCoreTrainConfig"
Cohesion: 0.20
Nodes (5): PatchCoreTrainConfig, _create_roi_dataset(), main(), test_trainler_patchcore_logic(), test_patchcore_train_config_defaults()

### Community 32 - "ModelUnet"
Cohesion: 0.09
Nodes (5): UnetConfig, ModelUnet, crop_img(), get_touching_boundary_boxes(), main()

### Community 34 - "MotionSimulator"
Cohesion: 0.12
Nodes (4): MotionSimulator, CommandParser, StateEnum, TestProtocolAndServer

### Community 35 - "handler_work_detect.py"
Cohesion: 0.09
Nodes (3): ProductAggregator, ModelHandler, HandlerWorkDetect

### Community 36 - "model/__init__.py"
Cohesion: 0.10
Nodes (9): Line, BaseAI, print_result(), test_add_roi_image(), test_delete_product(), test_get_all_products(), test_get_arr_path_img_roi_product_by_id(), test_get_product() (+1 more)

### Community 37 - "ocr_tool.js"
Cohesion: 0.18
Nodes (14): ACTIVATION_DISTANCE_WHEN_CLICKING_THE_SQUARE, boxContentOCR, obj_region_ocr_canvas, panner_region_ocr, closeButton, event_transition_items(), getInspector(), logOCR (+6 more)

### Community 38 - "RectangleDrawer"
Cohesion: 0.17
Nodes (4): LineDrawer, drawPoint(), drawTransparentLine(), isPointOnLineSegment()

### Community 39 - "FaceModelPatchCore"
Cohesion: 0.06
Nodes (6): FaceModelPatchCore, FaceModelYoloObject, main(), test_get_bounding_boxes_crops_roi_and_restores_coordinates(), test_predict_crops_roi_before_model_call(), test_rejects_invalid_roi()

### Community 40 - "JudgmentResult"
Cohesion: 0.07
Nodes (10): BaseJudgerAI, JudgmentResult, ColorDetector, StampDetector, create_recording_inspector(), judge(), load_item_config(), main() (+2 more)

### Community 41 - "add_new_product.js"
Cohesion: 0.09
Nodes (23): add_product, btn_cancel_delete, btn_confirm_delete, close_add_product, close_right_panel, createDataShowTable(), form_add_new_product, imageInput (+15 more)

### Community 42 - "numpy"
Cohesion: 0.09
Nodes (20): create_base_industrial_label(), create_mixed_orientation_label(), create_symmetric_edgecase_180_label(), degrade_blur_noisy_lowlight(), _load_font(), main(), rotate_slight_tilt(), inspect_stamp_alignment() (+12 more)

### Community 46 - "cnd_lybrary.js"
Cohesion: 0.15
Nodes (21): a(), i(), At(), c(), e(), Et(), f(), ft() (+13 more)

### Community 47 - "IAIConfig"
Cohesion: 0.11
Nodes (3): IAIConfig, IAIService, main()

### Community 48 - "app_demorobot/ui/main_window.py"
Cohesion: 0.11
Nodes (4): main(), CommandHistoryTable, LogViewerWidget, TowerLightWidget

### Community 50 - "StructureFaceYoloService"
Cohesion: 0.13
Nodes (3): StructureFaceYoloService, FakeStampFrameModel, TestStampDetector

### Community 51 - "barcode_tool.js"
Cohesion: 0.12
Nodes (29): closeButton, event_transition_items(), getInspector(), logBarcode, openRectangleEditor(), originalOnClick, removeStoredRectangle(), runButton (+21 more)

### Community 52 - "app/config/__init__.py"
Cohesion: 0.08
Nodes (10): TypeDataSendClient, CameraConfig, QueueConfig, ChooseProductRepository, PointRepository, print_result(), test_get_choose_product(), test_reset_choose_product() (+2 more)

### Community 53 - "common_value.js"
Cohesion: 0.08
Nodes (22): cameraConfigButton, cameraConfigFields, cameraConfigLog, cameraConfigPanel, openCameraConfigPanel(), renderCameraConfig(), requestCameraConfig(), active_sceen_show_video() (+14 more)

### Community 54 - "OCRService"
Cohesion: 0.14
Nodes (6): save_image_unicode(), main(), run_cli_inspection(), OCRService, VisualizationService, evaluate_all()

### Community 55 - "stamp_tool.js"
Cohesion: 0.18
Nodes (14): boxContentStamp, COLOR_RECT_SHAPE_REGION_DETECT, obj_region_stamp_canvas, panner_region_stamp, closeButton, event_transition_items(), getInspector(), judgmentButton (+6 more)

### Community 56 - ".Ok"
Cohesion: 0.06
Nodes (4): ChooseProductService, ProductService, FakePointService, FakeStampAlignmentService

### Community 58 - "ocr_service.py"
Cohesion: 0.19
Nodes (3): InspectionJudgement, OrientationStatus, OrientationService

### Community 63 - ".inspect_image"
Cohesion: 0.13
Nodes (3): DocumentOrientationInfo, OCRInspectionResult, TextLineResult

### Community 68 - "stamp_reversed_tool.js"
Cohesion: 0.19
Nodes (14): boxContentStampReversed, obj_region_stamp_reversed_canvas, panner_region_stamp_reversed, closeButton, createConfigRow(), event_transition_items(), getInspector(), judgmentButton (+6 more)

### Community 69 - "OCRTextDetector"
Cohesion: 0.21
Nodes (4): OCRTextDetector, FakeOCRService, ocr_result(), TestOCRTextDetector

### Community 72 - "Senior Python & Computer Vision Web Engineer"
Cohesion: 0.10
Nodes (20): 1. Vai trò và trách nhiệm, 2.1. Python & Backend, 2.2. Computer Vision & AI, 2.3. Tối ưu hóa hệ thống, 2. Năng lực chuyên môn, 3.1. Báo cáo tiến trình, 3. Nguyên tắc giao tiếp, 4. Quy trình xử lý task (+12 more)

### Community 78 - "RobotConfig"
Cohesion: 0.12
Nodes (7): RobotConfig, test_api_robot_get_config(), test_api_robot_get_defaults(), test_api_robot_save_config(), test_api_test_connection_unreachable(), test_api_validate_pose(), test_robot_config_defaults()

### Community 82 - "barcode_config.js"
Cohesion: 0.13
Nodes (15): barcodeListBody, barcodeStatusMsg, btnCloseBarcode, btnCreateBarcode, btnOpenBarcode, escapeHtml(), formAddBarcode, handleDeleteBarcode() (+7 more)

### Community 84 - "api_robot_config.py"
Cohesion: 0.20
Nodes (5): get_robot_config(), get_robot_defaults(), save_robot_config(), test_robot_connection(), validate_pose()

### Community 88 - "api_barcode.py"
Cohesion: 0.15
Nodes (7): create_barcode_account(), CreateBarcodeAccountRequest, get_admin_info(), get_barcode_accounts(), update_admin_info(), UpdateAdminRequest, validate_barcode()

### Community 90 - "geometry.py"
Cohesion: 0.22
Nodes (5): compute_skew_angle_deg(), crop_text_region(), order_quad_points(), read_image_unicode(), restore_upright_image()

### Community 91 - "threading"
Cohesion: 0.09
Nodes (4): BaseConfig, ModeState, _delayed_exit(), shutdown_system()

### Community 92 - "api_product.py"
Cohesion: 0.33
Nodes (5): delete_preview(), erase_product(), get_product(), list_product(), select_product_new()

### Community 95 - "Project Standards — Python & Computer Vision"
Cohesion: 0.15
Nodes (12): 10. Kiểm thử & hoàn thiện, 11. Nguyên tắc kết thúc thay đổi, 1. Mục tiêu, 2. Quy tắc sửa đổi mã nguồn, 3. Python Coding Standards, 4. Kiến trúc và dữ liệu, 5. Graphify & phân tích kiến trúc, 6. Computer Vision & AI (+4 more)

### Community 101 - "PHẦN MỀM GIẢ LẬP PLC ROBOT (APP_DEMOROBOT)"
Cohesion: 0.17
Nodes (11): 1.1. Cấu hình Mạng TCP Socket, 1.2. Danh mục Lệnh từ PC gửi tới PLC (PC -> PLC), 1.3. Danh mục Phản hồi từ PLC trả về PC (PLC -> PC), 1. Bảng Đặc Tả Tập Lệnh & Giao Thức (Theo `Bang_Giao_Tiep_Robot_PLC_PROD4.xlsx`), 2. Cấu Trúc Thư Mục Dự Án, 3.1. Khởi động Giao diện Giả lập PLC, 3.2. Chạy Kiểm thử Tự động (Unit Tests & Socket Integration Tests), 3. Hướng Dẫn Cài Đặt & Khởi Động (+3 more)

### Community 108 - "stamp_alignment_tool.js"
Cohesion: 0.18
Nodes (15): boxContentStampAlignment, obj_region_stamp_alignment_canvas, panner_region_stamp_alignment, selected, closeButton, createConfigRow(), event_transition_items(), getInspector() (+7 more)

### Community 109 - "TrainWorkerPatchCore"
Cohesion: 0.08
Nodes (7): PatchCoreTrainRequest, TrainWorkerPatchCore, FakeTrainer, main(), test_train_worker_waits_for_required_images(), main(), test_run_train_worker_patchcore_runtime()

### Community 111 - "service/__init__.py"
Cohesion: 0.11
Nodes (3): ModelYoloOBB, OCRTextService, StampAlignmentService

### Community 113 - "Manager_Log"
Cohesion: 0.05
Nodes (4): LogCleanupWorker, Log_Img, Manager_Log, TestStorageOptimization

### Community 115 - "Hệ Thống OCR Nhận Diện Nội Dung & Xác Định Hướng Chữ Công Nghiệp (`app_demo_ocr_reverses`)"
Cohesion: 0.12
Nodes (11): 1. Tổng quan & Mục tiêu, 2. Khảo sát & Lựa chọn Thư viện / Mô hình OCR, 3. Cấu trúc Source Code (OOP), 4. Hướng dẫn Cài đặt & Khởi chạy, 5. Định dạng JSON Kết quả Đầu ra, A. Kích hoạt môi trường ảo (`.venv`), B. Khởi chạy Giao diện Đồ họa (PySide6 GUI), C. Kiểm tra ảnh bất kỳ bằng dòng lệnh (CLI Mode) (+3 more)

### Community 117 - "get"
Cohesion: 0.20
Nodes (4): get_ai_model_paths(), get_config_logs(), software_information(), software_version()

### Community 119 - "PatchCoreTrainRecordRepository"
Cohesion: 0.08
Nodes (5): PatchCoreTrainRecordRepository, main(), test_patchcore_train_record_service_logic(), main(), test_run_patchcore_train_record_service()

### Community 122 - "MultiRegionDetectorTests"
Cohesion: 0.19
Nodes (3): config_region(), MultiRegionDetectorTests, region()

### Community 126 - "FakePointService"
Cohesion: 0.29
Nodes (3): FakeColorService, FakePointService, TestColorAPI

### Community 128 - "TestAnomalyPointRoiIsolation"
Cohesion: 0.11
Nodes (4): AnomalyPointPatchCoreService, _FakeWorker, _make_model(), TestAnomalyPointRoiIsolation

### Community 131 - "test_trainler_patchcore_runtime_with_workspace_images"
Cohesion: 0.29
Nodes (3): _crop_image(), main(), test_trainler_patchcore_runtime_with_workspace_images()

### Community 142 - "Dantem"
Cohesion: 0.40
Nodes (4): 1. Giới thiệu dự án, 2. Hướng dẫn cài đặt môi trường, 3. Khởi chạy ứng dụng, Dantem

### Community 171 - "FakeOCRDetector"
Cohesion: 0.25
Nodes (3): FakeOCRDetector, FakePointService, TestOCRAPI

### Community 175 - "ServiceContainer"
Cohesion: 0.07
Nodes (28): ServiceContainer, erase_frame(), erase_item_img(), anomaly_point_runtime_images(), anomaly_point_train_status(), create_anomaly_point_model(), create_foreign_object_model(), delete_anomaly_point_model() (+20 more)

### Community 177 - "test_crop.py"
Cohesion: 0.38
Nodes (3): center_to_box(), crop_image(), main()

## Knowledge Gaps
- **104 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config_SoftWare` connect `Config_SoftWare` to `.read_json_from_file`, `.__init__`, `container.py`, `Log_CSV`, `JudgmentResult`, `Judment`, `.test_config_software_max_workers_validation`, `Manager_Log`, `Path`, `get`, `pathlib`, `api_captureproduct.py`, `.test_manager_log_pipeline_integration`, `.test_config_software_log_dir_and_retrain_inspectors`, `Change_Disk`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `ServiceContainer` (e.g. with `RobotConfig` and `RuntimeState`) actually correct?**
  _`ServiceContainer` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Should `trainler.py` be split into smaller, more focused modules?**
  _Cohesion score 0.049107142857142856 - nodes in this community are weakly interconnected._
- **Why does `IAIControl` connect `IAIControl` to `.stop`, `.__init__`, `container.py`, `.move_to_point`, `._handle_single_input_message`, `.send_log_html`, `.send_command_stm32`, `ServiceContainer`, `IAIConfig`, `.start_thread_handl_request_stm32`, `threading`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Config_SoftWare` (e.g. with `Judment` and `get_config_logs()`) actually correct?**
  _`Config_SoftWare` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `summary_tool.js` be split into smaller, more focused modules?**
  _Cohesion score 0.05723905723905724 - nodes in this community are weakly interconnected._
- **Why does `StageTransform` connect `container.py` to `Config_SoftWare`, `StagePreprocess`, `ServiceContainer`, `Manager_Log`, `pathlib`, `test_anti_blur_logic.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._