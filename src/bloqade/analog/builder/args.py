from beartype import beartype
from beartype.typing import List, Union, Optional

from bloqade.analog.ir.scalar import Variable
from bloqade.analog.builder.base import Builder
from bloqade.analog.builder.backend import BackendRoute
from bloqade.analog.builder.pragmas import Parallelizable


class Args(Parallelizable, BackendRoute, Builder):
    @beartype
    def __init__(
        self, order: List[Union[str, Variable]], parent: Optional[Builder] = None
    ) -> None:
        super().__init__(parent)
        self._order = tuple([o.name if isinstance(o, Variable) else o for o in order])
