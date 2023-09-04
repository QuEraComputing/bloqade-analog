from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum
from bloqade.ir.control.sequence import LevelCoupling
from bloqade.emulate.ir.space import AtomType


class RabiOperatorType(Enum):
    Rabi = 0
    RabiSymmetric = 1


@dataclass(frozen=True)
class RabiOperatorData:
    operator_type: RabiOperatorType
    target_atoms: Dict[int, Decimal]


@dataclass(frozen=True)
class RabiTerm:
    operator_data: RabiOperatorData
    amplitude: Callable[[float], float]
    phase: Optional[Callable[[float], float]] = None


@dataclass(frozen=True)
class DetuningOperatorData:
    target_atoms: Dict[int, Decimal]


@dataclass(frozen=True)
class DetuningTerm:
    operator_data: DetuningOperatorData
    amplitude: Callable[[float], float]


@dataclass(frozen=True)
class LaserCoupling:
    detuning: List[DetuningTerm]
    rabi: List[RabiTerm]


@dataclass(frozen=True)
class Geometry:
    atom_type: AtomType
    positions: List[Tuple[Decimal, Decimal]]
    blockade_radius: Decimal

    def __len__(self):
        return len(self.positions)

    def __hash__(self) -> int:
        if self.blockade_radius == Decimal("0"):
            return hash(self.atom_type) ^ hash(len(self.positions))
        else:
            return (
                hash(self.atom_type)
                ^ hash(self.blockade_radius)
                ^ hash(tuple(self.positions))
            )


@dataclass(frozen=True)
class EmulatorProgram:
    geometry: Geometry
    duration: float
    drives: Dict[LevelCoupling, LaserCoupling]


class Visitor:
    def visit_emulator_program(self, ast):
        raise NotImplementedError

    def visit_laser_coupling(self, ast):
        raise NotImplementedError

    def visit_detuning_operator_data(self, ast):
        raise NotImplementedError

    def visit_rabi_operator_data(self, ast):
        raise NotImplementedError

    def visit_detuning_term(self, ast):
        raise NotImplementedError

    def visit_rabi_term(self, ast):
        raise NotImplementedError

    def visit_geometry(self, ast):
        raise NotImplementedError

    def visit(self, ast):
        match ast:
            case EmulatorProgram():
                return self.visit_emulator_program(ast)
            case Geometry():
                return self.visit_geometry(ast)
            case LaserCoupling():
                return self.visit_laser_coupling(ast)
            case DetuningOperatorData():
                return self.visit_detuning_operator_data(ast)
            case RabiOperatorData():
                return self.visit_rabi_operator_data(ast)
            case DetuningTerm():
                return self.visit_detuning_term(ast)
            case RabiTerm():
                return self.visit_rabi_term(ast)
