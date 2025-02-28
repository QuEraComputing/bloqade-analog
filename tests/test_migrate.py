import io

import simplejson as json

from bloqade.analog.migrate import _migrate


def test_walk_dict():

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

    obj_str = json.dumps(obj)
    expected_str = json.dumps(expected)

    in_io = io.StringIO(obj_str)
    out_io = io.StringIO()

    _migrate(in_io, out_io)

    assert out_io.getvalue() == expected_str
