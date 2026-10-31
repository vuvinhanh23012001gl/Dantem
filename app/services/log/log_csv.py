import csv
from datetime import datetime
from pathlib import Path
import threading
import logging
from typing import Any

# Header file CSV Tổng nội dung (Ảnh 1)
SUMMARY_DAILY_HEADER = [
    "Time",
    "Product",
    "Session",
    "OK/NG",
    "Tỷ lệ phán định",
    "Message",
]

# Header file CSV Session chi tiết (Ảnh 2)
SESSION_DETAIL_HEADER = [
    "timestamp",
    "product_id",
    "product_name",
    "frame_id",
    "item_id",
    "overall_status",
    # 1. Đường hàn (Weld)
    "weld_status",
    "Theory",
    "Reality",
    "message",
    # 2. Cảm biến ARM (Arm Sensor)
    "status_arm_sensor",
    "Theory",
    "Reality",
    "message",
    # 3. Nắp ARM (Arm Cover)
    "status_arm_cover",
    "Theory",
    "Reality",
    "message",
    # 4. Lỗ định vị (Hole)
    "status_hole",
    "Theory",
    "Reality",
    "message",
    # 6. Khe rãnh màng (Slit)
    "status_slit",
    "Theory",
    "Reality",
    "message",
    # 7. Dị vật (Foreign Object)
    "status_foreign_object",
    "Theory",
    "Reality",
    "message",
    # 8. Điểm bất thường (Anomaly Point)
    "status_anomaly_point",
    "Theory",
    "Reality",
    "message",
    # 9. Kiểm tra Có/Không tem (Stamp)
    "status_stamp",
    "Theory",
    "Reality",
    "message",
    # Tên ảnh trong Log_img
    "Ảnh item",
]


class Log_CSV:
    """Quản lý ghi log kết quả phán định ra file CSV chuẩn công nghiệp:
    1. File CSV tổng nội dung trong ngày (summary_daily.csv) theo định dạng Ảnh 1.
    2. File CSV session chi tiết theo từng hạng mục kiểm tra (session/{session_id}.csv) theo Ảnh 2.
    3. Hỗ trợ ghi tương thích ngược thông qua write().
    """

    def __init__(
        self,
        folder: str | Path,
        filename: str | None = None,
        header: list[str] | None = None,
        enable: bool = True,
        auto_timestamp: bool = True,
        daily_rolling: bool = True,
        time_format: str = "%Y-%m-%d %H:%M:%S",
    ):
        self.enable = enable
        self.auto_timestamp = auto_timestamp
        self.daily_rolling = daily_rolling
        self.time_format = time_format
        self.lock = threading.Lock()

        self.path_folder = Path(folder)
        self.filename = filename

        self.header = list(header) if header else list(SESSION_DETAIL_HEADER)
        self.summary_header = list(SUMMARY_DAILY_HEADER)
        self.session_header = list(SESSION_DETAIL_HEADER)

    def _ensure_file_initialized(self, target_path: Path, header_columns: list[str]) -> None:
        """Đảm bảo thư mục và tiêu đề header BOM UTF-8-SIG của file CSV tồn tại."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if not target_path.exists() or target_path.stat().st_size == 0:
            with open(target_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(header_columns)

    def write_summary(self, data: dict[str, Any], custom_file_path: Path | str | None = None) -> Path | None:
        """Ghi 1 dòng tổng kết phiên phán định vào file CSV tổng nội dung (Ảnh 1).
        Cột: Time | Product | Session | OK/NG | Tỷ lệ phán định | Message
        """
        if not self.enable:
            return None

        time_val = data.get("Time") or data.get("timestamp") or datetime.now().strftime(self.time_format)
        product_val = data.get("Product") or data.get("product_name") or ""
        session_val = data.get("Session") or data.get("session_id") or ""
        status_val = data.get("OK/NG") or data.get("overall_status") or data.get("status") or "NA"
        rate_val = data.get("Tỷ lệ phán định") or data.get("pass_rate") or ""
        msg_val = data.get("Message") or data.get("message") or ""

        row = [time_val, product_val, session_val, status_val, rate_val, msg_val]

        target_file = Path(custom_file_path) if custom_file_path else self.path_folder / "summary_daily.csv"
        with self.lock:
            self._ensure_file_initialized(target_file, self.summary_header)
            with open(target_file, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(row)

        return target_file

    def write_session_item(
        self,
        session_id: str,
        item_data: dict[str, Any],
        custom_file_path: Path | str | None = None,
    ) -> Path | None:
        """Ghi chi tiết 1 item/point vào file CSV session theo từng hạng mục (Ảnh 2)."""
        if not self.enable:
            return None

        def _resolve_category(status_val: Any, theory_val: Any, reality_val: Any, msg_val: Any) -> tuple[str, str, str, str]:
            status_str = str(status_val).strip() if status_val is not None else "NA"
            if not status_str or status_str in ("NA", "None"):
                return "NA", "NA", "N/A", "NA"
            theory_str = str(theory_val).strip() if theory_val is not None else "NA"
            reality_str = str(reality_val).strip() if reality_val is not None else "N/A"
            msg_str = str(msg_val).strip() if msg_val is not None else "NA"
            return (
                status_str,
                theory_str if theory_str else "NA",
                reality_str if reality_str else "N/A",
                msg_str if msg_str else "NA",
            )

        timestamp = item_data.get("timestamp") or datetime.now().strftime(self.time_format)

        weld_status, weld_theory, weld_reality, weld_msg = _resolve_category(
            item_data.get("weld_status"),
            item_data.get("weld_theory"),
            item_data.get("weld_reality"),
            item_data.get("weld_message"),
        )
        sensor_status, sensor_theory, sensor_reality, sensor_msg = _resolve_category(
            item_data.get("status_arm_sensor", item_data.get("arm_sensor_status")),
            item_data.get("arm_sensor_theory"),
            item_data.get("arm_sensor_reality"),
            item_data.get("arm_sensor_message"),
        )
        cover_status, cover_theory, cover_reality, cover_msg = _resolve_category(
            item_data.get("status_arm_cover", item_data.get("arm_cover_status")),
            item_data.get("arm_cover_theory"),
            item_data.get("arm_cover_reality"),
            item_data.get("arm_cover_message"),
        )
        hole_status, hole_theory, hole_reality, hole_msg = _resolve_category(
            item_data.get("status_hole", item_data.get("hole_status")),
            item_data.get("hole_theory"),
            item_data.get("hole_reality"),
            item_data.get("hole_message"),
        )
        slit_status, slit_theory, slit_reality, slit_msg = _resolve_category(
            item_data.get("status_slit", item_data.get("slit_status")),
            item_data.get("slit_theory"),
            item_data.get("slit_reality"),
            item_data.get("slit_message"),
        )
        foreign_status, foreign_theory, foreign_reality, foreign_msg = _resolve_category(
            item_data.get("status_foreign_object", item_data.get("foreign_object_status")),
            item_data.get("foreign_theory"),
            item_data.get("foreign_reality"),
            item_data.get("foreign_message"),
        )
        anomaly_status, anomaly_theory, anomaly_reality, anomaly_msg = _resolve_category(
            item_data.get(
                "status_anomaly_point",
                item_data.get("anomaly_point_status"),
            ),
            item_data.get("anomaly_theory"),
            item_data.get("anomaly_reality"),
            item_data.get("anomaly_message"),
        )
        stamp_status, stamp_theory, stamp_reality, stamp_msg = _resolve_category(
            item_data.get("status_stamp", item_data.get("stamp_status")),
            item_data.get("stamp_theory"),
            item_data.get("stamp_reality"),
            item_data.get("stamp_message"),
        )

        row = [
            timestamp,
            item_data.get("product_id", ""),
            item_data.get("product_name", ""),
            item_data.get("frame_id", ""),
            item_data.get("item_id", ""),
            item_data.get("overall_status", "NA"),
            # 1. Weld
            weld_status,
            weld_theory,
            weld_reality,
            weld_msg,
            # 2. Arm Sensor
            sensor_status,
            sensor_theory,
            sensor_reality,
            sensor_msg,
            # 3. Arm Cover
            cover_status,
            cover_theory,
            cover_reality,
            cover_msg,
            # 4. Hole
            hole_status,
            hole_theory,
            hole_reality,
            hole_msg,
            # 6. Slit
            slit_status,
            slit_theory,
            slit_reality,
            slit_msg,
            # 7. Foreign Object
            foreign_status,
            foreign_theory,
            foreign_reality,
            foreign_msg,
            # 8. Anomaly Point
            anomaly_status,
            anomaly_theory,
            anomaly_reality,
            anomaly_msg,
            # 9. Stamp
            stamp_status,
            stamp_theory,
            stamp_reality,
            stamp_msg,
            # Ảnh item (chỉ lưu tên file ảnh trong Log_img)
            item_data.get("image_name", item_data.get("image_path", "")),
        ]

        if custom_file_path:
            target_file = Path(custom_file_path)
        else:
            session_clean = str(session_id).strip().replace(" ", "_")
            target_file = self.path_folder / "session" / f"{session_clean}.csv"

        with self.lock:
            target_file = self._compatible_session_path(target_file)
            self._ensure_file_initialized(target_file, self.session_header)
            with open(target_file, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(row)

        return target_file

    def _compatible_session_path(self, target: Path) -> Path:
        for candidate in (target, target.with_name(f"{target.stem}_inspectors-v2{target.suffix}")):
            if not candidate.exists() or candidate.stat().st_size == 0:
                return candidate
            with candidate.open(newline="", encoding="utf-8-sig") as stream:
                if next(csv.reader(stream), []) == self.session_header:
                    return candidate
            logging.getLogger(__name__).warning("Giữ CSV khác schema, không ghi đè: %s", candidate)
        raise ValueError(f"CSV có schema không tương thích: {target}")

    def write(self, data: dict[str, Any], custom_file_path: Path | str | None = None) -> Path | None:
        """Phương thức ghi dữ liệu tương thích ngược:
        - Nếu data có 'Session' và 'Tỷ lệ phán định': điều hướng ghi summary
        - Nếu data có 'session_id' và 'item_id': điều hướng ghi session item
        - Nếu không: ghi vào file CSV mặc định theo self.header
        """
        if not self.enable:
            return None

        if "Tỷ lệ phán định" in data or ("Session" in data and "OK/NG" in data):
            return self.write_summary(data, custom_file_path)

        if "session_id" in data and "item_id" in data and (
            "weld_status" in data or "status_stamp" in data or "stamp_status" in data
        ):
            session_id = data.get("session_id", "default_session")
            return self.write_session_item(session_id, data, custom_file_path)

        # Fallback ghi row tự do
        row_data = dict(data)
        if self.auto_timestamp and "timestamp" not in row_data:
            row_data["timestamp"] = datetime.now().strftime(self.time_format)

        if custom_file_path:
            target_file = Path(custom_file_path)
        elif self.daily_rolling:
            today_str = datetime.now().strftime("%Y-%m-%d")
            target_file = self.path_folder / f"judgment_daily_{today_str}.csv"
        elif self.filename:
            target_file = self.path_folder / self.filename
        else:
            target_file = self.path_folder / "judgment_log.csv"

        row = [row_data.get(col, "") for col in self.header]
        with self.lock:
            self._ensure_file_initialized(target_file, self.header)
            with open(target_file, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(row)

        return target_file


# Alias để tương thích tên gọi
InspectionCsvLogger = Log_CSV
