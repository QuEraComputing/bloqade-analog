from bloqade.ir import (
    rydberg,
    detuning,
    hyperfine,
    Sequence,
    Field,
    Pulse,
    Uniform,
    Linear,
    ScaledLocations,
    LevelCoupling,
)
from bloqade.ir.control.sequence import NamedSequence
from bloqade.ir import Interval
import pytest
from bloqade import cast


def test_lvlcouple_base():
    lc = LevelCoupling()
    assert lc.children() == []


def test_lvlcouple_hf():
    lc = hyperfine

    assert lc.print_node() == "HyperfineLevelCoupling"
    assert lc.__repr__() == "hyperfine"


def test_lvlcouple_ryd():
    lc = rydberg

    assert lc.print_node() == "RydbergLevelCoupling"
    assert lc.__repr__() == "rydberg"


def test_seqence():
    # seq empty
    seq = Sequence()
    assert seq.value == {}

    # seq non-lvlcoupling:
    with pytest.raises(TypeError):
        Sequence({"c": {}})

    # seq non-lvlcoupling:
    with pytest.raises(TypeError):
        Sequence({rydberg: 3.3})

    # seq full
    f = Field({Uniform: Linear(start=1.0, stop="x", duration=3.0)})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})

    assert seq_full.children() == {"RydbergLevelCoupling": ps}
    assert seq_full.print_node() == "Sequence"

    # named seq:
    named = NamedSequence(seq_full, "qq")

    assert named.children() == {"sequence": seq_full, "name": "qq"}
    assert named.print_node() == "NamedSequence"


def test_slice_sequence():
    f = Field({Uniform: Linear(start=1.0, stop=2.0, duration=3.0)})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})
    itvl = Interval(cast(0), cast(1.5))

    # slice:
    slc = seq_full[0:1.5]

    assert slc.children() == {"sequence": seq_full, "interval": itvl}
    assert slc.print_node() == "Slice"


def test_append_sequence():
    f = Field({Uniform: Linear(start=1.0, stop=2.0, duration=3.0)})
    ps = Pulse({detuning: f})
    seq_full = Sequence({rydberg: ps})

    app = seq_full.append(seq_full)

    assert app.children() == [seq_full, seq_full]
    assert app.print_node() == "Append"


seq = Sequence(
    {
        rydberg: {
            detuning: {
                Uniform: Linear(start=1.0, stop="x", duration=3.0),
                ScaledLocations({1: 1.0, 2: 2.0}): Linear(
                    start=1.0, stop="x", duration=3.0
                ),
            },
        }
    }
)

print(seq)
print(seq.name("test"))
print(seq.append(seq))
print(seq[:0.5])
