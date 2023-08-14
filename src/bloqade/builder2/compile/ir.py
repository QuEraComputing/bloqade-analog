from typing import Tuple, Union
from .stream import BuilderNode, BuilderStream
from ... import ir
from ..base import Builder

# from ..start import ProgramStart
from ..coupling import LevelCoupling, Rydberg, Hyperfine
from ..field import Field, Detuning, RabiAmplitude, RabiPhase
from ..spatial import SpatialModulation, Location, Uniform, Var, Scale
from ..waveform import (
    WaveformPrimitive,
    # Linear,
    # Constant,
    # Poly,
    # PiecewiseConstant,
    # PiecewiseLinear,
    # Fn,
    Slice,
    Record,
)
from ..parallelize import Parallelize, ParallelizeFlatten


class BuilderCompiler:
    def __init__(self, ast: Builder) -> None:
        self.stream = BuilderStream.create(ast)


class SequenceCompiler(BuilderCompiler):
    def read_address(self) -> Tuple[LevelCoupling, Field, BuilderNode]:
        spatial = self.stream.eat([Location, Uniform, Var], [Scale])
        curr = spatial

        if curr is None:
            return (None, None, None)

        while curr.next is not None:
            if not isinstance(curr.node, SpatialModulation):
                break
            curr = curr.next

        if type(spatial.node.__parent__) in [Detuning, RabiAmplitude, RabiPhase]:
            field = spatial.node.__parent__  # field is updated
            if type(field) in [RabiAmplitude, RabiPhase]:
                coupling = field.__parent__.__parent__  # skip Rabi
            else:
                coupling = field.__parent__

            # coupling not updated
            if type(coupling) not in [Rydberg, Hyperfine]:
                coupling = None
            return (coupling, field, spatial)
        else:  # only spatial is updated
            return (None, None, spatial)

    def _read_waveform(self, head: BuilderNode) -> Tuple[ir.Waveform, BuilderNode]:
        curr = head
        waveform: ir.Waveform = head.node.__bloqade_ir__()
        curr = curr.next
        while curr is not None:
            match curr.node:
                case WaveformPrimitive() as wf:
                    waveform = waveform.append(wf.__bloqade_ir__())
                case Slice(start, stop, _):
                    waveform = waveform[start:stop]
                case Record(name, _):
                    waveform = waveform.record(name)
                case _:
                    break
            curr = curr.next
        return waveform, curr

    def _read_spatial_modulation(
        self, head: BuilderNode
    ) -> Tuple[ir.SpatialModulation, BuilderNode]:
        curr = head
        spatial_modulation = None
        scaled_locations = ir.ScaledLocations({})

        while curr is not None:
            match curr.node:
                case Location(label, _):
                    scaled_locations[ir.Location(label)] = 1.0
                case Scale(value, Location(label, _)):
                    scaled_locations[ir.Location(label)] = ir.cast(value)
                case Uniform(_):
                    spatial_modulation = ir.Uniform
                case Var(name, _):
                    spatial_modulation = ir.RunTimeVector(name)
                case _:
                    break
            curr = curr.next

        if scaled_locations:
            return scaled_locations, curr
        else:
            return spatial_modulation, curr

    def _read_field(self, head) -> Tuple[ir.Field, BuilderNode]:
        sm, curr = self._read_spatial_modulation(head)
        wf, curr = self._read_waveform(curr)
        return ir.Field({sm: wf}), curr

    # def read_spatial_modulation(self) -> ir.SpatialModulation:
    #     head = self.stream.eat([Location, Uniform, Var], [Scale])
    #     sm, *_ = self._read_spatial_modulation(head)
    #     return sm

    # def read_waveform(self) -> ir.Waveform:
    #     wf_head = self.stream.eat(
    #         types=[Linear, Constant, Poly, PiecewiseConstant, PiecewiseLinear, Fn],
    #         skips=[Slice, Record],
    #     )
    #     wf, *_ = self._read_waveform(wf_head)
    #     return wf

    # def read_field(self) -> ir.Field:
    #     new_field = ir.Field({})
    #     while True:
    #         sm = self.read_spatial_modulation()
    #         wf = self.read_waveform()

    #         new_field = new_field.add(ir.Field({sm: wf}))

    #         match self.stream.curr:
    #             case BuilderNode(node=SpatialModulation()):
    #                 continue
    #             case _:
    #                 break

    #     return new_field

    # def compile(self) -> ir.Sequence:
    #     sequence = ir.Sequence()
    #     while True:
    #         node = self.stream.read_next(
    #             [Detuning, RabiAmplitude, RabiPhase, Hyperfine, Rydberg]
    #         )
    #         match node:
    #             case BuilderNode(node=Field() as field_node) as field_name:
    #                 field_name = field_node.__bloqade_ir__()
    #             case BuilderNode(
    #                 node=LevelCoupling() as coupling_node
    #             ) as coupling_name:
    #                 coupling_name = coupling_node.__bloqade_ir__()
    #                 continue
    #             case None:
    #                 break

    #         pulse = sequence.pulses.get(coupling_name, ir.Pulse({}))
    #         field = pulse.fields.get(field_name, ir.Field({}))

    #         field = field.add(self.read_field())

    #         pulse.fields[field_name] = field
    #         sequence.pulses[coupling_name] = pulse

    #     return sequence

    def compile(self) -> ir.Sequence:
        coupling_builder, field_builder, spatial_head = self.read_address()

        sequence = ir.Sequence({})
        coupling_name = coupling_builder.__bloqade_ir__()
        field_name = field_builder.__bloqade_ir__()

        pulse = sequence.pulses.get(coupling_name, ir.Pulse({}))
        field = pulse.fields.get(field_name, ir.Field({}))

        new_field, _ = self._read_field(spatial_head)
        field = field.add(new_field)

        while True:
            coupling_builder, field_builder, spatial_head = self.read_address()

            if coupling_builder is not None:
                # update old pulse
                sequence.pulses[coupling_name] = pulse
                # create/access new pulse
                coupling_name = coupling_builder.__bloqade_ir__()
                pulse = sequence.pulses.get(coupling_name, ir.Pulse({}))

            if field_builder is not None:
                # update old field
                pulse.fields[field_name] = field
                # create/access new field
                field_name = field_builder.__bloqade_ir__()
                field = pulse.fields.get(field_name, ir.Field({}))

            if spatial_head is None:
                break

            new_field, _ = self._read_field(spatial_head)
            field = field.add(new_field)


class RegisterCompiler(BuilderCompiler):
    def compile(self) -> Union[ir.AtomArrangement, ir.ParallelRegister]:
        # register is always head of the stream
        register_block = self.stream.read()

        register = register_block.node

        parallel_options = self.stream.eat([Parallelize, ParallelizeFlatten])

        if parallel_options is not None:
            parallel_options = parallel_options.node
            return ir.ParallelRegister(register, parallel_options._cluster_spacing)

        return register
