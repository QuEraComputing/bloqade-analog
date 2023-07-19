from bloqade import start
from bloqade.ir.location import Square
from bloqade.ir import Constant, Linear
import json
import numpy as np
import pytest


def test_location_exceedloc():
    with pytest.raises(ValueError):
        seq = Linear(start=0.0, stop=1.0, duration=0.5).append(
            2 * Constant(0.5, duration=0.5)
        )
        start.rydberg.detuning.location(0).apply(seq).mock(10)


def test_hyperfine_schema():
    with pytest.raises(ValueError):
        seq = Linear(start=0.0, stop=1.0, duration=0.5).append(
            2 * Constant(0.5, duration=0.5)
        )
        Square(1).hyperfine.detuning.location(0).apply(seq).mock(10)


def test_local_no_global():
    seq = Linear(start=0.0, stop=1.0, duration=0.5).append(
        2 * Constant(0.5, duration=0.5)
    )
    job = Square(1).rydberg.detuning.location(0).scale(0.5).apply(seq).mock(10)

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(detune_ir["local"]["times"] == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(detune_ir["local"]["values"] == np.array([0, 1, 1]) * 1e6)
    assert detune_ir["local"]["lattice_site_coefficients"] == [0.5]

    # should have global even without assign:
    assert all(detune_ir["global"]["times"] == np.array([0, 1]) * 1e-6)
    assert all(detune_ir["global"]["values"] == np.array([0, 0]))


def test_local_global():
    seq = Linear(start=0.0, stop=1.0, duration=0.5).append(
        2 * Constant(0.5, duration=0.5)
    )
    seq_global = Constant(0.55, duration=1.0)

    job = (
        Square(1)
        .rydberg.detuning.uniform.apply(seq_global)
        .location(0)
        .scale(0.5)
        .apply(seq)
        .mock(10)
    )

    panel = json.loads(job.json())

    print(panel)

    ir = panel["tasks"]["0"]["task_ir"]

    assert ir["nshots"] == 10
    assert ir["lattice"]["sites"][0] == [0.0, 0.0]
    assert ir["lattice"]["filling"] == [1]

    detune_ir = ir["effective_hamiltonian"]["rydberg"]["detuning"]
    assert all(detune_ir["local"]["times"] == np.array([0, 0.5, 1.0]) * 1e-6)
    assert all(detune_ir["local"]["values"] == np.array([0, 1, 1]) * 1e6)
    assert detune_ir["local"]["lattice_site_coefficients"] == [0.5]

    # global :
    assert all(detune_ir["global"]["times"] == np.array([0, 1.0]) * 1e-6)
    assert all(detune_ir["global"]["values"] == np.array([0.55, 0.55]) * 1e6)
