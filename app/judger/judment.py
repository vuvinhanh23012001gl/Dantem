from dataclasses import dataclass, field
from collections.abc import Mapping
import concurrent.futures
from datetime import datetime, timezone
from pathlib import Path
import threading
from typing import Any, Sequence
import numpy as np
import cv2
from app.config.path_config import PATH_FOLDER_OUTPUT_RETRAIN
from .base_ai import BaseJudgerAI, JudgmentResult
from app.utils.opencv_tool import Tool_OpenCv2


@dataclass
class InspectorTask:
    """Cấu hình một inspector trong một lần kiểm tra ảnh.
    Input:
        inspector: Instance của một lớp kế thừa ``BaseJudgerAI``.
        standard_data: Dữ liệu chuẩn truyền vào ``compare``.
        define_args: Tham số vị trí truyền thêm cho ``define`` sau ảnh.
        define_kwargs: Tham số tên truyền vào ``define``.
        compare_kwargs: Tham số tên truyền thêm vào ``compare``.
    Output:
        Một cấu hình có thể được ``Judment`` thực thi tuần tự.
    Errors:
        ``TypeError`` nếu ``inspector`` không phải là ``BaseJudgerAI``.
    """
    inspector: BaseJudgerAI
    standard_data: Any
    define_args: tuple[Any, ...] = ()
    define_kwargs: dict[str, Any] = field(default_factory=dict)
    compare_kwargs: dict[str, Any] = field(default_factory=dict)
    overlay_labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Kiểm tra inspector ngay khi tạo task."""
        if not isinstance(self.inspector, BaseJudgerAI):
            raise TypeError("inspector phải là instance của BaseJudgerAI")


class Judment:
    RETRAIN_OUTPUT_DIR = PATH_FOLDER_OUTPUT_RETRAIN
    _retrain_executor: concurrent.futures.ThreadPoolExecutor | None = None
    _retrain_lock: threading.Lock = threading.Lock()

    @classmethod
    def _get_retrain_executor(cls) -> concurrent.futures.ThreadPoolExecutor:
        with cls._retrain_lock:
            if cls._retrain_executor is None:
                cls._retrain_executor = concurrent.futures.ThreadPoolExecutor(
                    max_workers=2,
                    thread_name_prefix="JudmentRetrainSaver",
                )
            return cls._retrain_executor

    @classmethod
    def flush_retrain_queue(cls, timeout: float = 5.0) -> None:
        """Đợi toàn bộ ảnh retrain trong luồng nền được flush xuống đĩa."""
        with cls._retrain_lock:
            if cls._retrain_executor is not None:
                cls._retrain_executor.shutdown(wait=True, cancel_futures=False)
                cls._retrain_executor = None

    LINE_BASED_INSPECTORS: set[str] = set()
    ROI_DISPLAY_NAMES = {
        "StampItemInspector": "Kiểm tra Có/Không tem",
        "StampAlignmentInspector": "Kiểm tra độ lệch tem",
        "StampReversedInspector": "Kiểm tra tem in ngược",
        "AnomalyPointInspector": "Điểm bất thường",
        "ForeignObjectInspector": "Dị vật",
        "OCRTextInspector": "Nhận diện chữ OCR",
        "ColorItemInspector": "Kiểm tra màu",
        "BarcodeItemInspector": "Kiểm tra mã Barcode",
        "QRItemInspector": "Kiểm tra mã QR",
    }

    def __init__(
        self,
        inspector_registry: Mapping[str, BaseJudgerAI] | None = None,
    ) -> None:
        """Khởi tạo bộ điều phối với registry các detector đã load model."""
        self.inspector_registry = dict(inspector_registry or {})
        for name, inspector in self.inspector_registry.items():
            if not isinstance(name, str) or not isinstance(inspector, BaseJudgerAI):
                raise TypeError("inspector_registry phải map tên tới BaseJudgerAI")

    def run(
        self,
        image: np.ndarray,
        inspectors: Sequence[InspectorTask] | Mapping[str, Any],
        inspector_registry: Mapping[str, BaseJudgerAI] | None = None,
        scale_mm_per_pixel: float = 1.0,
    ) -> dict[str, JudgmentResult]:
        """Chạy lần lượt tất cả inspector trên một ảnh."""
        if not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("image đầu vào không được rỗng")
        if not inspectors:
            raise ValueError("inspectors phải chứa ít nhất một inspector")
        if not isinstance(scale_mm_per_pixel, (int, float)) or scale_mm_per_pixel <= 0:
            raise ValueError("scale_mm_per_pixel phải là số lớn hơn 0")

        if isinstance(inspectors, Mapping):
            registry = dict(inspector_registry or self.inspector_registry)
            inspectors = self._tasks_from_config(
                inspectors,
                registry,
                float(scale_mm_per_pixel),
            )

        results: dict[str, JudgmentResult] = {}
        for index, task in enumerate(inspectors, start=1):
            if not isinstance(task, InspectorTask):
                raise TypeError("mọi phần tử inspectors phải là InspectorTask")
            name = task.inspector.get_inspector_name()
            if name in results:
                raise ValueError(f"Inspector bị trùng tên: {name}")
            self._log_inspector_start(index, name, image, task)
            runtime_data = task.inspector.define(
                image,
                *task.define_args,
                **task.define_kwargs,
            )
            comparison_data = task.inspector.compare(
                task.standard_data,
                runtime_data,
                **task.compare_kwargs,
            )
            result = task.inspector.judge(comparison_data)
            if not isinstance(result, JudgmentResult):
                raise TypeError(f"{name}.judge() phải trả về JudgmentResult")
            results[name] = result
            self._log_inspector_result(name, runtime_data, comparison_data, result)
        return results

    @staticmethod
    def _tasks_from_config(
        config: Mapping[str, Any],
        inspector_registry: Mapping[str, BaseJudgerAI],
        scale_mm_per_pixel: float,
        context: Mapping[str, Any] | None = None,
    ) -> list[InspectorTask]:
        """Chuyển object config thành danh sách task có thể thực thi."""
        if "EndChippingInspector" in config:
            config = dict(config)
            legacy_config = config.pop("EndChippingInspector")
            config.setdefault("AnomalyPointInspector", legacy_config)

        tasks: list[InspectorTask] = []
        for name, inspector_config in config.items():
            inspector = inspector_registry.get(name)
            if inspector is None:
                raise ValueError(
                    f"Chưa có detector cho inspector '{name}'"
                )
            if not isinstance(inspector_config, Mapping):
                raise ValueError(f"Cấu hình {name} phải là object")

            if name == "StampItemInspector":
                boxes: list[dict[str, Any]] = []
                labels: list[str] = []
                for region_key, region in inspector_config.items():
                    if not isinstance(region, Mapping):
                        continue
                    try:
                        x1 = int(region["xStart"])
                        y1 = int(region["yStart"])
                        x2 = int(region["xEnd"])
                        y2 = int(region["yEnd"])
                    except (KeyError, TypeError, ValueError) as error:
                        raise ValueError(f"Cấu hình vùng của {name} thiếu tọa độ") from error
                    if x2 <= x1 or y2 <= y1:
                        raise ValueError(f"Cấu hình vùng của {name} có kích thước không hợp lệ")
                    box_name = str(
                        region.get("name") or f"Tem {len(boxes) + 1}"
                    ).strip() or f"Tem {len(boxes) + 1}"
                    boxes.append(
                        {
                            "id": region.get("id", region_key),
                            "key": str(region_key),
                            "name": box_name,
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                        }
                    )
                    labels.append(box_name)
                if not boxes:
                    raise ValueError(f"Cấu hình {name} không chứa khung ROI hợp lệ")
                tasks.append(
                    InspectorTask(
                        inspector=inspector,
                        standard_data={name: dict(inspector_config)},
                        define_args=(boxes,),
                        overlay_labels=tuple(labels),
                    )
                )
                continue

            if name == "StampAlignmentInspector":
                boxes: list[dict[str, Any]] = []
                labels: list[str] = []
                for region_key, region in inspector_config.items():
                    if not isinstance(region, Mapping):
                        continue
                    try:
                        x1 = int(region["xStart"])
                        y1 = int(region["yStart"])
                        x2 = int(region["xEnd"])
                        y2 = int(region["yEnd"])
                    except (KeyError, TypeError, ValueError) as error:
                        raise ValueError(f"Cấu hình vùng của {name} thiếu tọa độ") from error
                    if x2 <= x1 or y2 <= y1:
                        raise ValueError(f"Cấu hình vùng của {name} có kích thước không hợp lệ")
                    box_name = str(
                        region.get("name") or f"Tem {len(boxes) + 1}"
                    ).strip() or f"Tem {len(boxes) + 1}"
                    boxes.append(
                        {
                            "id": region.get("id", region_key),
                            "key": str(region_key),
                            "name": box_name,
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            "max_du": float(region.get("max_du", 15.0)),
                            "max_dv": float(region.get("max_dv", 15.0)),
                            "max_deg": float(region.get("max_deg", 3.0)),
                            "margin": float(region.get("margin", 5.0)),
                        }
                    )
                    labels.append(box_name)
                if not boxes:
                    raise ValueError(f"Cấu hình {name} không chứa khung ROI hợp lệ")
                tasks.append(
                    InspectorTask(
                        inspector=inspector,
                        standard_data={name: dict(inspector_config)},
                        define_args=(boxes,),
                        overlay_labels=tuple(labels),
                    )
                )
                continue

            if name == "ColorItemInspector":
                boxes: list[dict[str, Any]] = []
                labels: list[str] = []
                for region_key, region in inspector_config.items():
                    if not isinstance(region, Mapping):
                        continue
                    try:
                        x1 = int(region["xStart"])
                        y1 = int(region["yStart"])
                        x2 = int(region["xEnd"])
                        y2 = int(region["yEnd"])
                    except (KeyError, TypeError, ValueError) as error:
                        raise ValueError(f"C?u h?nh v?ng c?a {name} thi?u t?a ??") from error
                    if x2 <= x1 or y2 <= y1:
                        raise ValueError(f"C?u h?nh v?ng c?a {name} c? k?ch th??c kh?ng h?p l?")
                    box_name = str(region.get("name") or f"M?u {len(boxes) + 1}").strip() or f"M?u {len(boxes) + 1}"
                    boxes.append(
                        {
                            "id": region.get("id", region_key),
                            "key": str(region_key),
                            "name": box_name,
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            "ref_rgb": region.get("ref_rgb"),
                            "ref_lab": region.get("ref_lab"),
                            "max_delta_e": float(region.get("max_delta_e", 5.0)),
                        }
                    )
                    labels.append(box_name)
                if not boxes:
                    raise ValueError(f"C?u h?nh {name} kh?ng ch?a khung ROI h?p l?")
                tasks.append(
                    InspectorTask(
                        inspector=inspector,
                        standard_data={name: dict(inspector_config)},
                        define_args=(boxes,),
                        overlay_labels=tuple(labels),
                    )
                )
                continue

            if name == "StampReversedInspector":
                boxes: list[dict[str, Any]] = []
                labels: list[str] = []
                for region_key, region in inspector_config.items():
                    if not isinstance(region, Mapping):
                        continue
                    try:
                        x1 = int(region["xStart"])
                        y1 = int(region["yStart"])
                        x2 = int(region["xEnd"])
                        y2 = int(region["yEnd"])
                    except (KeyError, TypeError, ValueError) as error:
                        raise ValueError(f"Cấu hình vùng của {name} thiếu tọa độ") from error
                    if x2 <= x1 or y2 <= y1:
                        raise ValueError(f"Cấu hình vùng của {name} có kích thước không hợp lệ")
                    box_name = str(
                        region.get("name") or f"Tem ngược {len(boxes) + 1}"
                    ).strip() or f"Tem ngược {len(boxes) + 1}"
                    boxes.append(
                        {
                            "id": region.get("id", region_key),
                            "key": str(region_key),
                            "name": box_name,
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            "xStart": x1,
                            "yStart": y1,
                            "xEnd": x2,
                            "yEnd": y2,
                            "bbox_roi": [x1, y1, x2, y2],
                            "max_deg": float(region.get("max_deg", 15.0)),
                        }
                    )
                    labels.append(box_name)
                if not boxes:
                    raise ValueError(f"Cấu hình {name} không chứa khung ROI hợp lệ")
                tasks.append(
                    InspectorTask(
                        inspector=inspector,
                        standard_data={name: dict(inspector_config)},
                        define_args=(boxes,),
                        overlay_labels=tuple(labels),
                    )
                )
                continue

            if name in {"OCRTextInspector", "BarcodeItemInspector", "QRItemInspector"}:
                boxes: list[dict[str, Any]] = []
                labels: list[str] = []
                default_prefix = Judment.ROI_DISPLAY_NAMES.get(name, name)
                for region_key, region in inspector_config.items():
                    if not isinstance(region, Mapping):
                        continue
                    try:
                        x1 = int(region["xStart"])
                        y1 = int(region["yStart"])
                        x2 = int(region["xEnd"])
                        y2 = int(region["yEnd"])
                    except (KeyError, TypeError, ValueError) as error:
                        raise ValueError(
                            f"Cấu hình vùng của {name} thiếu tọa độ"
                        ) from error
                    if x2 <= x1 or y2 <= y1:
                        raise ValueError(
                            f"Cấu hình vùng của {name} có kích thước không hợp lệ"
                        )
                    box_name = str(
                        region.get("name") or f"{default_prefix} {len(boxes) + 1}"
                    ).strip() or f"{default_prefix} {len(boxes) + 1}"
                    boxes.append(
                        {
                            "id": region.get("id", region_key),
                            "key": str(region_key),
                            "name": box_name,
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            "expected_text": str(region.get("expected_text") or ""),
                        }
                    )
                    labels.append(box_name)
                if not boxes:
                    raise ValueError(f"Cấu hình {name} không chứa khung ROI hợp lệ")
                tasks.append(
                    InspectorTask(
                        inspector=inspector,
                        standard_data={name: dict(inspector_config)},
                        define_args=(boxes,),
                        overlay_labels=tuple(labels),
                    )
                )
                continue

            if name in {"AnomalyPointInspector", "ForeignObjectInspector", "ColorItemInspector"}:
                boxes: list[dict[str, Any]] = []
                labels: list[str] = []
                coordinate_keys = ("xStart", "yStart", "xEnd", "yEnd")
                raw_regions = (
                    [("0", inspector_config)]
                    if all(k in inspector_config for k in coordinate_keys)
                    else list(inspector_config.items())
                )
                for region_key, region in raw_regions:
                    if not isinstance(region, Mapping):
                        continue
                    try:
                        x1 = int(region["xStart"])
                        y1 = int(region["yStart"])
                        x2 = int(region["xEnd"])
                        y2 = int(region["yEnd"])
                    except (KeyError, TypeError, ValueError) as error:
                        raise ValueError(f"Cấu hình vùng của {name} thiếu tọa độ") from error
                    if x2 <= x1 or y2 <= y1:
                        raise ValueError(f"Cấu hình vùng của {name} có kích thước không hợp lệ")
                    box_name = str(
                        region.get("name") or f"{Judment.ROI_DISPLAY_NAMES[name]} {len(boxes) + 1}"
                    ).strip() or f"{Judment.ROI_DISPLAY_NAMES[name]} {len(boxes) + 1}"
                    boxes.append(
                        {
                            "id": 0 if name == "ForeignObjectInspector" and all(
                                k in inspector_config for k in coordinate_keys
                            ) else region.get("id", region_key),
                            "key": str(region_key),
                            "name": box_name,
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            **({"threshold": float(
                                region.get("threshold", region.get("thresholdNG", 0.2))
                            )} if name == "AnomalyPointInspector" else {}),
                            "saveRuntimeImages": bool(region.get("saveRuntimeImages", False)),
                        }
                    )
                    labels.append(box_name)
                if not boxes:
                    raise ValueError(f"Cấu hình {name} không chứa khung ROI hợp lệ")
                define_kwargs_anom: dict[str, Any] = {}
                if context:
                    define_kwargs_anom.update(context)
                tasks.append(
                    InspectorTask(
                        inspector=inspector,
                        standard_data={name: dict(inspector_config)},
                        define_args=(boxes,),
                        define_kwargs=define_kwargs_anom,
                        overlay_labels=tuple(labels),
                    )
                )
                continue


            try:
                x1 = int(inspector_config["xStart"])
                y1 = int(inspector_config["yStart"])
                x2 = int(inspector_config["xEnd"])
                y2 = int(inspector_config["yEnd"])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"Cấu hình ROI của {name} thiếu tọa độ") from error

            define_args: tuple[Any, ...] = (x1, y1, x2, y2)
            tasks.append(
                InspectorTask(
                    inspector=inspector,
                    standard_data=True,
                    define_args=define_args,
                    overlay_labels=(str(
                        inspector_config.get("name")
                        or Judment.ROI_DISPLAY_NAMES.get(name, name)
                    ),),
                )
            )
        return tasks

    def evaluate(
        self,
        image: np.ndarray,
        inspectors: Sequence[InspectorTask] | Mapping[str, Any],
        inspector_registry: Mapping[str, BaseJudgerAI] | None = None,
        scale_mm_per_pixel: float = 1.0,
    ) -> dict[str, JudgmentResult]:
        """Alias dễ đọc hơn cho ``run``."""
        return self.run(
            image,
            inspectors,
            inspector_registry,
            scale_mm_per_pixel,
        )

    def run_summary(
        self,
        image: np.ndarray,
        inspectors: Sequence[InspectorTask] | Mapping[str, Any],
        inspector_registry: Mapping[str, BaseJudgerAI] | None = None,
        scale_mm_per_pixel: float = 1.0,
        training_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Chạy toàn bộ tool trên một ảnh và tạo output tổng để ghi log."""
        if not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("image đầu vào không được rỗng")
        tasks = inspectors
        if isinstance(inspectors, Mapping):
            registry = dict(inspector_registry or self.inspector_registry)
            tasks = self._tasks_from_config(
                inspectors,
                registry,
                float(scale_mm_per_pixel),
                context=training_context,
            )
        if not tasks:
            raise ValueError("inspectors phải chứa ít nhất một inspector")

        inspector_results: dict[str, dict[str, Any]] = {}
        errors: list[dict[str, str]] = []
        inspector_images: dict[str, np.ndarray] = {}
        overlay_data: dict[str, dict[str, Any]] = {}
        judgment_image = image.copy()

        for index, task in enumerate(tasks, start=1):
            if not isinstance(task, InspectorTask):
                raise TypeError("mọi phần tử inspectors phải là InspectorTask")
            name = task.inspector.get_inspector_name()
            self._log_inspector_start(index, name, image, task)
            try:
                if training_context is not None:
                    allowed_inspectors = (
                        training_context.get("enabled_inspectors")
                        if isinstance(training_context, dict)
                        else None
                    )
                    is_async_retrain = (
                        bool(training_context.get("async_retrain", False))
                        if isinstance(training_context, dict)
                        else False
                    )
                    if allowed_inspectors is None or name in allowed_inspectors:
                        try:
                            saved_inputs = self._save_training_inputs(
                                image,
                                name,
                                task.define_args,
                                async_save=is_async_retrain,
                            )
                            for saved_path in saved_inputs:
                                print(f"[JUDMENT][{name}] TRAIN_INPUT saved={saved_path}")
                        except Exception as save_error:
                            print(
                                f"[JUDMENT][{name}] TRAIN_INPUT_SAVE_WARNING: "
                                f"{save_error!r}"
                            )
                define_kwargs = dict(task.define_kwargs)

                runtime_data = task.inspector.define(
                    image,
                    *task.define_args,
                    **define_kwargs,
                )
                comparison_data = task.inspector.compare(
                    task.standard_data,
                    runtime_data,
                    **task.compare_kwargs,
                )
                result = task.inspector.judge(comparison_data)
                if not isinstance(result, JudgmentResult):
                    raise TypeError("detector phải trả về JudgmentResult")
                inspector_results[name] = result.to_dict()
                inspector_image, inspector_overlay = self._render_inspector_overlay(
                    image,
                    name,
                    task.standard_data,
                    task.define_args,
                    runtime_data,
                    comparison_data,
                    result,
                    task.overlay_labels,
                )
                inspector_images[name] = inspector_image
                overlay_data[name] = inspector_overlay
                has_custom_image = (
                    isinstance(runtime_data, dict)
                    and isinstance(runtime_data.get("image"), np.ndarray)
                )
                overlay_alpha = (
                    1.0
                    if has_custom_image
                    else (
                        0.85
                        if inspector_overlay.get("standard", {}).get("boxes")
                        else 0.45
                    )
                )
                judgment_image = self._blend_overlay_image(
                    judgment_image,
                    inspector_image,
                    overlay_alpha,
                    image,
                )
                self._log_inspector_result(name, runtime_data, comparison_data, result)
                if not result.ok:
                    errors.append({
                        "inspector": name,
                        "message": result.message or "Tool phán định NG",
                    })
            except Exception as error:
                message = str(error)
                print(f"[JUDMENT][{name}] ERROR: {message}")
                errors.append({"inspector": name, "message": message})
                inspector_results[name] = JudgmentResult(
                    ok=False,
                    status="NG",
                    message=f"Lỗi tool {name}: {message}",
                    errors=[message],
                ).to_dict()

        overall = not errors and all(
            result.get("ok") is True for result in inspector_results.values()
        )
        missing_judgment_data = any(
            isinstance(result, dict)
            and isinstance(result.get("runtime_data"), dict)
            and bool(result["runtime_data"].get("missing_judgment_data"))
            for result in inspector_results.values()
        )
        if overall:
            status = "OK"
            message = "Tất cả hạng mục kiểm tra đạt"
        else:
            status = "NO_DATA" if missing_judgment_data else "NG"
            message = (
                "Thiếu dữ liệu phán định ở một hoặc nhiều hạng mục"
                if missing_judgment_data
                else f"Có {len(errors)} hạng mục kiểm tra không đạt"
            )
        return {
            "overall": overall,
            "status": status,
            "message": message,
            "image": {
                "height": int(image.shape[0]),
                "width": int(image.shape[1]),
                "channels": int(image.shape[2]) if image.ndim == 3 else 1,
            },
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "inspectors": inspector_results,
            "errors": errors,
            "overlay_data": overlay_data,
            "judgment_image": judgment_image,
            "inspector_images": inspector_images,
        }

    @staticmethod
    def _normalize_polygons(polygon_data: np.ndarray | list | None) -> list[np.ndarray]:
        """Chuẩn hóa đầu vào polygon đơn/đa contour về list ``np.ndarray`` Nx1x2."""
        if polygon_data is None:
            return []
        if isinstance(polygon_data, np.ndarray):
            contour = np.asarray(polygon_data, dtype=np.float32).reshape(-1, 1, 2)
            if len(contour) >= 3:
                return [contour.astype(np.int32)]
            return []
        if not isinstance(polygon_data, list) or not polygon_data:
            return []

        first = polygon_data[0]
        if (
            isinstance(first, (list, tuple, np.ndarray))
            and len(first) >= 2
            and not isinstance(first[0], (list, tuple, np.ndarray))
        ):
            contour = np.asarray(polygon_data, dtype=np.float32).reshape(-1, 1, 2)
            return [contour.astype(np.int32)] if len(contour) >= 3 else []

        contours: list[np.ndarray] = []
        for candidate in polygon_data:
            try:
                contour = np.asarray(candidate, dtype=np.float32).reshape(-1, 1, 2)
            except (TypeError, ValueError):
                continue
            if len(contour) >= 3:
                contours.append(contour.astype(np.int32))
        return contours


    @staticmethod
    def _extract_runtime_polygons(
        runtime_data: Any,
        comparison_data: Any,
    ) -> list[list[list[int]]]:
        """Trích xuất toàn bộ contour runtime theo định dạng chuẩn để tái sử dụng."""
        polygon_candidates = None
        if isinstance(runtime_data, dict) and runtime_data.get("polygons") is not None:
            polygon_candidates = runtime_data.get("polygons")
        elif isinstance(comparison_data, dict) and comparison_data.get("polygons") is not None:
            polygon_candidates = comparison_data.get("polygons")

        normalized_contours = Judment._normalize_polygons(polygon_candidates)
        if not normalized_contours:
            single_polygon = None
            if isinstance(runtime_data, dict) and runtime_data.get("polygon") is not None:
                single_polygon = runtime_data.get("polygon")
            elif isinstance(comparison_data, dict) and comparison_data.get("polygon") is not None:
                single_polygon = comparison_data.get("polygon")
            normalized_contours = Judment._normalize_polygons(single_polygon)

        polygons: list[list[list[int]]] = []
        for contour in normalized_contours:
            points = np.asarray(contour, dtype=np.float32).reshape(-1, 2)
            if len(points) < 3:
                continue
            polygons.append(points.astype(np.int32).tolist())
        return polygons


    @classmethod
    def _save_training_inputs(
        cls,
        image: np.ndarray,
        inspector_name: str,
        define_args: tuple[Any, ...],
        async_save: bool = False,
    ) -> list[Path]:
        """Lưu crop ROI hoặc full frame mà inspector thực sự nhận trước inference."""
        crops: list[tuple[str, np.ndarray]] = []
        if inspector_name in cls.LINE_BASED_INSPECTORS:
            crops.append(("full_frame", image))
        elif (
            inspector_name in {"StampItemInspector", "StampAlignmentInspector", "StampReversedInspector", "AnomalyPointInspector", "ForeignObjectInspector"}
            and define_args
            and isinstance(define_args[0], list)
        ):
            boxes = define_args[0]
            for index, box in enumerate(boxes, start=1):
                if isinstance(box, Mapping):
                    x1 = int(box.get("x1", box.get("xStart", 0)))
                    y1 = int(box.get("y1", box.get("yStart", 0)))
                    x2 = int(box.get("x2", box.get("xEnd", 0)))
                    y2 = int(box.get("y2", box.get("yEnd", 0)))
                    crops.append((
                        f"roi_{index:02d}",
                        cls._crop_training_input(image, x1, y1, x2, y2),
                    ))
        elif len(define_args) >= 4:
            x1, y1, x2, y2 = (int(value) for value in define_args[:4])
            crops.append(("roi_01", cls._crop_training_input(image, x1, y1, x2, y2)))
        else:
            crops.append(("full_frame", image))

        saved_paths = []
        retrain_dir = cls.RETRAIN_OUTPUT_DIR
        if retrain_dir == PATH_FOLDER_OUTPUT_RETRAIN:
            try:
                from app.services.log.config_software import Config_SoftWare
                cfg = Config_SoftWare()
                cfg_dir = cfg.get_output_retrain_dir()
                if cfg_dir:
                    retrain_dir = cfg_dir
            except Exception:
                pass

        for label, crop in crops:
            if async_save:
                executor = cls._get_retrain_executor()
                executor.submit(
                    Tool_OpenCv2.save_training_input,
                    crop,
                    inspector_name,
                    label,
                    retrain_dir,
                )
            else:
                saved_paths.append(Tool_OpenCv2.save_training_input(
                    crop,
                    inspector_name,
                    label,
                    retrain_dir,
                ))
        return saved_paths

    @staticmethod
    def _crop_training_input(
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> np.ndarray:
        """Cắt ROI theo tọa độ gốc và chặn biên ảnh."""
        height, width = image.shape[:2]
        left = max(0, min(width, min(x1, x2)))
        right = max(0, min(width, max(x1, x2)))
        top = max(0, min(height, min(y1, y2)))
        bottom = max(0, min(height, max(y1, y2)))
        if left >= right or top >= bottom:
            raise ValueError(f"ROI không hợp lệ: {(x1, y1, x2, y2)}")
        return image[top:bottom, left:right].copy()

    @staticmethod
    def _blend_overlay_image(
        base: np.ndarray,
        overlay: np.ndarray,
        overlay_alpha: float = 0.45,
        reference: np.ndarray | None = None,
    ) -> np.ndarray:
        """Gộp ảnh overlay inspector lên ảnh judgment tổng."""
        if not isinstance(overlay, np.ndarray) or overlay.shape != base.shape:
            return base
        source = reference if isinstance(reference, np.ndarray) and reference.shape == base.shape else base
        changed = np.any(overlay != source, axis=2)
        if not np.any(changed):
            return base
        alpha = max(0.0, min(1.0, float(overlay_alpha)))
        blended = cv2.addWeighted(base, 1.0 - alpha, overlay, alpha, 0)
        base[changed] = blended[changed]
        return base

    @classmethod
    def _render_inspector_overlay(
        cls,
        image: np.ndarray,
        name: str,
        standard_data: Any,
        define_args: tuple[Any, ...],
        runtime_data: Any,
        comparison_data: Any,
        result: JudgmentResult,
        roi_labels: tuple[str, ...] = (),
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Vẽ cấu hình chuẩn và dữ liệu runtime theo đúng loại inspector."""
        runtime_source = runtime_data if isinstance(runtime_data, dict) else {}
        comparison_source = comparison_data if isinstance(comparison_data, dict) else {}
        runtime_image = runtime_source.get("image")
        if not isinstance(runtime_image, np.ndarray):
            runtime_image = comparison_source.get("image")
        output = runtime_image.copy() if isinstance(runtime_image, np.ndarray) else image.copy()
        overlay: dict[str, Any] = {"standard": {}, "runtime": {}, "status": result.status}
        config = standard_data.get(name, standard_data) if isinstance(standard_data, dict) else standard_data

        coordinate_keys = ("xStart", "yStart", "xEnd", "yEnd")
        if name in {"StampItemInspector", "StampAlignmentInspector", "StampReversedInspector"}:
            box_items = comparison_source.get("box_comparisons")
            if not isinstance(box_items, list) or not box_items:
                box_items = runtime_source.get("boxes")
            if (not isinstance(box_items, list) or not box_items) and define_args and isinstance(define_args[0], list):
                box_items = define_args[0]
            if isinstance(box_items, list) and box_items:
                for b_item in box_items:
                    if not isinstance(b_item, dict):
                        continue
                    roi = b_item.get("bbox_roi") or b_item.get("roi")
                    if not isinstance(roi, (list, tuple)) or len(roi) != 4:
                        if all(k in b_item for k in ("x1", "y1", "x2", "y2")):
                            roi = [b_item["x1"], b_item["y1"], b_item["x2"], b_item["y2"]]
                        else:
                            continue
                    shape = [int(v) for v in roi]
                    raw_label = str(b_item.get("name") or "Tem")
                    if "ok" in b_item:
                        box_ok = bool(b_item.get("ok"))
                    elif "exists" in b_item:
                        box_ok = bool(b_item.get("exists"))
                    else:
                        box_ok = bool(result.ok)
                    status_tag = "OK" if box_ok else "NG"
                    roi_color = (0, 255, 0) if box_ok else (0, 0, 255)
                    Tool_OpenCv2.draw_labeled_roi(
                        output,
                        tuple(shape),
                        f"{raw_label} [{status_tag}]",
                        roi_color,
                    )
                    overlay["standard"].setdefault("labels", []).append(raw_label)
                    overlay["standard"].setdefault("boxes", []).append(shape)
        elif name in {
            "AnomalyPointInspector",
            "ForeignObjectInspector",
            "OCRTextInspector",
            "ColorItemInspector",
            "BarcodeItemInspector",
            "QRItemInspector",
        }:
            box_items = comparison_source.get("box_comparisons")
            if not isinstance(box_items, list) or not box_items:
                box_items = runtime_source.get("boxes")
            if (not isinstance(box_items, list) or not box_items) and define_args and isinstance(define_args[0], list):
                box_items = define_args[0]
            if isinstance(box_items, list) and box_items:
                for b_item in box_items:
                    if not isinstance(b_item, dict):
                        continue
                    roi = b_item.get("bbox_roi")
                    if not isinstance(roi, (list, tuple)) or len(roi) != 4:
                        if all(k in b_item for k in ("x1", "y1", "x2", "y2")):
                            roi = [b_item["x1"], b_item["y1"], b_item["x2"], b_item["y2"]]
                        else:
                            continue
                    shape = [int(v) for v in roi]
                    raw_label = str(b_item.get("name") or cls.ROI_DISPLAY_NAMES[name])
                    box_ok = bool(b_item.get("ok", result.ok))
                    status_tag = "OK" if box_ok else "NG"
                    score_val = b_item.get("score")
                    if score_val is not None:
                        display_label = f"{raw_label} [{status_tag} {float(score_val):.3f}]"
                    else:
                        display_label = f"{raw_label} [{status_tag}]"
                    roi_color = (0, 255, 0) if box_ok else (0, 0, 255)
                    Tool_OpenCv2.draw_labeled_roi(
                        output,
                        tuple(shape),
                        display_label,
                        roi_color,
                    )
                    overlay["standard"].setdefault("labels", []).append(raw_label)
                    overlay["standard"].setdefault("boxes", []).append(shape)
        elif isinstance(config, dict) and all(key in config for key in coordinate_keys):
            shape = [
                int(config["xStart"]), int(config["yStart"]),
                int(config["xEnd"]), int(config["yEnd"]),
            ]
            raw_label = str(
                config.get("name")
                or (roi_labels[0] if roi_labels else cls.ROI_DISPLAY_NAMES.get(name, name))
            )
            status_tag = "OK" if result.ok else "NG"
            score_val = runtime_source.get("score")
            if score_val is not None:
                display_label = f"{raw_label} [{status_tag} {float(score_val):.3f}]"
            else:
                display_label = f"{raw_label} [{status_tag}]"
            roi_color = (0, 255, 0) if result.ok else (0, 0, 255)
            Tool_OpenCv2.draw_labeled_roi(
                output,
                tuple(shape),
                display_label,
                roi_color,
            )
            overlay["standard"].setdefault("labels", []).append(raw_label)
            overlay["standard"].setdefault("boxes", []).append(shape)
        elif isinstance(config, dict):
            for config_key, value in config.items():
                if not isinstance(value, dict):
                    continue
                if not all(key in value for key in coordinate_keys):
                    continue
                shape = [
                    int(value["xStart"]), int(value["yStart"]),
                    int(value["xEnd"]), int(value["yEnd"]),
                ]
                label = str(
                    value.get("name_line")
                    or value.get("nameLine")
                    or value.get("name")
                    or config_key
                )
                Tool_OpenCv2.draw_labeled_roi(
                    output,
                    tuple(shape),
                    label,
                    (255, 0, 0),
                )
                overlay["standard"].setdefault("labels", []).append(label)
                overlay["standard"].setdefault("boxes", []).append(shape)
        elif standard_data is True and len(define_args) == 4:
            x1, y1, x2, y2 = [int(value) for value in define_args]
            label = roi_labels[0] if roi_labels else cls.ROI_DISPLAY_NAMES.get(name, name)
            Tool_OpenCv2.draw_labeled_roi(output, (x1, y1, x2, y2), label)
            overlay["standard"]["labels"] = [label]
            overlay["standard"].setdefault("boxes", []).append([x1, y1, x2, y2])

        polygons = cls._extract_runtime_polygons(runtime_source, comparison_source)
        if polygons:
            drawn_polygons: list[list[list[int]]] = []
            for polygon in polygons:
                polygon_points = cls._points_array(polygon)
                if polygon_points is None or len(polygon_points) < 3:
                    continue
                cv2.polylines(output, [polygon_points], True, (0, 255, 0), 3)
                drawn_polygons.append(polygon_points.reshape(-1, 2).tolist())
            if drawn_polygons:
                overlay["runtime"]["polygons"] = drawn_polygons

        objects = (
            runtime_source.get("objects")
            or comparison_source.get("objects")
            or runtime_source.get("detections")
        )
        if isinstance(objects, list):
            boxes = []
            for obj in objects:
                if not isinstance(obj, dict):
                    continue
                box = obj.get("box") or obj.get("bbox")
                if isinstance(box, dict):
                    bx1 = int(round(float(box.get("x1", 0))))
                    by1 = int(round(float(box.get("y1", 0))))
                    bx2 = int(round(float(box.get("x2", 0))))
                    by2 = int(round(float(box.get("y2", 0))))
                    boxes.append([bx1, by1, bx2, by2])
                elif isinstance(box, (list, tuple)) and len(box) == 4:
                    x1, y1, x2, y2 = [int(float(value)) for value in box]
                    boxes.append([x1, y1, x2, y2])
            if boxes:
                overlay["runtime"]["boxes"] = boxes

        anomaly_boxes = runtime_source.get("anomaly_boxes")
        if isinstance(anomaly_boxes, list) and anomaly_boxes:
            converted_anomaly_boxes = []
            for abox in anomaly_boxes:
                if isinstance(abox, (list, tuple)) and len(abox) == 4:
                    ax, ay, aw, ah = [int(float(v)) for v in abox]
                    converted_anomaly_boxes.append([ax, ay, ax + aw, ay + ah])
            if converted_anomaly_boxes:
                overlay["runtime"]["anomaly_boxes"] = converted_anomaly_boxes

        return output, overlay

    @staticmethod
    def _points_array(value: Any) -> np.ndarray | None:
        """Chuẩn hóa polygon về mảng OpenCV dạng Nx1x2."""
        try:
            array = np.asarray(value, dtype=np.float32).reshape(-1, 1, 2)
            return array.astype(np.int32)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _log_inspector_start(
        index: int,
        name: str,
        image: np.ndarray,
        task: InspectorTask,
    ) -> None:
        """In log đầy đủ trước khi gọi model của một inspector."""
        print(f"[JUDMENT][{index}] START {name}")
        print(
            f"[JUDMENT][{name}] image_shape={image.shape}, "
            f"dtype={image.dtype}"
        )
        print(f"[JUDMENT][{name}] standard_data={Judment._format_log_data(task.standard_data)}")
        print(f"[JUDMENT][{name}] define_args={Judment._format_log_data(task.define_args)}")
        print(f"[JUDMENT][{name}] define_kwargs={Judment._format_log_data(task.define_kwargs)}")
        print(f"[JUDMENT][{name}] compare_kwargs={Judment._format_log_data(task.compare_kwargs)}")

    @staticmethod
    def _log_inspector_result(
        name: str,
        runtime_data: Any,
        comparison_data: Any,
        result: JudgmentResult,
    ) -> None:
        """In log runtime, comparison và kết luận của một inspector."""
        print(f"[JUDMENT][{name}] runtime_data={Judment._format_log_data(runtime_data)}")
        print(f"[JUDMENT][{name}] comparison_data={Judment._format_log_data(comparison_data)}")
        print(
            f"[JUDMENT][{name}] END status={result.status}, "
            f"ok={result.ok}, message={result.message}, errors={result.errors}"
        )

    @staticmethod
    def _format_log_data(value: Any) -> Any:
        """Rút gọn mảng NumPy khi ghi log nhưng giữ nguyên cấu trúc dữ liệu."""
        if isinstance(value, np.ndarray):
            return f"<numpy shape={value.shape} dtype={value.dtype}>"
        if isinstance(value, dict):
            return {
                key: Judment._format_log_data(child)
                for key, child in value.items()
            }
        if isinstance(value, list):
            return [Judment._format_log_data(child) for child in value]
        if isinstance(value, tuple):
            return tuple(Judment._format_log_data(child) for child in value)
        return value

    def judge_image(
        self,
        image: np.ndarray,
        inspectors: Sequence[InspectorTask] | Mapping[str, Any],
        inspector_registry: Mapping[str, BaseJudgerAI] | None = None,
        scale_mm_per_pixel: float = 1.0,
    ) -> dict[str, Any]:
        """Tên gọi thay thế cho ``run_summary`` dành cho luồng production."""
        return self.run_summary(
            image,
            inspectors,
            inspector_registry,
            scale_mm_per_pixel,
        )
