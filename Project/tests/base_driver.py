from abc import ABC, abstractmethod
from typing import List, Dict

class BaseDriver(ABC):
    def __init__(self, host: str, port: int, table: str, **kwargs):
        self.host = host
        self.port = port
        self.table = table
        self.kwargs = kwargs

    @abstractmethod
    def connect(self): ...

    @abstractmethod
    def prepare_schema(self): ...

    @abstractmethod
    def insert_batch(self, batch: List[Dict]) -> int:
        """Return rows actually inserted."""
        ...

    @abstractmethod
    def close(self): ...