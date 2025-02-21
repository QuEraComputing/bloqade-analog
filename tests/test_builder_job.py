import pytest

from bloqade.analog.ir.location import Square


def test_braket_unsupport_parallel():
    prog = Square(3)

    prog = prog.rydberg.detuning.uniform.piecewise_constant([0.1], [32])
    prog = prog.parallelize(4)

    with pytest.raises(TypeError):
        prog.braket.local_emulator().run(shots=10)
