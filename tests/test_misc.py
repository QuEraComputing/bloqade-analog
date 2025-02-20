import bloqade.analog


def test_global_treedepth():
    bloqade.analog.tree_depth(4)
    assert bloqade.analog.tree_depth() == 4
    bloqade.analog.tree_depth(10)
    assert bloqade.analog.tree_depth() == 10
