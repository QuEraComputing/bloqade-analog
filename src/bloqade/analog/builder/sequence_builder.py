from bloqade.analog.builder.base import Builder
from bloqade.analog.builder.route import PragmaRoute
from bloqade.analog.ir.control.sequence import SequenceExpr


class SequenceBuilder(PragmaRoute, Builder):
    def __init__(self, sequence: SequenceExpr, parent: Builder):
        super().__init__(parent)
        self._sequence = sequence
