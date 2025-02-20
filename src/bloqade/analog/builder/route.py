from bloqade.analog.builder.drive import Drive
from bloqade.analog.builder.coupling import LevelCoupling
from bloqade.analog.builder.field import Field, Rabi
from bloqade.analog.builder.pragmas import (
    Assignable,
    BatchAssignable,
    Parallelizable,
    AddArgs,
)
from bloqade.analog.builder.backend import BackendRoute


class PulseRoute(Drive, LevelCoupling, Field, Rabi):
    pass


class PragmaRoute(Assignable, BatchAssignable, Parallelizable, AddArgs, BackendRoute):
    pass


class WaveformRoute(PulseRoute, PragmaRoute):
    pass
