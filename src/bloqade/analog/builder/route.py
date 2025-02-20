from bloqade_analog.builder.drive import Drive
from bloqade_analog.builder.coupling import LevelCoupling
from bloqade_analog.builder.field import Field, Rabi
from bloqade_analog.builder.pragmas import (
    Assignable,
    BatchAssignable,
    Parallelizable,
    AddArgs,
)
from bloqade_analog.builder.backend import BackendRoute


class PulseRoute(Drive, LevelCoupling, Field, Rabi):
    pass


class PragmaRoute(Assignable, BatchAssignable, Parallelizable, AddArgs, BackendRoute):
    pass


class WaveformRoute(PulseRoute, PragmaRoute):
    pass
