from bloqade.emulate.ir.space import ThreeLevelAtom, TwoLevelAtom, Space
from bloqade.emulate.ir.emulator import Register
import numpy as np


def test_two_level_space():
    positions = [(0, 0), (0, 1)]
    register = Register(TwoLevelAtom, positions, 0)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 2
    assert space.size == 4
    assert np.all(space.configurations == np.array([0, 1, 2, 3]))


def test_two_level_subspace():
    positions = [(0, 0), (0, 1)]
    register = Register(TwoLevelAtom, positions, 1.1)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 2
    assert space.size == 3
    assert np.all(space.configurations == np.array([0, 1, 2]))


def test_two_level_subspace_2():
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    register = Register(TwoLevelAtom, positions, np.sqrt(2) + 0.1)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 4
    assert space.size == 5
    assert np.all(space.configurations == np.array([0, 1, 2, 4, 8]))


def test_three_level_space():
    positions = [(0, 0), (0, 1)]
    register = Register(ThreeLevelAtom, positions, 0)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 2
    assert space.size == 9
    assert np.all(space.configurations == np.array([0, 1, 2, 3, 4, 5, 6, 7, 8]))


def test_three_level_subspace():
    positions = [(0, 0), (0, 1)]
    register = Register(ThreeLevelAtom, positions, 1.1)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 2
    assert space.size == 8
    assert np.all(space.configurations == np.array([0, 1, 2, 3, 4, 5, 6, 7]))


def test_three_level_subspace_2():
    positions = [(0, 0), (0.5, np.sqrt(3) / 2), (0, 1)]
    register = Register(ThreeLevelAtom, positions, 1.1)
    space = Space.create(register)
    print(space)
    assert space.n_atoms == 3
    assert space.size == 20
    assert np.all(
        space.configurations
        == np.array(
            [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 21, 22]
        )
    )


def test_two_level_integer_to_string():
    assert TwoLevelAtom.integer_to_string(0, 2) == "|gg>"
    assert TwoLevelAtom.integer_to_string(1, 2) == "|rg>"
    assert TwoLevelAtom.integer_to_string(2, 2) == "|gr>"
    assert TwoLevelAtom.integer_to_string(3, 2) == "|rr>"


def test_two_level_string_to_integer():
    assert TwoLevelAtom.string_to_integer("|gg>") == 0
    assert TwoLevelAtom.string_to_integer("|rg>") == 1
    assert TwoLevelAtom.string_to_integer("|gr>") == 2
    assert TwoLevelAtom.string_to_integer("|rr>") == 3


def test_three_level_integer_to_string():
    assert ThreeLevelAtom.integer_to_string(0, 2) == "|gg>"
    assert ThreeLevelAtom.integer_to_string(1, 2) == "|hg>"
    assert ThreeLevelAtom.integer_to_string(2, 2) == "|rg>"
    assert ThreeLevelAtom.integer_to_string(3, 2) == "|gh>"
    assert ThreeLevelAtom.integer_to_string(4, 2) == "|hh>"
    assert ThreeLevelAtom.integer_to_string(5, 2) == "|rh>"
    assert ThreeLevelAtom.integer_to_string(6, 2) == "|gr>"
    assert ThreeLevelAtom.integer_to_string(7, 2) == "|hr>"
    assert ThreeLevelAtom.integer_to_string(8, 2) == "|rr>"


def test_three_level_string_to_integer():
    assert ThreeLevelAtom.string_to_integer("|gg>") == 0
    assert ThreeLevelAtom.string_to_integer("|hg>") == 1
    assert ThreeLevelAtom.string_to_integer("|rg>") == 2
    assert ThreeLevelAtom.string_to_integer("|gh>") == 3
    assert ThreeLevelAtom.string_to_integer("|hh>") == 4
    assert ThreeLevelAtom.string_to_integer("|rh>") == 5
    assert ThreeLevelAtom.string_to_integer("|gr>") == 6
    assert ThreeLevelAtom.string_to_integer("|hr>") == 7
    assert ThreeLevelAtom.string_to_integer("|rr>") == 8
