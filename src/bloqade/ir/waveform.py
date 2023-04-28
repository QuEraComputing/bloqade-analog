from pydantic.dataclasses import dataclass
from typing import Any, Union, List
from enum import Enum
from bloqade.ir.scalar import Scalar, Interval, cast


class AlignedValue(str, Enum):
    Left = "left_value"
    Right = "right_value"


class Alignment(str, Enum):
    Left = "left_aligned"
    Right = "right_aligned"


@dataclass(frozen=True)
class Waveform:
    """
    <waveform> ::= <instruction>
        | <smooth>
        | <slice>
        | <append>
        | <negative>
        | <scale>
        | <add>
    """

    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError

    def add(self, other: "Waveform") -> "Waveform":
        return self.canonicalize(Add(self, other))

    def align(
        self, alignment: Alignment, value: Union[None, AlignedValue, Scalar] = None
    ) -> "Waveform":
        if value is None:
            if alignment == Alignment.Left:
                value = AlignedValue.Left
            elif alignment == Alignment.Right:
                value = AlignedValue.Right
            else:
                raise ValueError(f"Invalid alignment: {alignment}")
        return self.canonicalize(AlignedWaveform(self, alignment, value))

    def smooth(self, kernel: str = "gaussian") -> "Waveform":
        return self.canonicalize(Smooth(kernel, self))

    def scale(self, value: Scalar) -> "Waveform":
        return self.canonicalize(Scale(value, self))
    
    def __neg__(self) -> "Waveform":
        return self.canonicalize(Negative(self))

    def __getitem__(self, s: slice) -> "Waveform":
        match s:
            case slice(start=None, stop=None, step=None):
                raise ValueError("Slice must have at least one argument")
            case slice(start=None, stop=None, step=_):
                raise ValueError("Slice step must be None")
            case slice(start=None, stop=stop, step=None):
                expr = Slice(self, Interval(None, cast(stop)))
            case slice(start=None, stop=stop, step=_):
                raise ValueError("Slice step must be None")
            case slice(start=start, stop=None, step=None):
                expr = Slice(self, Interval(cast(start), None))
            case slice(start=start, stop=None, step=_):
                raise ValueError("Slice step must be None")
            case slice(start=start, stop=stop, step=None):
                expr = Slice(self, Interval(cast(start), cast(stop)))
            case slice(start=start, stop=stop, step=_):
                raise ValueError("Slice step must be None")
        return self.canonicalize(expr)

    def duration(self) -> Scalar:
        match self:
            case Instruction(duration=duration):
                return duration
            case AlignedWaveform(waveform=waveform, alignment=_, value=_):
                return waveform.duration()
            case Slice(waveform=waveform, interval=interval):
                return interval.end - interval.start
            case _:
                raise ValueError(f"Cannot compute duration of {self}")

    @staticmethod
    def canonicalize(expr: "Waveform") -> "Waveform":
        return expr


@dataclass(frozen=True)
class AlignedWaveform(Waveform):
    """
    <padded waveform> ::= <waveform> | <waveform> <alignment> <value>

    <alignment> ::= 'left aligned' | 'right aligned'
    <value> ::= 'left value' | 'right value' | <scalar expr>
    """

    waveform: Waveform
    alignment: Alignment
    value: Union[Scalar, AlignedValue]


@dataclass(frozen=True)
class Instruction(Waveform):
    duration: Scalar


@dataclass(frozen=True)
class Linear(Instruction):
    """
    <linear> ::= 'linear' <scalar expr> <scalar expr>
    """

    start: Scalar
    stop: Scalar

    def __call__(self, clock_s: float, **kwargs) -> Any:
        start_value = self.start(**kwargs)
        stop_value = self.stop(**kwargs)

        if clock_s > self.duration(**kwargs):
            return 0.0
        else:
            return ((stop_value - start_value)/self.duration(**kwargs)) * clock_s
    
    def __repr__(self) -> str:
        return f"linear {self.start} {self.stop}"


@dataclass(frozen=True)
class Constant(Instruction):
    """
    <constant> ::= 'constant' <scalar expr>
    """

    value: Scalar

    def __call__(self, clock_s: float, **kwargs) -> Any:
        constant_value = self.value(**kwargs)
        if clock_s > self.duration(**kwargs):
            return 0.0
        else:
            return constant_value
    
    def __repr__(self) -> str:
        return f"constant {self.value}"


@dataclass(frozen=True)
class Poly(Instruction):
    """
    <poly> ::= <scalar>+
    """

    checkpoints: List[Scalar]

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        # b + x + x^2 + ... + x^n-1 + x^n
        if clock_s > self.duration(**kwargs):
            return 0.0
        else:
            # call clock_s on each element of the scalars,
            # then apply the proper powers
            for exponent, scalar_expr in enumerate(self.checkpoints):
                value += scalar_expr(**kwargs) * clock_s**exponent

            return value
    
    def __repr__(self) -> str:
        return f"{', '.join(map(str, self.checkpoints))}"


@dataclass(frozen=True)
class Smooth(Waveform):
    """
    <smooth> ::= 'smooth' <kernel> <waveform>
    """

    kernel: str
    waveform: Waveform

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class Slice(Waveform):
    """
    <slice> ::= <waveform> <scalar.interval>
    """

    waveform: Waveform
    interval: Interval

    def __repr__(self) -> str:
        return f"{self.waveform}[{self.interval}]"

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class Append(Waveform):
    """
    <append> ::= <waveform> | <append> <waveform>
    """

    waveforms: List[Waveform]

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        raise NotImplementedError


@dataclass(frozen=True)
class Negative(Waveform):
    """
    <negative> ::= '-' <waveform>
    """

    waveform: Waveform

    # TODO: implement
    def __call__(self, clock_s: float, **kwargs) -> Any:
        return -self.waveform(clock_s, **kwargs)


@dataclass(frozen=True)
class Scale(Waveform):
    """
    <scale> ::= <scalar expr> '*' <waveform>
    """

    scalar: Scalar
    waveform: Waveform

    def __call__(self, clock_s: float, **kwargs) -> Any:
        return self.scalar(**kwargs) * self.waveform(clock_s, **kwargs)


@dataclass(frozen=True)
class Add(Waveform):
    """
    <add> ::= <waveform> '+' <waveform>
    """

    left: Waveform
    right: Waveform

    def __call__(self, clock_s: float, **kwargs) -> Any:
        return self.left(clock_s, **kwargs) + self.right(clock_s, **kwargs)
