from abc import ABC,abstractmethod

class BaseAI(ABC):
    @abstractmethod
    def load_model(self):
        # Load
        pass
    @abstractmethod
    def preprocess(self):
        # tiền xử lý
        pass
    @abstractmethod
    def predict(self):
        # du doan
        pass
    @abstractmethod
    def unload(self):
        # giai phong mo hinh tren ram
        pass
    @abstractmethod
    def warmup(self):
        # chạy trước mô hình 1 lần
        pass

     