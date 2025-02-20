from typing import Dict
from decimal import Decimal

import bloqade.analog.ir.control.waveform as waveform
from bloqade.analog.ir.visitor import BloqadeIRVisitor
from bloqade.analog.builder.typing import LiteralType


class AssignmentScan(BloqadeIRVisitor):
    def __init__(self, assignments: Dict[str, LiteralType] = {}):
        self.assignments = dict(assignments)

    def visit_waveform_Record(self, node: waveform.Record):
        self.visit(node.waveform)
        duration = node.waveform.duration(**self.assignments)
        var = node.var

        if node.side is waveform.Side.Right:
            value = node.waveform.eval_decimal(duration, **self.assignments)
        else:
            value = node.waveform.eval_decimal(Decimal(0), **self.assignments)

        self.assignments[var.name] = value

    def scan(self, node) -> Dict[str, LiteralType]:
        self.visit(node)
        return self.assignments
