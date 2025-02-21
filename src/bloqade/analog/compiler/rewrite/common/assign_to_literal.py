import bloqade.analog.ir.scalar as scalar
from bloqade.analog.ir.control import waveform
from bloqade.analog.ir.visitor import BloqadeIRTransformer


class AssignToLiteral(BloqadeIRTransformer):
    """Transform all assigned variables to literals."""

    def visit_scalar_AssignedVariable(self, node: scalar.AssignedVariable):
        return scalar.Literal(node.value)

    def visit_waveform_PythonFn(self, node: waveform.PythonFn):
        return node  # skip these nodes
