from bloqade.ir import (
    Field,
    Uniform,
    Linear,
    ScaledLocations,
    Location,
    SpatialModulation,
    RunTimeVector,
)
import pytest
from bloqade import cast
from io import StringIO
from IPython.lib.pretty import PrettyPrinter as PP


def test_location():
    loc = Location(3)

    assert loc.__repr__() == "Location(3)"
    assert loc.print_node() == "Location 3"
    assert loc.children() == []


def test_spacmod_base():
    x = SpatialModulation()

    with pytest.raises(NotImplementedError):
        hash(x)


def test_unform():
    x = Uniform

    assert x.__repr__() == "Uniform"
    assert x.print_node() == "UniformModulation"
    assert x.children() == []

    mystdout = StringIO()
    p = PP(mystdout)

    x._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "UniformModulation\n"


def test_runtime_vec():
    x = RunTimeVector("sss")

    assert x.__repr__() == "RunTimeVector('sss')"
    assert x.print_node() == "RunTimeVector"
    assert x.children() == ["sss"]

    mystdout = StringIO()
    p = PP(mystdout)

    x._repr_pretty_(p, 0)

    assert mystdout.getvalue() == "RunTimeVector\n" + "└─ sss\n"


def test_scal_loc():
    x = ScaledLocations({1: 1.0, 2: 2.0})

    with pytest.raises(ValueError):
        ScaledLocations({(2, 3): 2})

    assert x.print_node() == "ScaledLocations"
    assert x.children() == {"Location 1": cast(1.0), "Location 2": cast(2.0)}

    mystdout = StringIO()
    p = PP(mystdout)

    x._repr_pretty_(p, 0)

    assert (
        mystdout.getvalue()
        == "ScaledLocations\n"
        + "├─ Location 1 ⇒ Literal: 1.0\n"
        + "⋮\n"
        + "└─ Location 2 ⇒ Literal: 2.0⋮\n"
    )


def test_field():
    Loc = ScaledLocations({1: 1.0, 2: 2.0})
    Loc2 = ScaledLocations({3: 1.0, 4: 2.0})
    f1 = Field({Loc: Linear(start=1.0, stop="x", duration=3.0)})
    f2 = Field({Loc: Linear(start=1.0, stop="x", duration=3.0)})
    f3 = Field({Loc2: Linear(start=1.0, stop="x", duration=3.0)})

    # add with non field
    with pytest.raises(ValueError):
        f1.add(Loc)

    mystdout = StringIO()
    p = PP(mystdout)

    f1._repr_pretty_(p, 10)

    assert (
        mystdout.getvalue()
        == "Field\n"
        + "└─ ScaledLocations ⇒ Linear\n"
        + "                     ├─ start ⇒ Literal: 1.0\n"
        + "                     ├─ stop ⇒ Variable: x\n"
        + "                     └─ duration ⇒ Literal: 3.0"
    )

    # add with field same spat-mod
    o1 = f1.add(f2)
    assert len(o1.value.keys()) == 1

    # add with field diff spat-mod
    o2 = f1.add(f3)
    assert len(o2.value.keys()) == 2

    assert f2.print_node() == "Field"
    # assert type(hash(f1)) == int
    assert f1.children() == {
        "ScaledLocations": Linear(start=1.0, stop=cast("x"), duration=3.0)
    }
