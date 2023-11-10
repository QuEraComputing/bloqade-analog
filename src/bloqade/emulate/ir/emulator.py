from bloqade.codegen.common.json import WaveformSerializer, BloqadeIRDeserializer
from bloqade.serialize import Serializer
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Tuple, Optional
from enum import Enum
from bloqade.ir.control.waveform import Waveform
from bloqade.emulate.ir.atom_type import AtomType


@dataclass(frozen=True)
@Serializer.register
class CompiledWaveform:
    assignments: Dict[str, Decimal]
    source: Waveform

    def __call__(self, t: float) -> float:
        return self.source(t, **self.assignments)


@CompiledWaveform.set_serializer
def _serialize(obj: CompiledWaveform) -> Dict[str, Any]:
    return {
        "assignments": obj.assignments,
        "source": WaveformSerializer().default(obj.source),
    }


@CompiledWaveform.set_deserializer
def _deserializer(d: Dict[str, Any]) -> CompiledWaveform:
    from json import loads, dumps

    source_str = dumps(d["source"])
    d["source"] = loads(source_str, object_hook=BloqadeIRDeserializer.object_hook)
    return CompiledWaveform(**d)


class RabiOperatorType(int, Enum):
    RabiAsymmetric = 0
    RabiSymmetric = 1


@dataclass(frozen=True)
@Serializer.register
class RabiOperatorData:
    operator_type: RabiOperatorType
    target_atoms: Dict[int, Decimal]

    def __hash__(self):
        return hash(self.operator_type) ^ hash(frozenset(self.target_atoms.items()))


@RabiOperatorData.set_deserializer
def _deserializer(d: Dict[str, Any]) -> RabiOperatorData:
    d["target_atoms"] = {int(k): v for k, v in d["target_atoms"].items()}
    return RabiOperatorData(**d)


@dataclass(frozen=True)
@Serializer.register
class RabiTerm:
    operator_data: RabiOperatorData
    amplitude: CompiledWaveform
    phase: Optional[CompiledWaveform] = None


@dataclass(frozen=True)
@Serializer.register
class DetuningOperatorData:
    target_atoms: Dict[int, Decimal]

    def __hash__(self) -> int:
        return hash(frozenset(self.target_atoms.items()))


@DetuningOperatorData.set_deserializer
def _deserializer(d: Dict[str, Any]) -> DetuningOperatorData:
    d["target_atoms"] = {int(k): v for k, v in d["target_atoms"].items()}
    return DetuningOperatorData(**d)


@dataclass(frozen=True)
@Serializer.register
class DetuningTerm:
    operator_data: DetuningOperatorData
    amplitude: CompiledWaveform


@dataclass(frozen=True)
@Serializer.register
class Fields:
    detuning: List[DetuningTerm]
    rabi: List[RabiTerm]


@dataclass(frozen=True)
@Serializer.register
class Register:
    """This class represents the of the atoms in the system."""

    atom_type: AtomType
    sites: List[Tuple[Decimal, Decimal]]
    blockade_radius: Decimal

    def __len__(self):
        return len(self.sites)

    def __eq__(self, other: Any):
        if isinstance(other, Register):
            return (
                self.atom_type == other.atom_type
                and self.blockade_radius == other.blockade_radius
                and set(self.sites) == set(other.sites)
            )

        return False

    def __hash__(self) -> int:
        if self.blockade_radius == Decimal("0"):
            # if blockade radius is zero, then the positions are irrelevant
            # because the fock states generated by the geometry are the same
            return hash(self.__class__) ^ hash(self.atom_type) ^ hash(len(self.sites))
        else:
            # if blockade radius is non-zero, then the positions are relevant
            # because depending on the location of the atoms and the blockade
            # radius, the fock states generated by the geometry are different
            return (
                hash(self.__class__)
                ^ hash(self.atom_type)
                ^ hash(self.blockade_radius)
                ^ hash(frozenset(self.sites))
            )


@Register.set_deserializer
def _deserializer(d: Dict[str, Any]) -> Register:
    d["sites"] = [tuple(map(Decimal, map(str, site))) for site in d["sites"]]

    return Register(**d)


class LevelCoupling(str, Enum):
    Rydberg = "rydberg"
    Hyperfine = "hyperfine"


@dataclass(frozen=True)
@Serializer.register
class EmulatorProgram:
    register: Register
    duration: float
    pulses: Dict[LevelCoupling, Fields]


@EmulatorProgram.set_deserializer
def _deserializer(d: Dict[str, Any]) -> EmulatorProgram:
    d["duration"] = float(d["duration"])
    return EmulatorProgram(**d)


class Visitor:
    def visit_emulator_program(self, ast: EmulatorProgram) -> Any:
        raise NotImplementedError

    def visit_compiled_waveform(self, ast: CompiledWaveform) -> Any:
        raise NotImplementedError

    def visit_fields(self, ast: Fields) -> Any:
        raise NotImplementedError

    def visit_detuning_operator_data(self, ast: DetuningOperatorData) -> Any:
        raise NotImplementedError

    def visit_rabi_operator_data(self, ast: RabiOperatorData) -> Any:
        raise NotImplementedError

    def visit_detuning_term(self, ast: DetuningTerm) -> Any:
        raise NotImplementedError

    def visit_rabi_term(self, ast: RabiTerm) -> Any:
        raise NotImplementedError

    def visit_register(self, ast: Register) -> Any:
        raise NotImplementedError

    def visit(self, ast) -> Any:
        if isinstance(ast, EmulatorProgram):
            return self.visit_emulator_program(ast)
        elif isinstance(ast, Register):
            return self.visit_register(ast)
        elif isinstance(ast, Fields):
            return self.visit_fields(ast)
        elif isinstance(ast, RabiTerm):
            return self.visit_rabi_term(ast)
        elif isinstance(ast, DetuningTerm):
            return self.visit_detuning_term(ast)
        elif isinstance(ast, RabiOperatorData):
            return self.visit_rabi_operator_data(ast)
        elif isinstance(ast, DetuningOperatorData):
            return self.visit_detuning_operator_data(ast)
        elif isinstance(ast, CompiledWaveform):
            return self.visit_compiled_waveform(ast)
        else:
            raise NotImplementedError(f"Unknown AST node type {type(ast)}: {ast!r}")
