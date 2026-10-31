import json
from pathlib import Path
from typing import Optional
import cv2
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import (
    InspectionJudgement,
    OrientationStatus,
    STATUS_LABELS_VI,
)
from app.core.geometry import read_image_unicode, save_image_unicode
from app.schemas.ocr_schema import OCRInspectionResult
from app.services.ocr_service import OCRService
from app.services.visualization_service import VisualizationService
from config import PROJECT_ROOT


class OCRWorkerThread(QThread):
    """Background worker thread for running OCR & Orientation inspection without freezing the UI."""

    finished_signal = Signal(object, object, object)
    error_signal = Signal(str)

    def __init__(self, ocr_service: OCRService, image_path: Path) -> None:
        super().__init__()
        self.ocr_service = ocr_service
        self.image_path = image_path

    def run(self) -> None:
        try:
            result, raw_bgr = self.ocr_service.inspect_image(self.image_path)
            vis_bgr = None
            if raw_bgr is not None:
                vis_bgr = VisualizationService.draw_inspection_result(
                    raw_bgr, result
                )
            self.finished_signal.emit(result, raw_bgr, vis_bgr)
        except Exception as exc:
            self.error_signal.emit(str(exc))


class ScalableImageLabel(QLabel):
    """QLabel that smoothly scales its QPixmap while preserving aspect ratio."""

    def __init__(self, placeholder_text: str = "") -> None:
        super().__init__(placeholder_text)
        self._pixmap: Optional[QPixmap] = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 260)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.setStyleSheet(
            "QLabel { background-color: #111827; color: #9CA3AF; "
            "border: 1px solid #374151; border-radius: 6px; font-size: 13px; }"
        )

    def set_cv_image(self, bgr_img: np.ndarray) -> None:
        rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(
            rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
        ).copy()
        self._pixmap = QPixmap.fromImage(qimg)
        self._update_scaled()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_scaled()

    def _update_scaled(self) -> None:
        if self._pixmap is not None and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            super().setPixmap(scaled)


class MainWindow(QMainWindow):
    """Main Desktop GUI Window for Industrial Label OCR & Orientation Inspection."""

    def __init__(self, ocr_service: OCRService) -> None:
        super().__init__()
        self.ocr_service = ocr_service
        self.current_image_path: Optional[Path] = None
        self.current_result: Optional[OCRInspectionResult] = None
        self.current_vis_bgr: Optional[np.ndarray] = None
        self.worker: Optional[OCRWorkerThread] = None

        self.setWindowTitle(
            "Industrial OCR & Orientation Inspector (0° | 90° | 180° | 270° | Mirror)"
        )
        self.resize(1520, 900)
        self._setup_ui()
        self._populate_sample_images()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 1. Top Control Bar
        top_bar = QFrame()
        top_bar.setStyleSheet(
            "QFrame { background-color: #1F2937; border-radius: 6px; padding: 6px; }"
        )
        top_layout = QHBoxLayout(top_bar)

        self.btn_open = QPushButton("📂 Chọn ảnh từ máy tính...")
        self.btn_open.setStyleSheet(
            "QPushButton { background-color: #2563EB; color: white; font-weight: bold; "
            "padding: 8px 16px; border-radius: 5px; font-size: 13px; }"
            "QPushButton:hover { background-color: #1D4ED8; }"
        )
        self.btn_open.clicked.connect(self._on_browse_image)

        lbl_sample = QLabel("Ảnh kiểm thử mẫu:")
        lbl_sample.setStyleSheet("color: #E5E7EB; font-weight: bold;")
        self.combo_samples = QComboBox()
        self.combo_samples.setMinimumWidth(290)
        self.combo_samples.setStyleSheet(
            "QComboBox { background-color: #374151; color: white; padding: 6px; border-radius: 4px; }"
        )
        self.combo_samples.currentIndexChanged.connect(self._on_sample_selected)

        self.btn_run = QPushButton("▶ Chạy nhận diện OCR & Kiểm tra hướng")
        self.btn_run.setStyleSheet(
            "QPushButton { background-color: #059669; color: white; font-weight: bold; "
            "padding: 8px 18px; border-radius: 5px; font-size: 13px; }"
            "QPushButton:hover { background-color: #047857; }"
        )
        self.btn_run.clicked.connect(self._on_run_inspection)

        self.btn_export = QPushButton("💾 Lưu kết quả (JSON + Ảnh)")
        self.btn_export.setStyleSheet(
            "QPushButton { background-color: #4B5563; color: white; font-weight: bold; "
            "padding: 8px 14px; border-radius: 5px; font-size: 13px; }"
            "QPushButton:hover { background-color: #374151; }"
        )
        self.btn_export.clicked.connect(self._on_export_result)

        self.lbl_path = QLabel("Chưa chọn ảnh")
        self.lbl_path.setStyleSheet("color: #9CA3AF; font-size: 12px;")

        top_layout.addWidget(self.btn_open)
        top_layout.addSpacing(8)
        top_layout.addWidget(lbl_sample)
        top_layout.addWidget(self.combo_samples)
        top_layout.addSpacing(8)
        top_layout.addWidget(self.btn_run)
        top_layout.addWidget(self.btn_export)
        top_layout.addStretch()
        top_layout.addWidget(self.lbl_path)

        main_layout.addWidget(top_bar)

        # 2. Main Splitter: Left (Original + Result Images) | Right (Inspection Details)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Image Splitter (Original vs OCR Annotated)
        img_splitter = QSplitter(Qt.Orientation.Horizontal)

        orig_group = QGroupBox("1. Ảnh gốc ban đầu (Original Image - Chưa xoay)")
        orig_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        orig_layout = QVBoxLayout(orig_group)
        self.lbl_img_orig = ScalableImageLabel("Chọn ảnh để hiển thị ảnh gốc")
        orig_layout.addWidget(self.lbl_img_orig)

        res_group = QGroupBox(
            "2. Ảnh kết quả OCR & Hướng chữ (Bounding Box trên hệ tọa độ gốc)"
        )
        res_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        res_layout = QVBoxLayout(res_group)
        self.lbl_img_res = ScalableImageLabel(
            "Nhấn 'Chạy nhận diện OCR' để xem kết quả"
        )
        res_layout.addWidget(self.lbl_img_res)

        img_splitter.addWidget(orig_group)
        img_splitter.addWidget(res_group)
        img_splitter.setSizes([460, 480])

        # Right Panel: Judgement Banner + Orientation Metrics + Table/JSON Tabs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Big Judgement Banner
        self.lbl_judgement = QLabel("TRẠNG THÁI: CHỜ KIỂM TRA")
        self.lbl_judgement.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_judgement.setFixedHeight(64)
        self.lbl_judgement.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.lbl_judgement.setStyleSheet(
            "background-color: #374151; color: white; border-radius: 6px; padding: 8px;"
        )
        right_layout.addWidget(self.lbl_judgement)

        # Summary Metrics Card
        summary_group = QGroupBox("Thông tin Hướng ảnh gốc & Đánh giá")
        summary_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        grid = QGridLayout(summary_group)

        self.val_angle = QLabel("-")
        self.val_status = QLabel("-")
        self.val_mirror = QLabel("-")
        self.val_skew = QLabel("-")
        self.val_conf = QLabel("-")
        self.val_doc_ori = QLabel("-")
        self.val_lines = QLabel("-")
        self.val_time = QLabel("-")
        self.val_reason = QLabel("-")
        self.val_reason.setWordWrap(True)

        for lbl in [
            self.val_angle,
            self.val_status,
            self.val_mirror,
            self.val_skew,
            self.val_conf,
            self.val_doc_ori,
            self.val_lines,
            self.val_time,
        ]:
            lbl.setStyleSheet("font-weight: bold; color: #111827;")

        grid.addWidget(QLabel("Góc xoay chữ (Angle):"), 0, 0)
        grid.addWidget(self.val_angle, 0, 1)
        grid.addWidget(QLabel("Trạng thái hướng (Status):"), 0, 2)
        grid.addWidget(self.val_status, 0, 3)

        grid.addWidget(QLabel("Lật gương (Mirror):"), 1, 0)
        grid.addWidget(self.val_mirror, 1, 1)
        grid.addWidget(QLabel("Góc nghiêng phối cảnh (Skew):"), 1, 2)
        grid.addWidget(self.val_skew, 1, 3)

        grid.addWidget(QLabel("Confidence hướng:"), 2, 0)
        grid.addWidget(self.val_conf, 2, 1)
        grid.addWidget(QLabel("Doc-Ori Model:"), 2, 2)
        grid.addWidget(self.val_doc_ori, 2, 3)

        grid.addWidget(QLabel("Tổng số dòng chữ:"), 3, 0)
        grid.addWidget(self.val_lines, 3, 1)
        grid.addWidget(QLabel("Thời gian xử lý:"), 3, 2)
        grid.addWidget(self.val_time, 3, 3)

        grid.addWidget(QLabel("Kết luận chi tiết:"), 4, 0)
        grid.addWidget(self.val_reason, 4, 1, 1, 3)

        right_layout.addWidget(summary_group)

        # Tabs: Per-Line Table & JSON Output
        tabs = QTabWidget()
        self.table_lines = QTableWidget(0, 7)
        self.table_lines.setHorizontalHeaderLabels(
            [
                "#",
                "Nội dung chữ (Text)",
                "Conf",
                "Góc (Angle)",
                "Trạng thái",
                "Skew (°)",
                "BBox [x1, y1, x2, y2]",
            ]
        )
        header = self.table_lines.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.txt_json = QPlainTextEdit()
        self.txt_json.setReadOnly(True)
        self.txt_json.setFont(QFont("Consolas", 10))
        self.txt_json.setStyleSheet(
            "background-color: #111827; color: #10B981; border-radius: 4px;"
        )

        tabs.addTab(self.table_lines, "📋 Danh sách từng dòng chữ")
        tabs.addTab(self.txt_json, "{ } Kết quả JSON chuẩn")
        right_layout.addWidget(tabs)

        main_splitter.addWidget(img_splitter)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([940, 560])

        main_layout.addWidget(main_splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sẵn sàng kiểm tra ảnh OCR & Hướng chữ.")

    def _populate_sample_images(self) -> None:
        test_dir = PROJECT_ROOT / "data" / "test_images"
        self.combo_samples.blockSignals(True)
        self.combo_samples.clear()
        self.combo_samples.addItem("-- Chọn ảnh mẫu trong data/test_images --", None)
        if test_dir.exists():
            files = sorted(
                [
                    p
                    for p in test_dir.iterdir()
                    if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")
                ]
            )
            for p in files:
                self.combo_samples.addItem(p.name, str(p))
        self.combo_samples.blockSignals(False)

    def _on_sample_selected(self, index: int) -> None:
        path_str = self.combo_samples.itemData(index)
        if path_str:
            self.load_and_inspect(Path(path_str))

    def _on_browse_image(self) -> None:
        initial_dir = str(PROJECT_ROOT / "data" / "test_images")
        if not Path(initial_dir).exists():
            initial_dir = str(PROJECT_ROOT)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn ảnh tem cần kiểm tra OCR & Hướng chữ",
            initial_dir,
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)",
        )
        if file_path:
            self.load_and_inspect(Path(file_path))

    def load_and_inspect(self, image_path: Path) -> None:
        if not image_path.exists():
            QMessageBox.warning(
                self, "Không tìm thấy file", f"File không tồn tại:\n{image_path}"
            )
            return

        self.current_image_path = image_path
        self.lbl_path.setText(str(image_path))
        try:
            raw_bgr = read_image_unicode(image_path)
            self.lbl_img_orig.set_cv_image(raw_bgr)
        except Exception as exc:
            QMessageBox.critical(
                self, "Lỗi đọc ảnh", f"Không thể đọc ảnh:\n{exc}"
            )
            return

        self._on_run_inspection()

    def _on_run_inspection(self) -> None:
        if self.current_image_path is None:
            QMessageBox.information(
                self, "Chưa chọn ảnh", "Vui lòng chọn một ảnh trước khi chạy kiểm tra."
            )
            return

        self.btn_run.setEnabled(False)
        self.btn_open.setEnabled(False)
        self.lbl_judgement.setText("⏳ ĐANG XỬ LÝ OCR & PHÂN TÍCH HƯỚNG CHỮ...")
        self.lbl_judgement.setStyleSheet(
            "background-color: #D97706; color: white; border-radius: 6px; padding: 8px;"
        )
        self.status_bar.showMessage(
            f"Đang chạy nhận diện trên {self.current_image_path.name}..."
        )

        self.worker = OCRWorkerThread(self.ocr_service, self.current_image_path)
        self.worker.finished_signal.connect(self._on_inspection_finished)
        self.worker.error_signal.connect(self._on_inspection_error)
        self.worker.start()

    def _on_inspection_error(self, err_msg: str) -> None:
        self.btn_run.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.lbl_judgement.setText("❌ LỖI XỬ LÝ")
        self.lbl_judgement.setStyleSheet(
            "background-color: #DC2626; color: white; border-radius: 6px; padding: 8px;"
        )
        QMessageBox.critical(self, "Lỗi OCR", err_msg)

    def _on_inspection_finished(
        self,
        result: OCRInspectionResult,
        raw_bgr: Optional[np.ndarray],
        vis_bgr: Optional[np.ndarray],
    ) -> None:
        self.btn_run.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.current_result = result
        self.current_vis_bgr = vis_bgr

        if vis_bgr is not None:
            self.lbl_img_res.set_cv_image(vis_bgr)

        ori = result.orientation
        is_ok = result.result == InspectionJudgement.OK.value
        vi_status = STATUS_LABELS_VI.get(ori.status, ori.status)

        if is_ok:
            self.lbl_judgement.setText(
                f"✅ KẾT LUẬN: OK — {vi_status.upper()}"
            )
            self.lbl_judgement.setStyleSheet(
                "background-color: #15803D; color: white; border-radius: 6px; padding: 8px;"
            )
        else:
            self.lbl_judgement.setText(
                f"🚨 KẾT LUẬN: NG — {vi_status.upper()}"
            )
            self.lbl_judgement.setStyleSheet(
                "background-color: #B91C1C; color: white; border-radius: 6px; padding: 8px;"
            )

        self.val_angle.setText(f"{ori.angle}°")
        self.val_status.setText(f"{ori.status} ({vi_status})")
        self.val_mirror.setText(
            "CÓ (Lật gương trái-phải)" if ori.is_mirrored else "Không"
        )
        self.val_skew.setText(
            f"{ori.skew_angle:+.2f}° {'(Nghiêng)' if ori.is_tilted else '(Chuẩn)'}"
        )
        self.val_conf.setText(f"{ori.confidence:.4f}")
        self.val_doc_ori.setText(
            f"{ori.doc_model_angle}° ({ori.doc_model_confidence:.3f})"
        )
        self.val_lines.setText(str(result.total_lines))
        self.val_time.setText(f"{result.processing_time_ms:.1f} ms")
        self.val_reason.setText(result.reason)

        # Populate table
        self.table_lines.setRowCount(len(result.texts))
        for row_idx, line in enumerate(result.texts):
            angle_disp = "MIRROR" if line.is_mirrored else f"{line.angle}°"
            items = [
                str(line.line_id + 1),
                line.text,
                f"{line.confidence:.4f}",
                angle_disp,
                line.orientation_status,
                f"{line.skew_angle:+.1f}°",
                str(line.bbox),
            ]
            row_bg = (
                QColor("#DCFCE7")
                if line.orientation_status == OrientationStatus.NORMAL.value
                else QColor("#FEE2E2")
            )
            for col_idx, val in enumerate(items):
                cell = QTableWidgetItem(val)
                cell.setBackground(row_bg)
                cell.setForeground(QColor("#111827"))
                self.table_lines.setItem(row_idx, col_idx, cell)

        # Populate JSON viewer
        json_str = json.dumps(
            result.to_compact_dict(), ensure_ascii=False, indent=4
        )
        self.txt_json.setPlainText(json_str)
        self.status_bar.showMessage(
            f"Hoàn tất kiểm tra {result.image} trong {result.processing_time_ms:.1f} ms — Kết quả: {result.result}"
        )

    def _on_export_result(self) -> None:
        if self.current_result is None:
            QMessageBox.information(
                self, "Chưa có kết quả", "Hãy chạy kiểm tra OCR trước khi lưu."
            )
            return

        out_dir = PROJECT_ROOT / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(self.current_result.image).stem

        json_path = out_dir / f"{stem}_result.json"
        img_path = out_dir / f"{stem}_annotated.png"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                self.current_result.to_compact_dict(),
                f,
                ensure_ascii=False,
                indent=4,
            )

        if self.current_vis_bgr is not None:
            save_image_unicode(img_path, self.current_vis_bgr)

        QMessageBox.information(
            self,
            "Đã lưu kết quả",
            f"Đã xuất kết quả thành công:\n- JSON: {json_path}\n- Ảnh: {img_path}",
        )
