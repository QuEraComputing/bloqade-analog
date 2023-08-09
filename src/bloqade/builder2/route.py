from .start import ProgramStart
from .coupling import LevelCoupling
from .field import Field, Rabi
from .pragmas import Assignable, Parallelizable, Flattenable
from .backend import SubmitBackendRoute


class PulseRoute(ProgramStart, LevelCoupling, Field, Rabi):
    pass


class PragmaRoute(Assignable, Parallelizable, Flattenable, SubmitBackendRoute):
    pass


class WaveformRoute(PulseRoute, PragmaRoute):
    pass
