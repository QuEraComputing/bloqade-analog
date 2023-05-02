from pydantic.dataclasses import dataclass
from bloqade.ir.pulse import (
    FieldName,
    RabiFrequencyAmplitude,
    RabiFrequencyPhase,
    Detuning,
)
from bloqade.ir.waveform import Waveform, Append, Linear, Constant, Slice
from bloqade.codegen.hardware.base import BaseCodeGen
from typing import List, Optional, Tuple
from bisect import bisect_left


@dataclass
class WaveformCodeGen(BaseCodeGen):
    field_name: Optional[FieldName] = None
    times: Optional[List[float]] = None
    values: Optional[List[float]] = None

    def scan_piecewise_linear(self, ast: Waveform):
        match ast:
            case Linear(duration=duration_expr, start=start_expr, stop=stop_expr):
                start = start_expr(**self.variable_reference)
                stop = stop_expr(**self.variable_reference)
                duration = duration_expr(**self.variable_reference)

                if not self.times:
                    self.times = [0, duration]
                    self.values = [start, stop]
                    return

                if self.values[-1] != start:
                    raise ValueError

                self.times.append(self.times[-1] + duration)
                self.values.append(stop)

            case Constant(duration=duration_expr, value=value_expr):
                start = stop = value_expr(**self.variable_reference)
                duration = duration_expr(**self.variable_reference)

                if not self.times:
                    self.times = [0, duration]
                    self.values = [start, stop]
                    return

                if self.values[-1] != start:
                    raise ValueError

                self.times.append(self.times[-1] + duration)
                self.values.append(stop)

            case Slice(waveform, interval):
                self.scan(waveform)
                start_time = interval.start(**self.variable_reference)
                stop_time = interval.stop(**self.variable_reference)
                start_value = waveform(start_time, **self.variable_reference)
                stop_value = waveform(stop_time, **self.variable_reference)

                start_index = bisect_left(self.times, start_time)
                stop_index = bisect_left(self.times, stop_time)

                absolute_times = (
                    [start_time] + self.times[start_index:stop_index] + [stop_time]
                )
                self.times = [time - start_time for time in absolute_times]
                self.values = (
                    [start_value] + self.values[start_index:stop_index] + [stop_value]
                )

            case Append(waveforms):
                for waveform in waveforms:
                    self.scan_piecewise_linear(waveform)

            case _:  # TODO: improve error message here
                raise NotImplementedError

    def scan_piecewise_constant(self, ast: Waveform):
        match ast:
            case Linear(
                duration=duration_expr, start=start_expr, stop=stop_expr
            ) if start_expr == stop_expr:
                value = start_expr(**self.variable_reference)
                duration = duration_expr(**self.variable_reference)

                if not self.times:
                    self.times = [0, duration]
                    self.values = [value, value]
                    return

                self.times.append(self.times[-1] + duration)
                self.values[-1] = value
                self.values.append(value)

            case Constant(duration=duration_expr, value=value_expr):
                value = value_expr(**self.variable_reference)
                duration = duration_expr(**self.variable_reference)

                if not self.times:
                    self.times = [0, duration]
                    self.values = [value, value]
                    return

                self.times.append(self.times[-1] + duration)
                self.values[-1] = value
                self.values.append(value)

            case Append(waveforms):
                for waveform in waveforms:
                    self.scan_piecewise_constant(waveform)

            case Slice(waveform, interval):
                self.scan(waveform)
                start_time = interval.start(**self.variable_reference)
                stop_time = interval.stop(**self.variable_reference)
                start_value = waveform(start_time, **self.variable_reference)
                stop_value = waveform(stop_time, **self.variable_reference)

                start_index = bisect_left(self.times, start_time)
                stop_index = bisect_left(self.times, stop_time)

                absolute_times = (
                    [start_time] + self.times[start_index:stop_index] + [stop_time]
                )

                self.times = [time - start_time for time in absolute_times]
                self.values = (
                    [start_value] + self.values[start_index:stop_index] + [stop_value]
                )

            case _:  # TODO: improve error message here
                raise NotImplementedError(
                    "Cannot interpret waveform as piecewise constant."
                )

    def scan(self, ast: Waveform):
        match self.field_name:
            case RabiFrequencyAmplitude():
                self.scan_piecewise_linear(ast)
            case RabiFrequencyPhase():
                self.scan_piecewise_constant(ast)
            case Detuning():
                self.scan_piecewise_linear(ast)

    def emit(self, ast: Waveform) -> Tuple[List[float], List[float]]:
        self.times = []
        self.values = []
        self.scan(ast)
        return self.times, self.values
