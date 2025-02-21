from typing import List, Union, Optional
from numbers import Real

from bloqade.analog.builder.parse.trait import Show, Parse

ParamType = Union[Real, List[Real]]


class Builder(Parse, Show):
    def __init__(
        self,
        parent: Optional["Builder"] = None,
    ) -> None:
        self.__parent__ = parent

    def __str__(self):
        return str(self.parse())
