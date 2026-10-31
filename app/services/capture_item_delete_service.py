from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import shutil
import uuid

from app.config import (
    BASE_DIR,
    PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST,
    PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST,
    PATH_FOLDER_IMG_COORDINATE_OUTPUT,
    PATH_FOLDER_IMG_COORDINATE_PRODUCT,
    PATH_FOLDER_MODEL_DETECT_PATCH_CORE,
)
from app.core import ErrorCode, Result
from app.engines.train.patchcore_train_model.patchcore_train_record_repository import (
    PatchCoreTrainRecordRepository,
)
from typing import Any, Optional
from app.services.judment_law_product_service import JudmentLawProductSevice
from app.services.point_service import PointService


@dataclass
class _MovedEntry:
    src: Path
    staged: Path


class CaptureItemDeleteService:
    def __init__(
        self,
        point_service: PointService,
        law_service: JudmentLawProductSevice,
        calibration_service: Optional[Any] = None,
    ):
        """
        Chức năng: Điều phối xóa item capture theo cơ chế strong-atomic có rollback.
        Input: point_service, law_service, calibration_service đã khởi tạo sẵn trong DI container.
        Output: Khởi tạo service với vùng staging transaction nội bộ.
        Errors: Không phát sinh ngoại lệ khi khởi tạo; thư mục staging được tạo nếu chưa tồn tại.
        """
        self.point_service = point_service
        self.law_service = law_service
        self.calibration_service = calibration_service
        self._base_dir = Path(BASE_DIR)
        self._staging_root = self._base_dir / "storage" / ".delete_item_txn"
        self._staging_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _prune_dir_if_empty(dir_path: Path, step_name: str) -> dict:
        """
        Chức năng: Xóa thư mục nếu rỗng và trả về log chi tiết cho technical report.
        Input: dir_path (Path), step_name (str).
        Output: dict trạng thái OK/NG với mô tả hành động.
        Errors: Trả trạng thái NG nếu gặp ngoại lệ khi truy cập hoặc xóa.
        """
        try:
            if not dir_path.exists():
                return {"step": step_name, "status": "OK", "detail": f"Không tồn tại: {dir_path}"}
            if not dir_path.is_dir():
                return {"step": step_name, "status": "NG", "detail": f"Không phải thư mục: {dir_path}"}
            if any(dir_path.iterdir()):
                return {"step": step_name, "status": "OK", "detail": f"Giữ nguyên vì chưa rỗng: {dir_path}"}
            dir_path.rmdir()
            return {"step": step_name, "status": "OK", "detail": f"Đã xóa thư mục rỗng: {dir_path}"}
        except Exception as error:
            return {"step": step_name, "status": "NG", "detail": f"Lỗi dọn thư mục {dir_path}: {error}"}

    def cleanup_empty_face_structure(self, product_id: int, face_id: int) -> Result:
        return self.cleanup_empty_frame_structure(product_id, face_id)

    def cleanup_empty_frame_structure(self, product_id: int, frame_id: int) -> Result:
        """
        Chức năng: Dọn cấu trúc thư mục frame/product nếu đã rỗng sau khi xóa dữ liệu item.
        Input: product_id (int), frame_id (int).
        Output: Result.Ok(dict) chứa technical_report nếu dọn dẹp thành công hoặc không cần dọn.
        Errors: Result.Fail(dict) nếu có ít nhất một bước dọn thư mục bị lỗi NG.
        """
        technical_report: list[dict] = []
        product_key = str(product_id)
        frame_key = str(frame_id)
        roots = [
            (Path(PATH_FOLDER_MODEL_DETECT_PATCH_CORE), "cleanup_patch_core"),
            (Path(PATH_FOLDER_IMG_COORDINATE_PRODUCT), "cleanup_img_points"),
            (Path(PATH_FOLDER_IMG_COORDINATE_OUTPUT), "cleanup_output_patch_core"),
        ]

        for root_path, label in roots:
            frame_dir = root_path / product_key / frame_key
            product_dir = root_path / product_key
            technical_report.append(
                self._prune_dir_if_empty(frame_dir, f"{label}_frame_dir")
            )
            technical_report.append(
                self._prune_dir_if_empty(product_dir, f"{label}_product_dir")
            )

        has_error = any(step.get("status") == "NG" for step in technical_report)
        if has_error:
            return Result.Fail(
                {
                    "error": "CLEANUP_EMPTY_FRAME_STRUCTURE_FAILED",
                    "technical_report": technical_report,
                }
            )
        return Result.Ok({"technical_report": technical_report})

    @staticmethod
    def _ok_step(step: str, detail: str) -> dict:
        """
        Chức năng: Tạo bản ghi thành công cho technical report.
        Input: step (str), detail (str).
        Output: dict chứa trạng thái OK.
        Errors: Không phát sinh.
        """
        return {"step": step, "status": "OK", "detail": detail}

    @staticmethod
    def _ng_step(step: str, detail: str) -> dict:
        """
        Chức năng: Tạo bản ghi thất bại cho technical report.
        Input: step (str), detail (str).
        Output: dict chứa trạng thái NG.
        Errors: Không phát sinh.
        """
        return {"step": step, "status": "NG", "detail": detail}

    def _safe_abs(self, relative_path: str | None) -> Path | None:
        """
        Chức năng: Chuẩn hóa đường dẫn tương đối theo BASE_DIR thành đường dẫn tuyệt đối an toàn.
        Input: relative_path (str | None).
        Output: Path tuyệt đối hoặc None nếu đầu vào rỗng.
        Errors: ValueError nếu path thoát ra ngoài BASE_DIR.
        """
        if not relative_path:
            return None
        candidate = (self._base_dir / str(relative_path)).resolve()
        candidate.relative_to(self._base_dir.resolve())
        return candidate

    def _stage_path(
        self,
        path_obj: Path | None,
        txn_dir: Path,
        moved_entries: list[_MovedEntry],
        report_steps: list[dict],
        step_name: str,
    ) -> None:
        """
        Chức năng: Stage file/folder sang thư mục transaction để hỗ trợ rollback.
        Input: path_obj, txn_dir, danh sách moved_entries/report và tên bước.
        Output: Cập nhật moved_entries/report; không trả về giá trị.
        Errors: RuntimeError nếu move thất bại hoặc đường dẫn không hợp lệ.
        """
        if path_obj is None:
            report_steps.append(self._ok_step(step_name, "Bỏ qua vì không có đường dẫn."))
            return
        if not path_obj.exists():
            report_steps.append(self._ok_step(step_name, f"Không tồn tại: {path_obj}"))
            return

        rel = path_obj.relative_to(self._base_dir.resolve())
        staged = txn_dir / rel
        staged.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path_obj), str(staged))
        moved_entries.append(_MovedEntry(src=path_obj, staged=staged))
        report_steps.append(self._ok_step(step_name, f"Đã stage: {path_obj}"))

    def _rollback(
        self,
        moved_entries: list[_MovedEntry],
        point_snapshot: dict,
        law_snapshot: dict,
        calibration_snapshot: Optional[dict],
        anomaly_manifest_snapshot: list[dict],
        foreign_manifest_snapshot: list[dict],
    ) -> list[dict]:
        """
        Chức năng: Khôi phục toàn bộ dữ liệu RAM/file và file-system đã stage khi transaction lỗi.
        Input: moved_entries + snapshot points/law/calibration/manifest.
        Output: Danh sách bước rollback để ghi technical report.
        Errors: Không ném lỗi; lỗi rollback được ghi trạng thái NG trong report.
        """
        rollback_steps: list[dict] = []

        for entry in reversed(moved_entries):
            try:
                if not entry.staged.exists():
                    rollback_steps.append(
                        self._ng_step(
                            "rollback_fs",
                            f"Thiếu staged path, không thể phục hồi: {entry.staged}",
                        )
                    )
                    continue
                entry.src.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(entry.staged), str(entry.src))
                rollback_steps.append(
                    self._ok_step("rollback_fs", f"Phục hồi: {entry.src}")
                )
            except Exception as error:
                rollback_steps.append(
                    self._ng_step("rollback_fs", f"Lỗi phục hồi {entry.src}: {error}")
                )

        try:
            self.point_service.points = deepcopy(point_snapshot)
            self.point_service._save_points()
            rollback_steps.append(self._ok_step("rollback_points", "Khôi phục points.json thành công."))
        except Exception as error:
            rollback_steps.append(self._ng_step("rollback_points", str(error)))

        try:
            self.law_service.repo.data = deepcopy(law_snapshot)
            self.law_service.repo.save()
            rollback_steps.append(self._ok_step("rollback_law", "Khôi phục config law thành công."))
        except Exception as error:
            rollback_steps.append(self._ng_step("rollback_law", str(error)))

        if self.calibration_service is not None and calibration_snapshot is not None:
            try:
                self.calibration_service.calibrations = deepcopy(calibration_snapshot)
                self.calibration_service._sync_to_repository()
                rollback_steps.append(self._ok_step("rollback_calibration", "Khôi phục calibration thành công."))
            except Exception as error:
                rollback_steps.append(self._ng_step("rollback_calibration", str(error)))

        try:
            anomaly_repo = PatchCoreTrainRecordRepository(
                manifest_path=PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST
            )
            anomaly_repo.save_manifest(anomaly_manifest_snapshot)
            rollback_steps.append(self._ok_step("rollback_manifest_anomaly_point", "Khôi phục manifest anomaly point thành công."))
        except Exception as error:
            rollback_steps.append(self._ng_step("rollback_manifest_anomaly_point", str(error)))

        try:
            foreign_repo = PatchCoreTrainRecordRepository(
                manifest_path=PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST
            )
            foreign_repo.save_manifest(foreign_manifest_snapshot)
            rollback_steps.append(self._ok_step("rollback_manifest_foreign", "Khôi phục manifest foreign object thành công."))
        except Exception as error:
            rollback_steps.append(self._ng_step("rollback_manifest_foreign", str(error)))

        return rollback_steps

    @staticmethod
    def _remove_item_from_law(repo_data: dict, product_key: str, frame_key: str, item_key: str) -> bool:
        """
        Chức năng: Xóa toàn bộ cấu hình law của item, đồng thời dọn node rỗng cha frame/product.
        Input: repo_data, product_key, frame_key, item_key.
        Output: True nếu có thay đổi dữ liệu, ngược lại False.
        Errors: Không phát sinh.
        """
        product_data = repo_data.get(product_key)
        if not isinstance(product_data, dict):
            return False
        frame_data = product_data.get(frame_key)
        if not isinstance(frame_data, dict):
            return False
        if item_key not in frame_data:
            return False
        frame_data.pop(item_key, None)
        if not frame_data:
            product_data.pop(frame_key, None)
        if not product_data:
            repo_data.pop(product_key, None)
        return True

    @staticmethod
    def _manifest_belongs_to_item(record: dict, product_key: str, frame_key: str, item_key: str) -> bool:
        """
        Chức năng: Xác định một record manifest có thuộc item (product/frame/point) hay không.
        Input: record metadata và bộ khóa product/frame/item dạng chuỗi.
        Output: True nếu record thuộc item cần xóa.
        Errors: Không phát sinh.
        """
        for field in ("model_root", "model_file", "runtime_images_root", "inference_result"):
            raw = record.get(field)
            if not raw:
                continue
            path_str = str(raw).replace("\\", "/")
            parts = [segment for segment in path_str.split("/") if segment]
            if "patch_core" not in parts:
                continue
            idx = parts.index("patch_core")
            if idx + 3 >= len(parts):
                continue
            if (
                parts[idx + 1] == product_key
                and parts[idx + 2] == frame_key
                and parts[idx + 3] == item_key
            ):
                return True
        return False

    def delete_capture_item(
        self,
        product_id: int,
        frame_id: int,
        point_id: int,
    ) -> Result:
        """
        Chức năng: Xóa item capture theo transaction mạnh: point assets + law + manifest + calibration điều kiện.
        Input: product_id (int), frame_id (int), point_id (int).
        Output: Result.Ok(dict) khi commit thành công hoặc Result.Fail(dict) nếu rollback/fail.
        Errors: Trả về Result.Fail(ErrorCode/str) với technical_report chi tiết từng bước.
        """
        technical_report: list[dict] = []
        point_obj = self.point_service.points.get(product_id, {}).get(frame_id, {}).get(point_id)
        if point_obj is None:
            return Result.Fail(
                {
                    "error": ErrorCode.POINT_NOT_FOUND,
                    "technical_report": [
                        self._ng_step("precheck_point", "Không tìm thấy point để xóa.")
                    ],
                }
            )

        product_key = str(product_id)
        frame_key = str(frame_id)
        item_key = str(point_id)

        point_snapshot = deepcopy(self.point_service.points)
        law_snapshot = deepcopy(self.law_service.repo.data)
        calibration_snapshot = deepcopy(self.calibration_service.calibrations) if self.calibration_service is not None else None
        anomaly_repo = PatchCoreTrainRecordRepository(
            manifest_path=PATH_FILE_ANOMALY_POINT_PATCHCORE_TRAIN_MANIFEST
        )
        foreign_repo = PatchCoreTrainRecordRepository(
            manifest_path=PATH_FILE_FOREIGN_PATCHCORE_TRAIN_MANIFEST
        )
        anomaly_manifest_snapshot = deepcopy(anomaly_repo.load_manifest())
        foreign_manifest_snapshot = deepcopy(foreign_repo.load_manifest())

        txn_dir = self._staging_root / f"txn_{uuid.uuid4().hex}"
        txn_dir.mkdir(parents=True, exist_ok=True)
        moved_entries: list[_MovedEntry] = []

        try:
            self._stage_path(
                self._safe_abs(point_obj.path_img_point),
                txn_dir,
                moved_entries,
                technical_report,
                "stage_point_image",
            )
            self._stage_path(
                self._safe_abs(point_obj.path_model_patch_core),
                txn_dir,
                moved_entries,
                technical_report,
                "stage_patchcore_model",
            )
            self._stage_path(
                self._safe_abs(point_obj.path_img_retrain),
                txn_dir,
                moved_entries,
                technical_report,
                "stage_retrain_folder",
            )

            self.point_service.points[product_id][frame_id].pop(point_id, None)
            if not self.point_service.points[product_id][frame_id]:
                self.point_service.points[product_id].pop(frame_id, None)
            if not self.point_service.points[product_id]:
                self.point_service.points.pop(product_id, None)
            technical_report.append(self._ok_step("mutate_point_ram", "Đã xóa point khỏi RAM."))

            law_changed = self._remove_item_from_law(
                self.law_service.repo.data,
                product_key,
                frame_key,
                item_key,
            )
            technical_report.append(
                self._ok_step(
                    "mutate_law_item",
                    "Đã xóa law item." if law_changed else "Không có law item tương ứng.",
                )
            )

            deleted_calibration = False
            if self.calibration_service is not None:
                calib_frame = self.calibration_service.calibrations.get(product_key, {}).get(frame_key)
                if calib_frame is not None:
                    id_tems = str(getattr(calib_frame, "id_tems", ""))
                    if id_tems == item_key:
                        self.calibration_service.calibrations[product_key].pop(frame_key, None)
                        if not self.calibration_service.calibrations[product_key]:
                            self.calibration_service.calibrations.pop(product_key, None)
                        deleted_calibration = True
                technical_report.append(
                    self._ok_step(
                        "mutate_calibration",
                        "Đã xóa calibration theo điều kiện id_tems." if deleted_calibration else "Giữ nguyên calibration (không khớp id_tems).",
                    )
                )

            anomaly_manifest_new = [
                record
                for record in anomaly_manifest_snapshot
                if not self._manifest_belongs_to_item(record, product_key, frame_key, item_key)
            ]
            foreign_manifest_new = [
                record
                for record in foreign_manifest_snapshot
                if not self._manifest_belongs_to_item(record, product_key, frame_key, item_key)
            ]
            technical_report.append(
                self._ok_step(
                    "mutate_manifest",
                    "Đã lọc manifest theo item cần xóa.",
                )
            )

            self.point_service._save_points()
            self.law_service.repo.save()
            if self.calibration_service is not None:
                self.calibration_service._sync_to_repository()
            anomaly_repo.save_manifest(anomaly_manifest_new)
            foreign_repo.save_manifest(foreign_manifest_new)
            technical_report.append(
                self._ok_step("persist_all", "Đã ghi toàn bộ dữ liệu metadata thành công.")
            )

            cleanup_result = self.cleanup_empty_frame_structure(product_id, frame_id)
            cleanup_steps = (
                cleanup_result.data.get("technical_report", [])
                if cleanup_result.ok
                else cleanup_result.error.get("technical_report", [])
                if isinstance(cleanup_result.error, dict)
                else []
            )
            technical_report.extend(cleanup_steps)
            if not cleanup_result.ok:
                raise RuntimeError("Không thể dọn cấu trúc thư mục frame rỗng.")

            shutil.rmtree(txn_dir, ignore_errors=True)
            technical_report.append(
                self._ok_step("commit", "Đã commit transaction và xóa staging.")
            )

            return Result.Ok(
                {
                    "technical_report": technical_report,
                    "deleted_calibration": deleted_calibration,
                }
            )
        except Exception as error:
            technical_report.append(self._ng_step("transaction", f"Lỗi transaction: {error}"))
            rollback_steps = self._rollback(
                moved_entries=moved_entries,
                point_snapshot=point_snapshot,
                law_snapshot=law_snapshot,
                calibration_snapshot=calibration_snapshot,
                anomaly_manifest_snapshot=anomaly_manifest_snapshot,
                foreign_manifest_snapshot=foreign_manifest_snapshot,
            )
            try:
                shutil.rmtree(txn_dir, ignore_errors=True)
            except Exception:
                pass
            return Result.Fail(
                {
                    "error": "DELETE_ITEM_TRANSACTION_FAILED",
                    "message": str(error),
                    "technical_report": technical_report + rollback_steps,
                }
            )