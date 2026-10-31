from abc import ABC, abstractmethod
class BaseConfig(ABC):
    @abstractmethod
    def load(self):
        pass
    @abstractmethod
    def save(self):
        pass