from pydantic.dataclasses import dataclass
from typing import Dict, List, Optional, Callable

from bloqade.ir.control.sequence import LevelCoupling
from bloqade.emulator.space import Space


@dataclass
class RabiTerm:
    phase: Optional[Callable[[float], float]] = None
    amplitude: Callable[[float], float]
    target_atoms: Dict[int, float]


@dataclass
class DetuningTerm:
    target_atoms: Dict[int, float]
    amplitude: Callable[[float], float]


@dataclass
class LaserCoupling:
    level_coupling: LevelCoupling
    detuning: List[DetuningTerm]
    rabi: List[RabiTerm]


@dataclass
class EmulatorProgram:
    space: Space
    rydberg: Optional[LaserCoupling] = None
    hyperfine: Optional[LaserCoupling] = None
