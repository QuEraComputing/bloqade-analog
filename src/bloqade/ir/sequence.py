from .pulse import PulseExpr, Pulse
from .scalar import Interval
from .tree_print import Printer

from pydantic.dataclasses import dataclass
from typing import List, Dict


__all__ = [
    "LevelCoupling",
    "rydberg",
    "hyperfine",
    "Sequence",
    "NamedSequence",
]


@dataclass(frozen=True)
class LevelCoupling:
    def children(self):
        return []

    pass


@dataclass(frozen=True)
class RydbergLevelCoupling(LevelCoupling):
    def __repr__(self) -> str:
        return "rydberg"

    def print_node(self):
        return "RydbergLevelCoupling"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(frozen=True)
class HyperfineLevelCoupling(LevelCoupling):
    def __repr__(self) -> str:
        return "hyperfine"

    def print_node(self):
        return "HyperfineLevelCoupling"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


rydberg = RydbergLevelCoupling()
hyperfine = HyperfineLevelCoupling()


@dataclass
class SequenceExpr:
    def append(self, other: "SequenceExpr") -> "SequenceExpr":
        return SequenceExpr.canonicalize(Append([self, other]))

    def name(self, name: str):  # no need to call canonicalize here
        return NamedSequence(self, name)

    def __getitem__(self, s: slice) -> "Slice":
        return self.canonicalize(Slice(self, Interval.from_slice(s)))

    @staticmethod
    def canonicalize(expr: "SequenceExpr") -> "SequenceExpr":
        return expr


@dataclass
class Append(SequenceExpr):
    value: List[SequenceExpr]

    def __repr__(self) -> str:
        return f"sequence.Append(value={self.value!r})"

    def children(self):
        return self.value

    def print_node(self):
        return "Append"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(init=False, repr=False)
class Sequence(SequenceExpr):
    value: dict[LevelCoupling, PulseExpr]

    def __init__(self, seq_pairs: Dict | None = None):
        if seq_pairs is None:
            self.value = {}
            return

        value = {}
        for level_coupling, pulse in seq_pairs.items():
            if not isinstance(level_coupling, LevelCoupling):
                raise TypeError(f"Unexpected type {type(level_coupling)}")

            if isinstance(pulse, PulseExpr):
                value[level_coupling] = pulse
            elif isinstance(pulse, dict):
                value[level_coupling] = Pulse(pulse)
            else:
                raise TypeError(f"Unexpected type {type(pulse)}")
        self.value = value

    def __call__(self, clock_s: float, level_coupling: LevelCoupling, *args, **kwargs):
        return self.value[level_coupling](clock_s, *args, **kwargs)

    def __repr__(self) -> str:
        return f"Sequence({self.value!r})"

    # return annotated version
    def children(self):
        return {
            level_coupling.print_node(): pulse_expr
            for level_coupling, pulse_expr in self.value.items()
        }

    def print_node(self):
        return "Sequence"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass
class NamedSequence(SequenceExpr):
    sequence: SequenceExpr
    name: str

    def __repr__(self) -> str:
        return f"NamedSequence(sequence={self.sequence!r}, name='{self.name!r}')"

    def children(self):
        return {"sequence": self.sequence, "name": self.name}

    def print_node(self):
        return "NamedSequence"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)


@dataclass(repr=False)
class Slice(SequenceExpr):
    sequence: SequenceExpr
    interval: Interval

    def __repr__(self) -> str:
        return f"{self.sequence!r}[{self.interval!r}]"

    def children(self):
        return {"sequence": self.sequence, "interval": self.interval}

    def print_node(self):
        return "Slice"

    def _repr_pretty_(self, p, cycle):
        Printer(p).print(self, cycle)
