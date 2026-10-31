# Graph Report - Inspector_carton  (2026-10-31)

## Corpus Check
- 324 files · ~36,827,000 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 60 file(s) not represented in the graph (top: .npy 11, .index 11, .pt 11)

## Summary
- 3848 nodes · 8929 edges · 186 communities (75 shown, 111 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 623 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- TrainlerPatchCore
- summary_tool.js
- ColorService
- Config_SoftWare
- drawRoi
- .__init__
- InspectionTaskItem
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
- .__init__
- PointService
- JudmentLawProductRepository
- pathlib
- numpy
- test_anti_blur_logic.py
- FastAPI
- IAIControl
- retired_inspectors_migration.py
- model_AI/__init__.py
- AnomalyPointDetector
- capture_face.js
- trainler.py
- test_product_service.py
- ModelUnet
- PLCTCPServer
- MotionSimulator
- handler_work_detect.py
- api_captureproduct.py
- ocr_tool.js
- RectangleDrawer
- FaceModelPatchCore
- JudgmentResult
- add_new_product.js
- cv2
- MainWindow
- RegionApiTests
- CaptureItemDeleteService
- cnd_lybrary.js
- IAIConfig
- app_demorobot/ui/main_window.py
- ForeignObjectPatchCoreService
- StructureFaceYoloService
- barcode_tool.js
- repository/__init__.py
- common_value.js
- OCRService
- qr_tool.js
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
- StageTransform
- OCRTextDetector
- Log_CSV
- CanvasManager
- Senior Python & Computer Vision Web Engineer
- Folder
- CameraConfig
- Log_Txt
- RobotConfig
- Infor_Software
- Worker
- .run
- barcode_config.js
- PoseCardWidget
- api_robot_config.py
- FaceHandlers
- ProductCountRepository
- api_barcode.py
- OrientationEngine
- Pipeline
- container.py
- dependencies.py
- TestCameraConfigAPI
- ForeignObjectInspector
- Project Standards — Python & Computer Vision
- OCREngine
- ProductRepository
- BarcodeAccountService
- TestAntiBlurAPI
- PHẦN MỀM GIẢ LẬP PLC ROBOT (APP_DEMOROBOT)
- StampAlignmentItemInspector
- ChooseProductService
- Logic
- stamp_alignment_tool.js
- TrainWorkerPatchCore
- ModelYoloOBB
- TestPackagedPathConfig
- TestStorageOptimization
- TestProtocolAndServer
- Hệ Thống OCR Nhận Diện Nội Dung & Xác Định Hướng Chữ Công Nghiệp (`app_demo_ocr_reverses`)
- PatchCoreImageDataset
- get
- ColorItemInspector
- TestStage2PipelinedQueue
- Camera
- MultiRegionDetectorTests
- RectangleDrawer
- FakePointService
- Change_Disk
- TestAnomalyPointRoiIsolation
- .evaluate_sharpness
- camera_status
- Line
- StampReversedItemInspector
- load_settings
- FilmBorder
- ModelSlit
- BarcodeDetector
- .cleanup_now
- .test_config_software_max_workers_validation
- TestBarcodeAPI
- .update
- train_worker.py
- ProductCountService
- OCRTextService
- .test_manager_log_pipeline_integration
- instruct_fix_erro.js
- instruct_staff_ee.js
- instruct_worker.js
- home
- FakeStampAlignmentService
- TestBarcodeAccount
- test_train_worker_patchcore.py
- FakeOCRDetector
- get_instruct_fix_erro
- get_instruct_staff_ee
- get_instruct_worker
- ServiceContainer
- CroppedImageFolder
- test_crop.py
- api_draw_regulations.py
- .is_pose_safe
- validate/__init__.py
- get_admin_info
- test_find_runtime_session_preserves_existing_session

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
- `ServiceContainer` --uses--> `RobotConfig`  [INFERRED]
  app/container.py → app/config/robot_config.py
- `RobotControl` --uses--> `RobotConfig`  [INFERRED]
  app/machine/robot_control.py → app/config/robot_config.py
- `get_robot_config()` --uses--> `RobotConfig`  [INFERRED]
  app/routers/api_robot_config.py → app/config/robot_config.py
- `get_robot_defaults()` --uses--> `RobotConfig`  [INFERRED]
  app/routers/api_robot_config.py → app/config/robot_config.py
- `save_robot_config()` --uses--> `RobotConfig`  [INFERRED]
  app/routers/api_robot_config.py → app/config/robot_config.py

## Import Cycles
- None detected.

## Communities (186 total, 111 thin omitted)

### Community 1 - "summary_tool.js"
Cohesion: 0.06
Nodes (50): openOptionPanel(), boxContentAnomalyPoint, boxContentBarcode, boxContentForeignObject, boxContentStampReversed, checkSelected(), dict_callbacks, getNameEventActivate() (+42 more)

### Community 2 - "ColorService"
Cohesion: 0.10
Nodes (3): ColorService, ColorDetector, TestColorService

### Community 4 - "drawRoi"
Cohesion: 0.10
Nodes (15): drawRoi(), ROI_STYLE, ModelRectangle, BarcodeItemInspector, OCRItemInspector, QRItemInspector, StampItemInspector, drawPendingRectangle() (+7 more)

### Community 5 - ".__init__"
Cohesion: 0.10
Nodes (9): BarcodeQRService, QRDetector, _generate_barcode_image(), _generate_qr_image(), test_barcode_detector_evaluate_roi(), test_barcode_service_scan_missing(), test_barcode_service_scan_success(), test_qr_detector_evaluate_roi() (+1 more)

### Community 7 - "ModelPatchCore"
Cohesion: 0.07
Nodes (7): PatchCoreAnomalyConfig, ModelPatchCore, build_patchcore_model(), _crop_image(), main(), test_run_patchcore_inference_from_latest_record(), test_trainler_patchcore_runtime_with_workspace_images()

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
Cohesion: 0.06
Nodes (42): AnomalyPointInspector, AnomalyPointRegion, activatePanel(), anomalyPanels, baseQuery(), btnCreateModel, btnDeleteModel, btnExit (+34 more)

### Community 12 - "StagePreprocess"
Cohesion: 0.07
Nodes (3): PreparedProduct, StagePreprocess, TestStage1Caching

### Community 13 - "color_tool.js"
Cohesion: 0.15
Nodes (19): closeButton, createConfigRow(), deltaE2000(), deltaE76(), event_transition_items(), extractAverageRgb(), getInspector(), judgmentButton (+11 more)

### Community 14 - "Judment"
Cohesion: 0.07
Nodes (3): InspectorTask, Judment, TestStage2ForeignObjectIntegration

### Community 15 - "home.js"
Cohesion: 0.07
Nodes (42): get_tcp_connection(), set_camera_connection(), set_tcp_connection(), SocketData, SocketLog, btn_left, btn_reset_count_total, btn_right (+34 more)

### Community 16 - "foreign_object_tool.js"
Cohesion: 0.12
Nodes (43): write_log_append(), activateForeignObjectPanel(), btnCreateModel, btnDeleteModel, btnDetectObject, btnExitForeignObject, btnRunModel, btnRuntimeImages (+35 more)

### Community 19 - "PointService"
Cohesion: 0.05
Nodes (3): Result, PointService, test_point_service()

### Community 21 - "pathlib"
Cohesion: 0.09
Nodes (7): ErrorCode, AnomalyPointPatchCoreService, PatchCoreInspectionService, PatchCoreTrainRecordRepository, _FakeWorker, main(), test_run_patchcore_train_record_service()

### Community 22 - "numpy"
Cohesion: 0.05
Nodes (19): ClassNameForeignObjectConfig, ClassNameObjectStructureDetectConfig, YoloDetectObjectConfig, TypeDataSendClient, TypeSend, ModelYoloObject, build_yolo_model(), main() (+11 more)

### Community 23 - "test_anti_blur_logic.py"
Cohesion: 0.09
Nodes (8): AntiBlurService, calculate_anti_blur_timers(), get_anti_blur_config(), get_anti_blur_defaults(), reload_features_config(), save_anti_blur_config(), TestAntiBlurConfigCache, TestAntiBlurFormulas

### Community 24 - "FastAPI"
Cohesion: 0.13
Nodes (8): create_container(), create_app(), lifespan(), data_home(), reset_product_count(), connect(), disconnect(), log_sender()

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
Cohesion: 0.07
Nodes (56): cameraConfigButton, cameraConfigFields, cameraConfigLog, cameraConfigPanel, openCameraConfigPanel(), renderCameraConfig(), requestCameraConfig(), anonymous (+48 more)

### Community 30 - "trainler.py"
Cohesion: 0.08
Nodes (9): PatchCoreTrainConfig, main(), test_patchcore_train_record_service_logic(), _create_roi_dataset(), main(), test_trainler_patchcore_logic(), _crop_image(), main() (+1 more)

### Community 31 - "test_product_service.py"
Cohesion: 0.07
Nodes (9): Product, add_product(), print_result(), test_add_roi_image(), test_delete_product(), test_get_all_products(), test_get_arr_path_img_roi_product_by_id(), test_get_product() (+1 more)

### Community 32 - "ModelUnet"
Cohesion: 0.09
Nodes (5): UnetConfig, ModelUnet, crop_img(), get_touching_boundary_boxes(), main()

### Community 34 - "MotionSimulator"
Cohesion: 0.14
Nodes (3): MotionSimulator, CommandParser, StateEnum

### Community 35 - "handler_work_detect.py"
Cohesion: 0.09
Nodes (3): ProductAggregator, ModelHandler, HandlerWorkDetect

### Community 36 - "api_captureproduct.py"
Cohesion: 0.09
Nodes (11): Line, BaseAI, camera_ws(), exit(), PointData, robot_home(), robot_reset(), robot_stop() (+3 more)

### Community 37 - "ocr_tool.js"
Cohesion: 0.10
Nodes (21): choose_product, close_choose_product, container, overlay_choose_product, HEIGH_IMG_SHAPE, btn_out_app, boxContentOCR, obj_region_ocr_canvas (+13 more)

### Community 38 - "RectangleDrawer"
Cohesion: 0.17
Nodes (3): LineDrawer, drawTransparentLine(), isPointOnLineSegment()

### Community 39 - "FaceModelPatchCore"
Cohesion: 0.05
Nodes (7): FacePatchCoreObjectDetector, FaceModelPatchCore, FaceModelYoloObject, main(), test_get_bounding_boxes_crops_roi_and_restores_coordinates(), test_predict_crops_roi_before_model_call(), test_rejects_invalid_roi()

### Community 40 - "JudgmentResult"
Cohesion: 0.06
Nodes (7): StampAlignmentService, BaseJudgerAI, JudgmentResult, StampAlignmentDetector, StampDetector, create_recording_inspector(), judge()

### Community 41 - "add_new_product.js"
Cohesion: 0.13
Nodes (16): add_product, btn_cancel_delete, btn_confirm_delete, close_add_product, close_right_panel, createDataShowTable(), form_add_new_product, imageInput (+8 more)

### Community 42 - "cv2"
Cohesion: 0.07
Nodes (19): compute_skew_angle_deg(), crop_text_region(), order_quad_points(), read_image_unicode(), restore_upright_image(), create_base_industrial_label(), create_mixed_orientation_label(), create_symmetric_edgecase_180_label() (+11 more)

### Community 46 - "cnd_lybrary.js"
Cohesion: 0.15
Nodes (21): a(), i(), At(), c(), e(), Et(), f(), ft() (+13 more)

### Community 47 - "IAIConfig"
Cohesion: 0.09
Nodes (5): BaseConfig, IAIConfig, IAIService, TestStage2AntiBlurIntegration, main()

### Community 48 - "app_demorobot/ui/main_window.py"
Cohesion: 0.11
Nodes (4): main(), CommandHistoryTable, LogViewerWidget, TowerLightWidget

### Community 50 - "StructureFaceYoloService"
Cohesion: 0.10
Nodes (3): StructureFaceYoloService, FakeStampFrameModel, TestStampDetector

### Community 51 - "barcode_tool.js"
Cohesion: 0.10
Nodes (34): closeButton, event_transition_items(), getInspector(), logBarcode, openRectangleEditor(), originalOnClick, removeStoredRectangle(), runButton (+26 more)

### Community 52 - "repository/__init__.py"
Cohesion: 0.17
Nodes (6): ChooseProductRepository, PointRepository, print_result(), test_get_choose_product(), test_reset_choose_product(), test_set_choose_product_valid()

### Community 53 - "common_value.js"
Cohesion: 0.09
Nodes (19): canvasManager, get_com_connection, scroll_container, set_com_connection, videoManager, WIDTH_IMG_SHAPE, VideoManager, SocketModel (+11 more)

### Community 54 - "OCRService"
Cohesion: 0.17
Nodes (3): VisualizationService, OCRWorkerThread, evaluate_all()

### Community 55 - "qr_tool.js"
Cohesion: 0.18
Nodes (14): additional_events, boxContentQR, obj_region_qr_canvas, panner_region_qr, closeButton, event_transition_items(), getInspector(), logQR (+6 more)

### Community 58 - "ocr_service.py"
Cohesion: 0.16
Nodes (3): InspectionJudgement, OrientationStatus, OrientationService

### Community 61 - "OCRService"
Cohesion: 0.13
Nodes (5): save_image_unicode(), main(), run_cli_inspection(), OCRService, MainWindow

### Community 62 - "RuntimeState"
Cohesion: 0.08
Nodes (3): AppContext, RuntimePipelineState, RuntimeState

### Community 63 - ".inspect_image"
Cohesion: 0.17
Nodes (3): DocumentOrientationInfo, OCRInspectionResult, TextLineResult

### Community 68 - "StageTransform"
Cohesion: 0.11
Nodes (5): EnumMode, StageTransform, StageExport, DummyPreparedProduct, TestStage2ReturnToFirstPoint

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
Cohesion: 0.17
Nodes (6): create_barcode_account(), CreateBarcodeAccountRequest, delete_barcode_account(), update_admin_info(), UpdateAdminRequest, validate_barcode()

### Community 89 - "OrientationEngine"
Cohesion: 0.11
Nodes (3): OrientationEngine, 2. Khảo sát & Lựa chọn Thư viện / Mô hình OCR, Lý do lựa chọn giải pháp kết hợp PaddleOCR Modular + Multi-Hypothesis Orientation Engine:

### Community 91 - "container.py"
Cohesion: 0.06
Nodes (8): ModeState, QueueConfig, _delayed_exit(), shutdown_system(), LogCleanupWorker, Log_Img, Manager_Log, Aggregate

### Community 92 - "dependencies.py"
Cohesion: 0.17
Nodes (7): get_services(), get_services_ws(), delete_preview(), erase_product(), get_product(), list_product(), select_product_new()

### Community 95 - "Project Standards — Python & Computer Vision"
Cohesion: 0.15
Nodes (12): 10. Kiểm thử & hoàn thiện, 11. Nguyên tắc kết thúc thay đổi, 1. Mục tiêu, 2. Quy tắc sửa đổi mã nguồn, 3. Python Coding Standards, 4. Kiến trúc và dữ liệu, 5. Graphify & phân tích kiến trúc, 6. Computer Vision & AI (+4 more)

### Community 101 - "PHẦN MỀM GIẢ LẬP PLC ROBOT (APP_DEMOROBOT)"
Cohesion: 0.17
Nodes (11): 1.1. Cấu hình Mạng TCP Socket, 1.2. Danh mục Lệnh từ PC gửi tới PLC (PC -> PLC), 1.3. Danh mục Phản hồi từ PLC trả về PC (PLC -> PC), 1. Bảng Đặc Tả Tập Lệnh & Giao Thức (Theo `Bang_Giao_Tiep_Robot_PLC_PROD4.xlsx`), 2. Cấu Trúc Thư Mục Dự Án, 3.1. Khởi động Giao diện Giả lập PLC, 3.2. Chạy Kiểm thử Tự động (Unit Tests & Socket Integration Tests), 3. Hướng Dẫn Cài Đặt & Khởi Động (+3 more)

### Community 108 - "stamp_alignment_tool.js"
Cohesion: 0.18
Nodes (15): boxContentStampAlignment, COLOR_RECT_SHAPE_REGION_DETECT, obj_region_stamp_alignment_canvas, panner_region_stamp_alignment, closeButton, createConfigRow(), event_transition_items(), getInspector() (+7 more)

### Community 109 - "TrainWorkerPatchCore"
Cohesion: 0.13
Nodes (3): TrainWorkerPatchCore, main(), test_run_train_worker_patchcore_runtime()

### Community 111 - "ModelYoloOBB"
Cohesion: 0.13
Nodes (10): inspect_stamp_alignment(), ModelYoloOBB, normalize_obb(), process_yolo_obb_result(), test_inspect_stamp_alignment_containment_violation(), test_inspect_stamp_alignment_exceed_angle(), test_inspect_stamp_alignment_exceed_du(), test_inspect_stamp_alignment_perfect() (+2 more)

### Community 115 - "Hệ Thống OCR Nhận Diện Nội Dung & Xác Định Hướng Chữ Công Nghiệp (`app_demo_ocr_reverses`)"
Cohesion: 0.20
Nodes (9): 1. Tổng quan & Mục tiêu, 3. Cấu trúc Source Code (OOP), 4. Hướng dẫn Cài đặt & Khởi chạy, 5. Định dạng JSON Kết quả Đầu ra, A. Kích hoạt môi trường ảo (`.venv`), B. Khởi chạy Giao diện Đồ họa (PySide6 GUI), C. Kiểm tra ảnh bất kỳ bằng dòng lệnh (CLI Mode), D. Tái tạo bộ ảnh kiểm thử và chạy Benchmark đánh giá (+1 more)

### Community 117 - "get"
Cohesion: 0.14
Nodes (7): browse_log_dir(), browse_output_dir(), get_ai_model_paths(), get_config_logs(), software_information(), software_version(), update_config_logs()

### Community 122 - "MultiRegionDetectorTests"
Cohesion: 0.25
Nodes (3): config_region(), MultiRegionDetectorTests, region()

### Community 126 - "FakePointService"
Cohesion: 0.29
Nodes (3): FakeColorService, FakePointService, TestColorAPI

### Community 131 - "camera_status"
Cohesion: 0.32
Nodes (3): camera_status(), exit_camera_config(), get_camera_config()

### Community 167 - "home"
Cohesion: 0.20
Nodes (3): get_hardware_status(), get_product_count(), home()

### Community 168 - "FakeStampAlignmentService"
Cohesion: 0.25
Nodes (3): FakePointService, FakeStampAlignmentService, TestStampAlignmentAPI

### Community 170 - "test_train_worker_patchcore.py"
Cohesion: 0.22
Nodes (3): FakeTrainer, main(), test_train_worker_waits_for_required_images()

### Community 171 - "FakeOCRDetector"
Cohesion: 0.25
Nodes (3): FakeOCRDetector, FakePointService, TestOCRAPI

### Community 175 - "ServiceContainer"
Cohesion: 0.08
Nodes (29): ServiceContainer, capture(), captureproduct_load(), erase_frame(), erase_item_img(), anomaly_point_runtime_images(), anomaly_point_train_status(), create_anomaly_point_model() (+21 more)

### Community 177 - "test_crop.py"
Cohesion: 0.38
Nodes (3): center_to_box(), crop_image(), main()

### Community 178 - "api_draw_regulations.py"
Cohesion: 0.40
Nodes (3): accept_data(), draw_regulations(), exit()

## Knowledge Gaps
- **111 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Config_SoftWare` connect `Config_SoftWare` to `.read_json_from_file`, `StageTransform`, `InspectionTaskItem`, `JudgmentResult`, `cv2`, `Judment`, `.test_config_software_max_workers_validation`, `.cleanup_now`, `.run`, `get`, `.test_manager_log_pipeline_integration`, `container.py`, `Change_Disk`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `ServiceContainer` (e.g. with `RobotConfig` and `RuntimeState`) actually correct?**
  _`ServiceContainer` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Should `TrainlerPatchCore` be split into smaller, more focused modules?**
  _Cohesion score 0.12318840579710146 - nodes in this community are weakly interconnected._
- **Why does `IAIControl` connect `IAIControl` to `.stop`, `.move_to_point`, `JudgmentResult`, `._handle_single_input_message`, `.send_log_html`, `.send_command_stm32`, `ServiceContainer`, `IAIConfig`, `.start_thread_handl_request_stm32`, `container.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Config_SoftWare` (e.g. with `Judment` and `get_config_logs()`) actually correct?**
  _`Config_SoftWare` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `summary_tool.js` be split into smaller, more focused modules?**
  _Cohesion score 0.05723905723905724 - nodes in this community are weakly interconnected._
- **Why does `StageTransform` connect `StageTransform` to `Config_SoftWare`, `InspectionTaskItem`, `._save_judgment_result`, `ServiceContainer`, `IAIConfig`, `.run`, `TestStorageOptimization`, `._strip_internal_images`, `test_anti_blur_logic.py`, `TestStage2PipelinedQueue`, `Pipeline`, `container.py`, `RuntimeState`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._