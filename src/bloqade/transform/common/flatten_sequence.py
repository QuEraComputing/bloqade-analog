import bloqade.ir.control.sequence as sequence
import bloqade.ir.control.pulse as pulse
import bloqade.ir.control.field as field
import bloqade.ir.control.waveform as waveform
import bloqade.ir.scalar as scalar
from bloqade.ir.visitor import BloqadeIRTransformer
from bloqade.analysis.common.scan_channels import Channels
from beartype import beartype

# Passes for compiling to hardware
# 1. Scan all spatial modulations, validate here
# 2. Insert zero waveform in the explicit time intervals missing a waveform
# 3. Flatten all sequences to a single sequence by moving slices/appends to waveform
#    level
# 4. Assign variables, validate here
# 5. Move the waveform slices into appends
# 5. Validate waveform to be hardware compatible
# 6. generate IR for hardware


class FillMissingWaveforms(BloqadeIRTransformer):
    def __init__(self, channels: Channels):
        self.level_couplings = channels.level_couplings
        self.field_names = channels.field_names
        self.spatial_modulations = channels.spatial_modulations

    def visit_sequence_Sequence(self, node: sequence.Sequence) -> sequence.Sequence:
        pulses = {}
        for lc in self.level_couplings:
            pulses[lc] = self.visit(node.pulses.get(lc, pulse.Pulse({})))

        return sequence.Sequence(pulses)

    def visit_pulse_Pulse(self, node: pulse.Pulse) -> pulse.Pulse:
        duration = node.duration
        fields = {}
        empty_wf = waveform.Constant(0, duration)
        empty_f = field.Field({sm: empty_wf for sm in self.spatial_modulations})
        for fn in self.field_names:
            fields[fn] = self.visit(node.fields.get(fn, empty_f))

        return pulse.Pulse(fields)

    def visit_field_Field(self, node: field.Field) -> field.Field:
        duration = node.duration
        drives = {}

        for sm in self.spatial_modulations:
            wf = node.drives.get(sm, waveform.Constant(0, duration))
            diff_duration = duration - wf.duration

            if isinstance(wf, waveform.AlignedWaveform):
                if isinstance(wf.value, waveform.Side):
                    value = scalar.var(f"__record_value_{hash(wf) ^ hash(wf.value)}__")
                    wf = wf.record(value, wf.value)
                    padding = waveform.Constant(value, diff_duration)
                else:
                    value = wf.value

                padding = waveform.Constant(wf.value, diff_duration)

                if wf.alignment is waveform.Alignment.Left:
                    new_wf = wf.append(padding)
                else:
                    new_wf = padding.append(wf)
            else:
                padding = waveform.Constant(0, diff_duration)
                new_wf = wf.append(padding)

            drives[sm] = new_wf

        return field.Field(drives)


class FlattenSequences(BloqadeIRTransformer):
    # every visitor for sequence returns a Sequence

    @beartype
    def __init__(self, channels: Channels):
        self.level_couplings = channels.level_couplings
        self.field_names = channels.field_names
        self.spatial_modulations = channels.spatial_modulations

    def visit_sequence_Append(self, node: sequence.Append) -> sequence.Sequence:
        seqs = [self.visit(s) for s in node.sequences]

        pulses = {}
        for lc in self.level_couplings:
            for s in seqs:
                p = s.pulses[lc]
                if lc in pulses:
                    pulses[lc] = pulses[lc].append(p)
                else:
                    pulses[lc] = p

        return self.visit(sequence.Sequence(pulses))

    def visit_sequence_Slice(self, node: sequence.Slice) -> sequence.Sequence:
        seq = self.visit(node.sequence)
        interval = node.interval

        pulses = {}

        for lc in self.level_couplings:
            p = seq.pulses[lc]
            pulses[lc] = p[interval.start : interval.stop]

        return self.visit(sequence.Sequence(pulses))

    def visit_sequence_NamedSequence(
        self, node: sequence.NamedSequence
    ) -> sequence.Sequence:
        return self.visit(node.sequence)

    def visit_pulse_Slice(self, node: pulse.Slice) -> pulse.Pulse:
        pul = self.visit(node.pulse)
        interval = node.interval

        fields = {}

        for fn in self.field_names:
            f = pul.fields[fn]
            drives = {}
            for sm in self.spatial_modulations:
                wf = f.drives[sm]
                drives[sm] = wf[interval.start : interval.stop]

            fields[fn] = field.Field(drives)

        return self.visit(pulse.Pulse(fields))

    def visit_pulse_Append(self, node: pulse.Append) -> pulse.Pulse:
        pulses = [self.visit(p) for p in node.pulses]

        fields = {}
        for p in pulses:
            for fn in self.field_names:
                drives = {}
                for sm in self.spatial_modulations:
                    wf = p.fields[fn].drives[sm]
                    if sm in drives:
                        drives[sm] = drives[sm].append(wf)
                    else:
                        drives[sm] = wf

            fields[fn] = field.Field(drives)

        return self.visit(pulse.Pulse(fields))

    def visit_pulse_NamedPulse(self, node: pulse.NamedPulse) -> pulse.Pulse:
        return self.visit(node.pulse)
