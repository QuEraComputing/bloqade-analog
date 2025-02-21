import bloqade.analog.ir.location as location
from bloqade.analog.ir import Linear

(
    location.Square(3)
    .rydberg.detuning.uniform.apply(Linear(start=1.0, stop="x", duration=3.0))
    .location(2)
    .scale(3.0)
    .apply(Linear(start=1.0, stop="x", duration=3.0))
)

(
    location.Square(3)
    .rydberg.detuning.uniform.apply(Linear(start=1.0, stop="x", duration=3.0))
    .location(2)
    .scale(3.0)
    .apply(Linear(start=1.0, stop="x", duration=3.0))
)
