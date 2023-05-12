from .base import Builder
from .coupling import Rydberg, Hyperfine


class ProgramStart(Builder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def rydberg(self):
        return Rydberg(self)

    @property
    def hyperfine(self):
        return Hyperfine(self)
