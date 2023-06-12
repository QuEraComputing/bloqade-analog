from bloqade.ir.scalar import Literal
import bloqade.ir.waveform as waveform
from bloqade.ir.field import (
    Field,
    Location,
    SpatialModulation,
    ScaledLocations,
    RunTimeVector,
    Uniform,
)
from bloqade.ir.pulse import (
    PulseExpr,
    Pulse,
    NamedPulse,
    RabiFrequencyAmplitude,
    RabiFrequencyPhase,
    Detuning,
)
from bloqade.ir.sequence import (
    SequenceExpr,
    Sequence,
    NamedSequence,
    RydbergLevelCoupling,
    HyperfineLevelCoupling,
)
from bloqade.ir.location.base import AtomArrangement, ParallelRegister
from bloqade.ir import Program

from bloqade.codegen.program_visitor import ProgramVisitor
from bloqade.codegen.waveform_visitor import WaveformVisitor
from bloqade.codegen.assignment_scan import AssignmentScan
from bloqade.submission.ir.parallel import ParallelDecoder, ClusterLocationInfo

import bloqade.submission.ir.task_specification as task_spec
from bloqade.submission.ir.capabilities import QuEraCapabilities
from typing import Any, Dict, Tuple, List, Union, Optional
from bisect import bisect_left
from numbers import Number
from decimal import Decimal
import numpy as np


class PiecewiseLinearCodeGen(WaveformVisitor):
    def __init__(self, assignments: Dict[str, Union[Number, List[Number]]]):
        self.assignments = assignments

    def visit_negative(
        self, ast: waveform.Negative
    ) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveform)
        return times, [-value for value in values]

    def visit_scale(self, ast: waveform.Scale) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveform)
        scaler = ast.scalar(**self.assignments)
        return times, [scaler * value for value in values]

    def visit_linear(self, ast: waveform.Linear) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        start = ast.start(**self.assignments)
        stop = ast.stop(**self.assignments)

        return [Decimal(0), duration], [start, stop]

    def visit_constant(
        self, ast: waveform.Constant
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        value = ast.value(**self.assignments)

        return [Decimal(0), duration], [value, value]

    def visit_poly(self, ast: waveform.Poly) -> Tuple[List[Decimal], List[Decimal]]:
        match ast:
            case waveform.Poly(
                checkpoints=checkpoint_exprs, duration=duration_expr
            ) if len(checkpoint_exprs) == 1:
                duration = duration_expr(**self.assignments)
                (value,) = [
                    checkpoint_expr(**self.assignments)
                    for checkpoint_expr in checkpoint_exprs
                ]
                return [Decimal(0), duration], [value, value]

            case waveform.Poly(
                checkpoints=checkpoint_exprs, duration=duration_expr
            ) if len(checkpoint_exprs) == 2:
                duration = duration_expr(**self.assignments)
                values = [
                    checkpoint_expr(**self.assignments)
                    for checkpoint_expr in checkpoint_exprs
                ]

                start = values[0]
                stop = values[0] + values[1] * duration

                return [Decimal(0), duration], [start, stop]

            case waveform.Poly(checkpoints=checkpoints):
                order = len(checkpoints) - 1
                raise ValueError(
                    "Failed to compile Waveform to piecewise linear,"
                    f"found Polynomial of order {order}."
                )

    def visit_slice(self, ast: waveform.Slice) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.waveform.duration(**self.assignments)

        start_time = ast.iterval.start(**self.assignments)
        stop_time = ast.interval.stop(**self.assignments)

        if start_time < 0:
            raise ValueError((f"start time for slice {start_time} is smaller than 0."))

        if stop_time > duration:
            raise ValueError(
                (f"end time for slice {stop_time} is larger than duration {duration}.")
            )

        if stop_time < start_time:
            raise ValueError(
                (
                    f"end time for slice {stop_time} is smaller than "
                    f"starting value for slice {start_time}."
                )
            )

        times, values = self.visit(ast.waveform)

        start_index = bisect_left(times, start_time)
        stop_index = bisect_left(times, stop_time)

        # evaluate start value using linear interpolation
        start_slope = (values[start_index + 1] - values[start_index]) / (
            times[start_index + 1] - times[start_index]
        )
        start_value = (
            start_slope * (start_time - times[start_index]) + values[start_index]
        )

        # evaluate stop value using linear interpolation
        stop_slope = (values[stop_index + 1] - values[stop_index]) / (
            times[stop_index + 1] - times[stop_index]
        )
        stop_value = stop_slope * (stop_time - times[stop_index]) + values[stop_index]

        absolute_times = [start_time] + times[start_index:stop_index] + [stop_time]

        times = [time - start_time for time in absolute_times]
        values = [start_value] + values[start_index:stop_index] + [stop_value]

        return times, values

    def visit_append(self, ast: waveform.Append) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveforms[0])

        for sub_expr in ast.waveforms[1:]:
            new_times, new_values = self.visit(sub_expr)

            # skip instructions with duration=0
            if new_times[-1] == Decimal(0):
                continue

            if values[-1] != new_values[0]:
                diff = abs(new_values[0] - values[-1])
                raise ValueError(
                    f"discontinuity with a jump of {diff} found when compiling to "
                    "piecewise linear."
                )

            shifted_times = [time + times[-1] for time in new_times[1:]]
            times.extend(shifted_times)
            values.extend(new_values[1:])

        return times, values

    def visit_sample(self, ast: waveform.Sample) -> Tuple[List[Decimal], List[Decimal]]:
        return ast.samples(**self.assignments)


class PiecewiseConstantCodeGen(WaveformVisitor):
    def __init__(self, assignments: Dict[str, Union[Number, List[Number]]]):
        self.assignments = assignments

    def visit_negative(
        self, ast: waveform.Negative
    ) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = ast.waveform
        return times, [-value for value in values]

    def visit_scale(self, ast: waveform.Scale) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveform)
        scaler = ast.scalar(**self.assignments)
        return times, [scaler * value for value in values]

    def visit_linear(self, ast: waveform.Linear) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        start = ast.start(**self.assignments)
        stop = ast.stop(**self.assignments)

        if start != stop:
            raise ValueError(
                "Failed to compile Waveform to piecewise constant, "
                "found non-constant Linear piecce."
            )

        return [0, duration], [start, stop]

    def visit_constant(
        self, ast: waveform.Constant
    ) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.duration(**self.assignments)
        value = ast.value(**self.assignments)

        return [Decimal(0), duration], [value, value]

    def visit_poly(self, ast: waveform.Poly) -> Tuple[List[Decimal], List[Decimal]]:
        match ast:
            case waveform.Poly(
                checkpoints=checkpoint_exprs, duration=duration_expr
            ) if len(checkpoint_exprs) == 1:
                duration = duration_expr(**self.assignments)
                (value,) = [
                    checkpoint_expr(**self.assignments)
                    for checkpoint_expr in checkpoint_exprs
                ]
                return [Decimal(0), duration], [value, value]

            case waveform.Poly(checkpoints=checkpoints):
                order = len(checkpoints) - 1
                raise ValueError(
                    "Failed to compile Waveform to piecewise constant, "
                    f"found Polynomial of order {order}."
                )

    def visit_slice(self, ast: waveform.Slice) -> Tuple[List[Decimal], List[Decimal]]:
        duration = ast.waveform.duration(**self.assignments)

        start_time = ast.iterval.start(**self.assignments)
        stop_time = ast.interval.stop(**self.assignments)

        if start_time < 0:
            raise ValueError((f"start time for slice {start_time} is smaller than 0."))

        if stop_time > duration:
            raise ValueError(
                (f"end time for slice {stop_time} is larger than duration {duration}.")
            )

        if stop_time < start_time:
            raise ValueError(
                (
                    f"end time for slice {stop_time} is smaller than "
                    f"starting value for slice {start_time}."
                )
            )

        times, values = self.visit(ast.waveform)

        start_index = bisect_left(times, start_time)
        stop_index = bisect_left(times, stop_time)

        # evaluate start value using constant interpolation
        start_value = values[start_index]
        # evaluate stop value using constant interpolation
        stop_value = values[stop_index]

        absolute_times = [start_time] + times[start_index:stop_index] + [stop_time]

        times = [time - start_time for time in absolute_times]
        values = [start_value] + values[start_index:stop_index] + [stop_value]

        return times, values

    def visit_append(self, ast: waveform.Append) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = self.visit(ast.waveforms[0])

        for sub_expr in ast.waveforms[1:]:
            new_times, new_values = self.visit(sub_expr)

            # skip instructions with duration=0
            if new_times[-1] == Decimal(0):
                continue

            shifted_times = [time + times[-1] for time in new_times[1:]]
            times.extend(shifted_times)
            values[-1] = new_values[0]
            values.extend(new_values[1:])

        return times, values

    def visit_sample(self, ast: waveform.Sample) -> Tuple[List[Decimal], List[Decimal]]:
        times, values = ast.samples(**self.assignments)

        values[-1] = values[-2]
        return times, values


class SchemaCodeGen(ProgramVisitor):
    def __init__(
        self,
        assignments: Dict[str, Union[Number, List[Number]]],
        capabilities: Optional[QuEraCapabilities] = None,
    ):
        self.capabilities = capabilities
        self.assignments = assignments
        self.parallel_decoder = None
        self.lattice = None
        self.effective_hamiltonian = None
        self.rydberg = None
        self.field_name = None
        self.rabi_frequency_amplitude = None
        self.rabi_frequency_phase = None
        self.detuning = None
        self.lattice_site_coefficients = None

    @staticmethod
    def convert_time_to_SI_units(times: List[Decimal]):
        return [time * Decimal("1e-6") for time in times]

    @staticmethod
    def convert_energy_to_SI_units(values: List[Decimal]):
        return [value * Decimal("1e6") for value in values]

    @staticmethod
    def convert_position_to_SI_units(position: Tuple[Decimal]):
        return tuple(coordinate * Decimal("1e-6") for coordinate in position)

    def visit_spatial_modulation(self, ast: SpatialModulation):
        lattice_site_coefficients = []

        match ast:
            case ScaledLocations(locations):
                for location in locations.keys():
                    if (
                        location.value >= self.n_atoms
                    ):  # n_atoms is now the number of atoms in the parallelized
                        # lattice, but needs to be num. atoms in the original
                        raise ValueError(
                            f"Location({location.value}) is larger than the register."
                        )

                for atom_index in range(self.n_atoms):
                    scale = locations.get(Location(atom_index), Literal(0.0))
                    lattice_site_coefficients.append(
                        scale(**self.assignments)
                    )  # append scalars to lattice_site_coefficients

            case RunTimeVector(name):
                if len(self.assignments[name]) != self.n_atoms:
                    raise ValueError(
                        f"Coefficient list {name} doesn't match the size of register "
                        f"{self.n_atoms}."
                    )
                lattice_site_coefficients = list(self.assignments[name])

        self.lattice_site_coefficients = []
        if self.parallel_decoder:
            for cluster_site_info in self.parallel_decoder.mapping:
                self.lattice_site_coefficients.append(
                    lattice_site_coefficients[cluster_site_info.cluster_location_index]
                )
        else:
            self.lattice_site_coefficients = lattice_site_coefficients

    def visit_field(self, ast: Field):
        match (self.field_name, ast):  # Pulse: Dict of FieldName/Field
            # Can only have a global RabiFrequencyAmplitude
            case (RabiFrequencyAmplitude(), Field(terms)) if len(
                terms
            ) == 1 and Uniform in terms:
                times, values = PiecewiseLinearCodeGen(self.assignments).visit(
                    terms[Uniform]
                )

                times = SchemaCodeGen.convert_time_to_SI_units(times)
                values = SchemaCodeGen.convert_energy_to_SI_units(values)

                self.rabi_frequency_amplitude = task_spec.RabiFrequencyAmplitude(
                    global_=task_spec.GlobalField(times=times, values=values)
                )
            # Can only have global RabiFrequencyPhase
            case (RabiFrequencyPhase(), Field(terms)) if len(
                terms
            ) == 1 and Uniform in terms:  # has to be global
                times, values = PiecewiseConstantCodeGen(self.assignments).visit(
                    terms[Uniform]
                )

                times = SchemaCodeGen.convert_time_to_SI_units(times)

                self.rabi_frequency_phase = task_spec.RabiFrequencyAmplitude(
                    global_=task_spec.GlobalField(times=times, values=values)
                )

            # 3 possible detuning cases:
            # (global, no local),
            # (local, no global),
            # (local, global)

            ## global detuning, no local
            case (Detuning(), Field(terms)) if len(terms) == 1 and Uniform in terms:
                times, values = PiecewiseLinearCodeGen(self.assignments).visit(
                    terms[Uniform]
                )

                times = SchemaCodeGen.convert_time_to_SI_units(times)
                values = SchemaCodeGen.convert_energy_to_SI_units(values)

                self.detuning = task_spec.Detuning(
                    global_=task_spec.GlobalField(times=times, values=values)
                )

            ## local detuning, no global
            case (Detuning(), Field(terms)) if len(terms) == 1:
                ((spatial_modulation, waveform),) = terms.items()

                times, values = PiecewiseLinearCodeGen(self.assignments).visit(waveform)

                times = SchemaCodeGen.convert_time_to_SI_units(times)
                values = SchemaCodeGen.convert_energy_to_SI_units(values)

                self.visit(spatial_modulation)
                self.detuning = task_spec.Detuning(
                    global_=task_spec.GlobalField(
                        times=[0, times[-1]], values=[0.0, 0.0]
                    ),
                    local=task_spec.LocalField(
                        times=times,
                        values=values,
                        lattice_site_coefficients=self.lattice_site_coefficients,
                    ),
                )

            # local AND global detuning
            case (Detuning(), Field(terms)) if len(terms) == 2 and Uniform in terms:
                # will only be two keys
                for k in terms.keys():
                    if k == Uniform:
                        global_times, global_values = PiecewiseLinearCodeGen(
                            self.assignments
                        ).visit(terms[Uniform])
                    else:  # can be RunTimeVector or ScaledLocations
                        spatial_modulation = k
                        local_times, local_values = PiecewiseLinearCodeGen(
                            self.assignments
                        ).visit(terms[k])

                self.visit(spatial_modulation)  # just visit the non-uniform locations

                global_times = SchemaCodeGen.convert_time_to_SI_units(global_times)
                local_times = SchemaCodeGen.convert_time_to_SI_units(local_times)

                global_values = SchemaCodeGen.convert_energy_to_SI_units(global_values)
                local_values = SchemaCodeGen.convert_energy_to_SI_units(local_values)

                self.detuning = task_spec.Detuning(
                    local=task_spec.LocalField(
                        times=local_times,
                        values=local_values,
                        lattice_site_coefficients=self.lattice_site_coefficients,
                    ),
                    global_=task_spec.GlobalField(
                        times=global_times, values=global_values
                    ),
                )

            case _:
                raise NotImplementedError()

    def visit_pulse(self, ast: PulseExpr):
        match ast:
            case Pulse(fields):
                if RabiFrequencyAmplitude() in fields:
                    self.field_name = RabiFrequencyAmplitude()
                    self.visit(fields[self.field_name])

                if RabiFrequencyPhase() in fields:
                    self.field_name = RabiFrequencyPhase()
                    self.visit(fields[self.field_name])

                if Detuning() in fields:
                    self.field_name = Detuning()
                    self.visit(fields[self.field_name])

            case NamedPulse(pulse, _):
                self.visit(pulse)

            case _:
                raise ValueError(
                    "Failed to compile pulse expression to QuEra task, "
                    f"found: {repr(ast)}"
                )

        # fix-up any missing fields
        duration = 0.0

        if self.rabi_frequency_amplitude is not None:
            duration = max(duration, self.rabi_frequency_amplitude.global_.times[-1])

        if self.rabi_frequency_phase is not None:
            duration = max(duration, self.rabi_frequency_phase.global_.times[-1])

        if self.detuning is not None:
            duration = max(duration, self.detuning.global_.times[-1])

        if duration == 0.0:
            raise ValueError("No Fields found in pulse.")

        if self.rabi_frequency_amplitude is None:
            self.rabi_frequency_amplitude = task_spec.RabiFrequencyAmplitude(
                global_=task_spec.GlobalField(times=[0, duration], values=[0.0, 0.0])
            )

        if self.rabi_frequency_phase is None:
            self.rabi_frequency_phase = task_spec.RabiFrequencyPhase(
                global_=task_spec.GlobalField(times=[0, duration], values=[0.0, 0.0])
            )

        if self.detuning is None:
            self.detuning = task_spec.Detuning(
                global_=task_spec.GlobalField(times=[0, duration], values=[0.0, 0.0])
            )

        self.rydberg = task_spec.RydbergHamiltonian(
            rabi_frequency_amplitude=self.rabi_frequency_amplitude,
            rabi_frequency_phase=self.rabi_frequency_phase,
            detuning=self.detuning,
        )

    def visit_sequence(self, ast: SequenceExpr):
        match ast:
            case Sequence(pulses):
                if HyperfineLevelCoupling() in pulses:
                    raise ValueError("QuEra tasks does not support Hyperfine coupling.")

                self.visit(pulses[RydbergLevelCoupling()])

            case NamedSequence(sequence, _):
                self.visit(sequence)

            case _:
                raise ValueError(
                    "Failed to compile sequence expression to QuEra task, "
                    f"found: {repr(ast)}"
                )

        self.effective_hamiltonian = task_spec.EffectiveHamiltonian(
            rydberg=self.rydberg
        )

    def visit_register(self, ast: AtomArrangement):
        sites = []
        filling = []

        for locaiton_info in ast.enumerate():
            site = tuple(ele(**self.assignments) for ele in locaiton_info.position)
            sites.append(SchemaCodeGen.convert_position_to_SI_units(site))
            filling.append(locaiton_info.filling.value)

        self.n_atoms = len(sites)

        self.lattice = task_spec.Lattice(sites=sites, filling=filling)

    def visit_parallel_register(self, ast: ParallelRegister) -> Any:
        if self.capabilities is None:
            raise NotImplementedError(
                "Cannot parallelize register without device capabilities."
            )

        height_max = self.capabilities.capabilities.lattice.area.height / 1e-6
        width_max = self.capabilities.capabilities.lattice.area.width / 1e-6
        number_sites_max = (
            self.capabilities.capabilities.lattice.geometry.number_sites_max
        )

        register_filling = np.asarray(ast.register_filling)
        register_locations = np.asarray(ast.register_locations)
        shift_vectors = np.asarray(ast.shift_vectors)

        # build register by stack method because
        # shift_vectosr might not be rectangular
        c_stack = [(0, 0)]
        visited = set([(0, 0)])
        mapping = []
        global_site_index = 0
        sites = []
        filling = []
        while c_stack:
            if len(mapping) + len(ast.register_locations) > number_sites_max:
                break

            cluster_index = c_stack.pop()

            shift = (
                shift_vectors[0] * cluster_index[0]
                + shift_vectors[1] * cluster_index[1]
            )

            new_register_locations = np.asarray(
                [ele(**self.assignments) for ele in (register_locations + shift).flat]
            ).reshape(register_locations.shape)

            # skip clusters that fall out of bounds
            if (
                np.any(new_register_locations < 0)
                or np.any(new_register_locations[:, 0] > width_max)
                or np.any(new_register_locations[:, 1] > height_max)
            ):
                continue

            new_cluster_indices = [
                (cluster_index[0] + 1, cluster_index[1]),
                (cluster_index[0], cluster_index[1] + 1),
                (cluster_index[0] - 1, cluster_index[1]),
                (cluster_index[0], cluster_index[1] - 1),
            ]

            for new_cluster_index in new_cluster_indices:
                if new_cluster_index not in visited:
                    visited.add(new_cluster_index)
                    c_stack.append(new_cluster_index)

            for cluster_location_index, (location, filled) in enumerate(
                zip(new_register_locations[:], register_filling)
            ):
                site = SchemaCodeGen.convert_position_to_SI_units(tuple(location))
                sites.append(site)
                filling.append(filled)

                mapping.append(
                    ClusterLocationInfo(
                        cluster_index=cluster_index,
                        global_location_index=global_site_index,
                        cluster_location_index=cluster_location_index,
                    )
                )

                global_site_index += 1

        self.lattice = task_spec.Lattice(sites=sites, filling=filling)
        self.n_atoms = len(ast.register_locations)
        self.parallel_decoder = ParallelDecoder(mapping=mapping)

    def emit(self, nshots: int, program: "Program") -> task_spec.QuEraTaskSpecification:
        self.assignments = AssignmentScan(self.assignments).emit(program.sequence)
        self.visit(program.register)
        self.visit(program.sequence)

        return task_spec.QuEraTaskSpecification(
            nshots=nshots,
            lattice=self.lattice,
            effective_hamiltonian=self.effective_hamiltonian,
        )
