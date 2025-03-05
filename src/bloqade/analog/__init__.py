try:
    __import__("pkg_resources").declare_namespace(__name__)
except ImportError:
    __path__ = __import__("pkgutil").extend_path(__path__, __name__)

import importlib.metadata

import bloqade.analog.ir as _ir
from bloqade.analog.ir import (
    Literal,
    Variable,
    var,
    cast,
    start,
    to_waveform as waveform,
)
from bloqade.analog.factory import (
    linear,
    constant,
    rydberg_h,
    get_capabilities,
    piecewise_linear,
    piecewise_constant,
)
from bloqade.analog.constants import RB_C6
from bloqade.analog.serialize import load, save, dumps, loads

__version__ = importlib.metadata.version("bloqade-analog")


def tree_depth(depth: int = None):
    """Setting globally maximum depth for tree printing

    If `depth=None`, return current depth.
    If `depth` is provided, setting current depth to `depth`

    Args:
        depth (int, optional): the user specified depth. Defaults to None.

    Returns:
        int: current updated depth
    """
    if depth is not None:
        _ir.tree_print.MAX_TREE_DEPTH = depth
    return _ir.tree_print.MAX_TREE_DEPTH


__all__ = [
    "RB_C6",
    "start",
    "var",
    "cast",
    "Variable",
    "Literal",
    "piecewise_linear",
    "piecewise_constant",
    "linear",
    "constant",
    "tree_depth",
    "load",
    "save",
    "loads",
    "dumps",
    "rydberg_h",
    "waveform",
    "get_capabilities",
]
