from abc import abstractmethod
from typing import Protocol


class Comparable[T](Protocol):
    """Protocol for annotating comparable types."""

    @abstractmethod
    def __lt__(self: T, other: T) -> bool:
        pass
