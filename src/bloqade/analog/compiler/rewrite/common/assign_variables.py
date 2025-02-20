from typing import Any, Dict

import bloqade.analog.ir.scalar as scalar
import bloqade.analog.ir.control.field as field
import bloqade.analog.ir.control.waveform as waveform
from bloqade.analog.ir.visitor import BloqadeIRTransformer
from bloqade.analog.builder.typing import LiteralType


class AssignBloqadeIR(BloqadeIRTransformer):
    def __init__(self, mapping: Dict[str, LiteralType]):
        self.mapping = dict(mapping)

    def visit_scalar_Variable(self, node: scalar.Variable):
        if node.name in self.mapping:
            return scalar.AssignedVariable(node.name, self.mapping[node.name])

        return node

    def visit_scalar_AssignedVariable(self, node: scalar.AssignedVariable):
        if node.name in self.mapping:
            raise ValueError(f"Variable {node.name} already assigned to {node.value}.")

        return node

    def visit_field_RunTimeVector(self, node: field.RunTimeVector):
        if node.name in self.mapping:
            return field.AssignedRunTimeVector(node.name, self.mapping[node.name])

        return node

    def visit_waveform_Record(self, node: waveform.Record):
        if node.var.name in self.mapping:
            return self.visit(node.waveform)

        return waveform.Record(self.visit(node.waveform), node.var)

    def visit_field_AssignedRunTimeVector(self, node: field.AssignedRunTimeVector):
        if node.name in self.mapping:
            raise ValueError(f"Variable {node.name} already assigned to {node.value}.")

        return node

    def emit(self, node) -> Any:
        return self.visit(node)
