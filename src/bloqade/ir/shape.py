from pydantic.dataclasses import dataclass
from typing import List

from bloqade.ir.scalar import Scalar


@dataclass(frozen=True)
class Shape:
    """
    <shape> ::= <linear shape>
      | <constant shape>
      | <poly>
    """

    pass


@dataclass(frozen=True)
class Linear(Shape):
    """
    <linear shape> ::= 'linear' <scalar expr> <scalar expr>
    """

    start: Scalar
    stop: Scalar


@dataclass(frozen=True)
class Constant(Shape):
    """
    <constant shape> ::= 'constant' <scalar expr>
    """

    value: Scalar


@dataclass(frozen=True)
class Poly(Shape):
    """
    <poly> ::= <scalar expr> | <poly> <scalar expr>
    """

    checkpoints: List[Scalar]
