from decimal import Decimal

from bloqade.analog import cast
from bloqade.analog.ir import scalar
from bloqade.analog.compiler.rewrite.common.assign_variables import AssignBloqadeIR
from bloqade.analog.compiler.rewrite.common.assign_to_literal import AssignToLiteral


def test_assign_to_literal():
    a = cast("a")
    b = cast("b")
    c = cast("c")

    expr = (a - b) * c / 2.0

    a = Decimal("1.0")
    b = Decimal("2.0")
    c = Decimal("3.0")

    assigned_expr = AssignBloqadeIR(dict(a=a, b=b, c=c)).visit(expr)

    assert AssignToLiteral().visit(assigned_expr) == scalar.Div(
        scalar.Mul(
            scalar.Add(scalar.Literal(a), scalar.Negative(scalar.Literal(b))),
            scalar.Literal(c),
        ),
        scalar.Literal(2.0),
    )
