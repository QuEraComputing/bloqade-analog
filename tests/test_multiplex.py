from bloqade.lattice import Square
from bloqade.lattice.multiplex import multiplex_program
from bloqade.hardware.capabilities import Capabilities
from bloqade.task import Program
from bloqade.codegen.quera_hardware import SchemaCodeGen

from bloqade.ir import (
    rydberg,
    detuning,
    Sequence,
    Uniform,
    Linear,
    ScaledLocations,
)


# create lattice
lattice = Square(4)

# create some test sequence
seq = Sequence(
    {
        rydberg: {
            detuning: {
                Uniform: Linear(start=1.0, stop=5.2, duration=3.0),
                ScaledLocations({1: 1.0, 2: 2.0, 3: 3.0, 4: 4.0}): Linear(
                    start=1.0, stop=5.2, duration=3.0
                ),
            },
        }
    }
)


prog = Program(lattice, seq, {})

# need to provide capabilities and problem spacing
cap = Capabilities(num_sites_max=256, max_height=75, max_width=75)

cluster_spacing = 2.0  # 1.0 micrometers

# can remove multiplex_enabled flag in favor of checking presence of mapping attribute
multiplexed_prog = multiplex_program(prog, cap, cluster_spacing)

# call codegen
generated_schema = SchemaCodeGen().emit(100, multiplexed_prog)
