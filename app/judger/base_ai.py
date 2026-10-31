from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True)
class JudgmentResult:
    """Dữ liệu đầy đủ của một lần phán định AI."""

    ok: bool
    status: str
    standard_data: Any = None
    runtime_data: Any = None
    comparison_data: Any = None
    message: str = ""
    errors: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển kết quả phán định sang dictionary dùng cho API hoặc log."""
        return asdict(self)


class BaseJudgerAI(ABC):
    """Hợp đồng chung cho các lớp AI phán định trong structure.

    Mỗi lớp con bắt buộc tự cài đặt ba bước:
    ``define`` để lấy dữ liệu từ ảnh hoặc input runtime, ``compare`` để so
    sánh dữ liệu chuẩn với dữ liệu runtime, và ``judge`` để kết luận OK/NG.
    Lớp base chỉ định nghĩa hợp đồng, không áp đặt cách xử lý riêng của từng
    bài toán detection, segmentation hoặc measurement.
    """

    INSPECTOR_NAME: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Kiểm tra mỗi judger con khai báo tên inspector riêng.

        Input: ``cls`` là lớp judger con đang được tạo.
        Output: Không trả về dữ liệu.
        Errors: ``TypeError`` nếu lớp con không khai báo ``INSPECTOR_NAME``
            hoặc tên inspector không phải chuỗi không rỗng.
        """
        super().__init_subclass__(**kwargs)
        inspector_name = cls.__dict__.get("INSPECTOR_NAME")
        if not isinstance(inspector_name, str) or not inspector_name.strip():
            raise TypeError(
                f"{cls.__name__} phải khai báo INSPECTOR_NAME riêng"
            )

    @classmethod
    def get_inspector_name(cls) -> str:
        """Lấy tên inspector cấu hình của judger.

        Input: Không có.
        Output: Tên key inspector dùng trong cấu hình judgment.
        Errors: Không phát sinh vì tên đã được kiểm tra khi tạo class.
        """
        return cls.INSPECTOR_NAME

    def evaluate(self, standard_data: Any, *args: Any, **kwargs: Any) -> JudgmentResult:
        """Thực hiện đầy đủ quy trình define, compare và judge.

        Input:
            standard_data: Dữ liệu chuẩn dùng để phán định.
            args, kwargs: Dữ liệu đầu vào được truyền cho ``define``.
        Output:
            ``JudgmentResult`` chứa dữ liệu runtime, dữ liệu so sánh và trạng
            thái ``OK`` hoặc ``NG``.
        Errors:
            Lỗi từ ``define`` hoặc ``compare`` được truyền ra ngoài; phát sinh
            ``TypeError`` nếu ``judge`` không trả về ``JudgmentResult``.
        """
        runtime_data = self.define(*args, **kwargs)
        comparison_data = self.compare(standard_data, runtime_data)
        result = self.judge(comparison_data)
        if not isinstance(result, JudgmentResult):
            raise TypeError("judge() phải trả về JudgmentResult")
        return result

    @abstractmethod
    def define(self, *args: Any, **kwargs: Any) -> Any:
        """Xác định dữ liệu runtime từ input của bài toán."""
        raise NotImplementedError

    @abstractmethod
    def compare(self, standard_data: Any, runtime_data: Any) -> Any:
        """So sánh dữ liệu chuẩn với dữ liệu runtime."""
        raise NotImplementedError

    @abstractmethod
    def judge(self, comparison_data: Any) -> JudgmentResult:
        """Phán định dữ liệu đã so sánh và trả về đầy đủ dữ liệu OK/NG."""
        raise NotImplementedError
