import bloqade_analog


def test_global_treedepth():
    bloqade_analog.tree_depth(4)
    assert bloqade_analog.tree_depth() == 4
    bloqade_analog.tree_depth(10)
    assert bloqade_analog.tree_depth() == 10
