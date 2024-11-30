from abc import ABC, abstractmethod
from typing import Any


class DataTransformer(ABC):
    @abstractmethod
    async def transform(self, data: Any) -> str:
        """Transform input data into string format."""
        pass
