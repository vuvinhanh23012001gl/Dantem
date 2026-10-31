"""Worker chạy train PatchCore trên thread riêng."""

from dataclasses import dataclass
from queue import Empty, Queue
import threading
from pathlib import Path
from typing import Any, Callable

from app.config import PatchCoreTrainConfig
from app.engines.train.patchcore_train_model.trainler import TrainlerPatchCore


@dataclass(frozen=True)
class PatchCoreTrainRequest:
    """Thông tin một yêu cầu train đang chờ xử lý."""

    model_root: str | Path
    roi_name: str
    purpose: str
    image_count: int
    config: PatchCoreTrainConfig | None
    model_variant: str


class TrainWorkerPatchCore:
    """Nhận ảnh qua queue và train PatchCore trên thread nền.

    Worker không chặn luồng chính: caller gọi ``start()``, gửi đủ số ảnh qua
    ``submit_image()``, rồi đọc kết quả từ ``result_queue``.
    """

    def __init__(self, record_manager=None):
        """Khởi tạo worker chỉ chứa quy tắc xử lý queue.

        Args:
            record_manager: Repository manifest truyền cho trainer của worker.
        """
        self.trainer_factory = None
        self.image_queue = None
        self.result_queue = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.record_manager = record_manager

    def start(
        self,
        model_root: str | Path,
        roi_name: str = "patchcore",
        purpose: str = "train patchcore",
        image_count: int = 1,
        config: PatchCoreTrainConfig | None = None,
        model_variant: str = "the_first",
        trainer_factory: Callable[[PatchCoreTrainConfig | None], TrainlerPatchCore] | None = None,
        image_queue: Queue | None = None,
        result_queue: Queue | None = None,
    ) -> None:
        """Bắt đầu một phiên train trên thread nền.

        Args:
            model_root: Folder gốc lưu ảnh và model.
            roi_name: Tên vùng train.
            purpose: Mục đích train.
            image_count: Số ảnh cần nhận từ image_queue.
            config: Cấu hình train của phiên.
            model_variant: Nhánh session train: ``the_first`` hoặc ``runtime``.
            trainer_factory: Factory tạo trainer; mặc định dùng manifest worker.
            image_queue: Queue nhận ảnh train.
            result_queue: Queue trả kết quả train.
        Raises:
            ValueError: Nếu image_count nhỏ hơn 1 hoặc worker đang chạy.
        """
        if self._thread is not None and self._thread.is_alive():
            raise ValueError("Worker đang chạy một phiên train khác")
        if image_count < 1:
            raise ValueError("image_count phải lớn hơn 0")
        self.trainer_factory = trainer_factory or (
            lambda train_config: TrainlerPatchCore(train_config, self.record_manager)
        )
        self.image_queue = image_queue or Queue()
        self.result_queue = result_queue or Queue()
        request = PatchCoreTrainRequest(
            model_root, roi_name, purpose, image_count, config, model_variant
        )
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_request,
            args=(request,),
            name="patchcore-train-worker",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout: float | None = 2.0) -> None:
        """Dừng thread worker sau khi xử lý các queue đang chờ.

        Args:
            timeout: Thời gian tối đa chờ thread dừng.

        Returns:
            None.
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def submit_image(self, image: Any) -> None:
        """Đưa một ảnh vào queue train.

        Args:
            image: PIL.Image, NumPy array hoặc bytes được trainer hỗ trợ.

        Returns:
            None.
        """
        if self.image_queue is None or self._thread is None or not self._thread.is_alive():
            raise RuntimeError("Worker chưa chạy phiên train")
        self.image_queue.put(image)

    def get_result(self, timeout: float | None = None) -> dict:
        """Lấy kết quả train hoặc lỗi từ result_queue.

        Args:
            timeout: Thời gian tối đa chờ kết quả.

        Returns:
            dict: ``{"ok": True, "record": ...}`` hoặc ``{"ok": False, "error": ...}``.

        Raises:
            queue.Empty: Nếu hết timeout mà chưa có kết quả.
        """
        if self.result_queue is None:
            raise RuntimeError("Worker chưa được start")
        return self.result_queue.get(timeout=timeout)

    def _run_request(self, request: PatchCoreTrainRequest) -> None:
        """Chạy một request train trên thread nền.

        Returns:
            None.
        """
        try:
            images = self._collect_images(request.image_count)
            if images is None:
                return
            trainer = self.trainer_factory(request.config)
            record = trainer.run_from_folder(
                images,
                request.model_root,
                roi_name=request.roi_name,
                purpose=request.purpose,
                model_variant=request.model_variant,
            )
            self.result_queue.put({"ok": True, "record": record})
        except Exception as error:
            self.result_queue.put({"ok": False, "error": error})

    def _collect_images(self, image_count: int) -> list[Any] | None:
        """Lấy đủ ảnh từ queue hoặc dừng nếu worker nhận tín hiệu stop.

        Args:
            image_count: Số ảnh cần lấy.

        Returns:
            list[Any] | None: Danh sách ảnh đủ số lượng hoặc None khi dừng.
        """
        images = []
        while len(images) < image_count and not self._stop_event.is_set():
            try:
                images.append(self.image_queue.get(timeout=0.1))
            except Empty:
                continue
        return images if len(images) == image_count else None
