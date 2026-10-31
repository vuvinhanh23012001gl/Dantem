from .erro_code import ERROR_MESSAGE
class Result:
    def __init__(self, ok: bool, data=None, error=None):
        self.ok = ok
        self.data = data
        self.error = error

    @staticmethod
    def Ok(data=None):
        return Result(True, data=data)

    @staticmethod
    def Fail(error):
        return Result(False, error=error)

    def message(self):
        if self.error is None:
            return None
        if isinstance(self.error, str):
            return self.error
        return ERROR_MESSAGE.get(self.error, str(self.error))

    def __repr__(self):
        if self.ok:
            return f"<Result OK data={type(self.data)}>"
        return f"<Result FAIL error={self.error}>"
    
    def to_dict(self):
        is_enum = hasattr(self.error, "value")
        return {
            "ok": self.ok,
            "data": self.data,
            "error_code": self.error.value if is_enum else None,
            "error_name": self.error.name if is_enum else None,
            "message": self.message()
        }