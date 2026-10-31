from queue import Queue
from typing import Any
from queue import Queue, Empty, Full
# =========================================
# Queue Manager
# =========================================
class QueueManager:
    def __init__(self):
        self.queues: dict[str, Queue[Any]] = {}

    def create_queue(
        self,
        name: str,
        maxsize: int = 0
    ) -> Queue[Any]:

        if name not in self.queues:
            self.queues[name] = Queue(maxsize=maxsize)

        return self.queues[name]

# =========================================
# Worker
# =========================================
class Worker:
    def __init__(self, q: Queue[Any]):
        self.q = q
    # =========================
    # PUT
    # =========================
    def put(
        self,
        data: Any,
        block: bool = False,
        timeout: float | None = None
    ) -> bool:
        try:
            self.q.put(
                data,
                block=block,
                timeout=timeout
            )
            return True

        except Full:
            import logging
            logging.getLogger(__name__).warning("⚠️ [Worker] Hàng đợi đã đầy (maxsize=%s), dữ liệu đã bị bỏ rơi (dropped)!", getattr(self.q, "maxsize", "unknown"))
            return False

    # =========================
    # GET NOWAIT
    # =========================
    def get(self) -> Any | None:
        try:
            return self.q.get_nowait()

        except Empty:
            return None

    # =========================
    # GET TIMEOUT
    # =========================
    def get_timeout(
        self,
        timeout: float | None = None
    ) -> Any | None:

        try:
            return self.q.get(timeout=timeout)

        except Empty:
            return None

    # =========================
    # CLEAR
    # =========================
    def clear(self) -> None:
        with self.q.mutex:
            self.q.queue.clear()

    # =========================
    # SIZE
    # =========================
    def size(self) -> int:
        return self.q.qsize()

    # =========================
    # EMPTY
    # =========================
    def empty(self) -> bool:
        return self.q.empty()

    # =========================
    # FULL
    # =========================
    def full(self) -> bool:
        return self.q.full()