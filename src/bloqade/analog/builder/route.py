from bloqade.analog.builder.drive import Drive
from bloqade.analog.builder.field import Rabi, Field
from bloqade.analog.builder.backend import BackendRoute
from bloqade.analog.builder.pragmas import (
    AddArgs,
    Assignable,
    Parallelizable,
    BatchAssignable,
)
from bloqade.analog.builder.coupling import LevelCoupling


class PulseRoute(Drive, LevelCoupling, Field, Rabi):
    pass


class PragmaRoute(Assignable, BatchAssignable, Parallelizable, AddArgs, BackendRoute):
    pass


class WaveformRoute(PulseRoute, PragmaRoute):
    pass
