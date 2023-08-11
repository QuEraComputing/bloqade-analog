from bloqade.codegen.common.json import BloqadeIREncoder
from ..base import Builder
from ..spatial import Location, Scale, Var
from ..waveform import (
    Linear,
    Constant,
    Poly,
    Fn,
    Apply,
    Slice,
    Record,
    Sample,
    PiecewiseLinear,
    PiecewiseConstant,
)


class BuilderEncoder(BloqadeIREncoder):
    def default(self, obj):
        match obj:
            case Constant(value, duration, parent):
                return {
                    "Constant": {
                        "value": self.default(value),
                        "duration": self.default(duration),
                        "parent": self.default(parent),
                    }
                }
            case Linear(start, stop, duration, parent):
                return {
                    "Linear": {
                        "start": self.default(start),
                        "stop": self.default(stop),
                        "duration": self.default(duration),
                        "parent": self.default(parent),
                    }
                }
            case Poly(coeffs, duration, parent):
                return {
                    "Poly": {
                        "coeffs": self.default(coeffs),
                        "duration": self.default(duration),
                        "parent": self.default(parent),
                    }
                }
            case Fn():
                raise ValueError(
                    "Bloqade does not support serialization of Python code."
                )
            case Apply(wf, parent):
                return {
                    "Apply": {"wf": self.default(wf), "parent": self.default(parent)}
                }
            case Slice(None, stop, parent):
                return {
                    "Slice": {
                        "stop": self.default(stop),
                        "parent": self.default(parent),
                    }
                }
            case Slice(start, None, parent):
                return {
                    "Slice": {
                        "start": self.default(start),
                        "parent": self.default(parent),
                    }
                }
            case Slice(start, stop, parent):
                return {
                    "Slice": {
                        "start": self.default(start),
                        "stop": self.default(stop),
                        "parent": self.default(parent),
                    }
                }
            case Record(name, parent):
                return {
                    "Record": {
                        "name": self.default(name),
                        "parent": self.default(parent),
                    }
                }
            case Sample(dt, interpolation, parent):
                return {
                    "Sample": {
                        "dt": self.default(dt),
                        "interpolation": self.default(interpolation),
                        "parent": self.default(parent),
                    }
                }
            case PiecewiseLinear(durations, values, parent):
                return {
                    "PiecewiseLinear": {
                        "durations": self.default(durations),
                        "values": self.default(values),
                        "parent": self.default(parent),
                    }
                }
            case PiecewiseConstant(durations, values, parent):
                return {
                    "PiecewiseConstant": {
                        "durations": self.default(durations),
                        "values": self.default(values),
                        "parent": self.default(parent),
                    }
                }
            case Location(label, parent):
                return {
                    "Location": {
                        "label": self.default(label),
                        "parent": self.default(parent),
                    }
                }
            case Scale(value, parent):
                return {
                    "Scale": {
                        "value": self.default(value),
                        "parent": self.default(parent),
                    }
                }
            case Var(name, parent):
                return {
                    "Var": {"name": self.default(name), "parent": self.default(parent)}
                }
            case Builder(parent):  # default serialization implementation
                return {"Builder": {"parent": self.default(parent)}}
            case _:
                return super().default(obj)
