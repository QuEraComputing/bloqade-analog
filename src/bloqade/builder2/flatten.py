from typing import List
from .base import Builder
from .pragmas import FlattenParallelizable
from .backend import FlattenedBackendRoute


class Flatten(FlattenParallelizable, FlattenedBackendRoute):
    __match_args__ = ("_orders", "__parent__")

    def __init__(self, orders: List[str], parent: Builder | None = None) -> None:
        super().__init__(parent)
        self._orders = orders
