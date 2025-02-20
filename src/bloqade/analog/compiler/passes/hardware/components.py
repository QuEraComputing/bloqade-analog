from decimal import Decimal

from beartype.typing import List, Optional
from pydantic.v1.dataclasses import dataclass

from bloqade.analog.compiler.codegen.hardware.lattice import AHSLatticeData
from bloqade.analog.compiler.codegen.hardware.piecewise_linear import PiecewiseLinear
from bloqade.analog.compiler.codegen.hardware.piecewise_constant import (
    PiecewiseConstant,
)


@dataclass
class AHSComponents:
    lattice_data: AHSLatticeData
    global_detuning: PiecewiseLinear
    global_amplitude: PiecewiseLinear
    global_phase: PiecewiseConstant
    local_detuning: Optional[PiecewiseLinear]
    lattice_site_coefficients: Optional[List[Decimal]]
