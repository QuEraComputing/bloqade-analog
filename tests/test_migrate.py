from bloqade.analog.migrate import JSONWalker


def test_walk_dict():
    walker = JSONWalker()
    obj = {
        "key1": "value1",
        "bloqade.key2": "value2",
        "bloqade.analog.key3": "value3",
        "nested": {"key4": "bloqade.value4", "bloqade.key5": "value5"},
        "list": [{"key6": "value6"}, {"bloqade.key7": "value7"}],
    }

    expected = {
        "key1": "value1",
        "bloqade.analog.key2": "value2",
        "bloqade.analog.key3": "value3",
        "nested": {"key4": "bloqade.value4", "bloqade.analog.key5": "value5"},
        "list": [{"key6": "value6"}, {"bloqade.analog.key7": "value7"}],
    }

    result = walker.walk_dict(obj)
    assert result == expected
