from bloqade_analog.ir.control.sequence import SequenceExpr
from bloqade_analog.builder.route import PragmaRoute
from bloqade_analog.builder.base import Builder


class SequenceBuilder(PragmaRoute, Builder):
    def __init__(self, sequence: SequenceExpr, parent: Builder):
        super().__init__(parent)
        self._sequence = sequence
