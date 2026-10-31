from typing import Any
from app.core import Result
from app.core import ErrorCode

class ValidateToolLawRegulation:
    @staticmethod
    def validate_levels(data: dict[str, Any]) -> Result:
        int_keys = ["product", "frame", "items"]
        result = {}
        for key in int_keys:
            if key not in data:
                return Result.Fail(ErrorCode.INVALID_INPUT)
            value = data[key]
            if isinstance(value, bool):
                return Result.Fail(ErrorCode.INVALID_INPUT)
            try:
                result[key] = int(value)
            except (TypeError, ValueError):
                return Result.Fail(ErrorCode.INVALID_INPUT)
        # Validate Level1 -> Level5
        level_keys = [
            "Level1_auto",
            "Level2_auto",
            "Level3_auto",
            "Level4_auto",
            "Level5_auto",
        ]
        levels = []
        for key in level_keys:
            if key not in data:
                return Result.Fail(ErrorCode.INVALID_INPUT)
            value = data[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return Result.Fail(ErrorCode.INVALID_INPUT)
            levels.append(float(value))
        for i in range(len(levels) - 1):
            if levels[i] >= levels[i + 1]:
                return Result.Fail(ErrorCode.INVALID_INPUT)
        result["levels"] = levels
        return Result.Ok(result)
    
    @staticmethod
    def validate_judment_item(data: dict) -> Result:
        # 1. Kiểm tra xem dữ liệu truyền vào có hợp lệ và có chứa key 'select' hay không
        if not isinstance(data, dict) or "select" not in data:
            return Result.Fail(ErrorCode.INVALID_FORMAT) # Thay bằng Enum lỗi tương ứng của bạn
        select_data = data["select"]
        if not isinstance(select_data, dict):
            return Result.Fail(ErrorCode.INVALID_FORMAT)
        required_fields = ["product_id", "frame_id", "items_id"]
        # 2. Kiểm tra sự tồn tại của các trường bắt buộc trong 'select'
        for field in required_fields:
            if field not in select_data:
                # Bạn nên định nghĩa các mã lỗi Enum rõ ràng trong file erro_code.py của mình
                # Ví dụ dưới đây giả định bạn có các mã lỗi này:
                return Result.Fail(ErrorCode.MISSING_FIELD) 
        # 3. Ép kiểu và kiểm tra giá trị hợp lệ
        for field in required_fields:
            try:
                value = int(select_data[field])
            except (TypeError, ValueError):
                return Result.Fail(ErrorCode.INVALID_TYPE)
            if value == -1:
                return Result.Fail(ErrorCode.INVALID_VALUE)
        return Result.Ok()