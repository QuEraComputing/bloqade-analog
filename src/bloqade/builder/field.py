from bloqade.builder.base import Builder
from beartype import beartype


class Field(Builder):
    @property
    def uniform(self):
        """
        Address all atoms as part of defining the spatial modulation component
        of a drive.

        Next steps to build your program include choosing the waveform that
        will be summed with the spatial modulation to create a drive.

        The drive by itself, or the sum of subsequent drives (created by just
        chaining the construction of drives) will become the field
        (e.g. Detuning Field, Real-Valued Rabi Amplitude/Rabi Phase Field, etc.).

        - You can now do:
            - `...uniform.linear(start, stop, duration)` : to apply a linear waveform
            - `...uniform.constant(value, duration)` : to apply a constant waveform
            - `...uniform.poly([coefficients], duration)` : to apply a
                polynomial waveform
            - `...uniform.apply(wf:bloqade.ir.Waveform)`: to apply a
            pre-defined waveform
            - `...uniform.piecewise_linear([durations], [values])`:  to apply
            a piecewise linear waveform
            - `...uniform.piecewise_constant([durations], [values])`: to apply
            a piecewise constant waveform
            - `...uniform.fn(f(t,...))`: to apply a function as a waveform

        """
        from bloqade.builder.spatial import Uniform

        return Uniform(self)

    @beartype
    def location(self, label: int):
        """
        Address a single atom (or multiple via chaining calls, see below) as
        part of defining the spatial modulation component of a drive.

        Next steps to build your program include choosing the waveform that
        will be summed with the spatial modulation to create a drive.

        The drive by itself, or the sum of subsequent drives (created by just
        chaining the construction of drives) will become the field.
        (e.g. Detuning Field, Real-Valued Rabi Amplitude/Rabi Phase Field, etc.)

        ### Usage Example:
        ```
        >>> prog = start.add_position([(0,0),(1,4),(2,8)]).rydberg.rabi
        # to target a single atom with a waveform
        >>> one_location_prog = prog.location(0)
        # to target multiple atoms with same waveform
        >>> multi_location_prog = prog.location(0).location(2)
        ```

        - You can now do:
            - `...location(int).linear(start, stop, duration)` : to apply
                a linear waveform
            - `...location(int).constant(value, duration)` : to apply
                a constant waveform
            - `...location(int).poly([coefficients], duration)` : to apply
                a polynomial waveform
            - `...location(int).apply(wf:bloqade.ir.Waveform)`: to apply
                a pre-defined waveform
            - `...location(int).piecewise_linear([durations], [values])`:  to apply
                a piecewise linear waveform
            - `...location(int).piecewise_constant([durations], [values])`: to apply
                a piecewise constant waveform
            - `...location(int).fn(f(t,..))`: to apply a function as a waveform
        - You can also address multiple atoms by chaining:
            - `...location(int).location(int)`
                - The waveform you specify after the last `location` in the chain will
                  be applied to all atoms in the chain
        - And you can scale any waveform by a multiplicative factor on a
            specific atom via:
            - `...location(int).scale(float)`
            - You cannot define a scaling across multiple atoms with one method call!
              They must be specified atom-by-atom.

        """
        from bloqade.builder.spatial import Location

        return Location(label, self)

    @beartype
    def var(self, name: str):
        """
        Address a single atom (or multiple via assigning a list of values) as
        part of defining the spatial modulation component of a drive.

        Next steps to build your program include choosing the waveform that
        will be summed with the spatial modulation to create a drive.

        The drive by itself, or the sum of subsequent drives (created by just
        chaining the construction of drives) will become the field
        (e.g. Detuning Field, Real-Valued Rabi Amplitude/Rabi Phase Field, etc.)

        ### Usage Example:
        ```
        >>> prog = start.add_position([(0,0),(1,4),(2,8)]).rydberg.rabi
        >>> one_location_prog = prog.var("a")
        # "a" can be assigned in the END of the program during variable assignment
        # indicating only a single atom should be targeted OR
        # a list of values, indicating a set of atoms should be targeted.
        >>> target_one_atom = ...assign(a = 0)
        >>> target_multiple_atoms = ...assign(a = [0, 2])
        # Note that `assign` is used, you cannot batch_assign variables used in
        # .var() calls
        ```

        - You can now do:
            - `...var(str).linear(start, stop, duration)` : to apply
                a linear waveform
            - `...var(str).constant(value, duration)` : to apply
                a constant waveform
            - `...var(str).poly([coefficients], duration)` : to apply
                a polynomial waveform
            - `...var(str).apply(wf:bloqade.ir.Waveform)`: to apply
                a pre-defined waveform
            - `...var(str).piecewise_linear(durations, values)`:  to
                apply a piecewise linear waveform
            - `...var(str).piecewise_constant(durations, values)`: to
                apply a piecewise constant waveform
            - `...var(str).fn(f(t,..))`: to apply a function as a waveform

        """
        from bloqade.builder.spatial import Var

        return Var(name, self)


class Detuning(Field):
    """
    This node represent detuning field of a
    specified level coupling (rydberg or hyperfine) type.


    Examples:

        - To specify detuning of rydberg coupling:

        >>> node = bloqade.start.rydberg.detuning
        >>> type(node)
        <class 'bloqade.builder.field.Detuning'>

        - To specify detuning of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.detuning
        >>> type(node)
        <class 'bloqade.builder.field.Detuning'>

    Note:
        This node is a SpatialModulation node.
        See [`SpatialModulation`][bloqade.builder.field.SpatialModulation]
        for additional options.

    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import detuning

        return detuning


# this is just an eye candy, thus
# it's not the actual Field object
# one can skip this node when doing
# compilation
class Rabi(Builder):
    """
    This node represent rabi field of a
    specified level coupling (rydberg or hyperfine) type.

    Examples:

        - To specify rabi of rydberg coupling:

        >>> node = bloqade.start.rydberg.rabi
        <class 'bloqade.builder.field.Rabi'>

        - To specify rabi of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.rabi
        >>> type(node)
        <class 'bloqade.builder.field.Rabi'>


    """

    @property
    def amplitude(self) -> "RabiAmplitude":
        """
        Specify the real-valued Rabi Amplitude field.

        Next steps to build your program focus on specifying a spatial
        modulation.

        The spatial modulation, when coupled with a waveform, completes the
        specification of a "Drive". One or more drives can be summed together
        automatically to create a field such as the Rabi Amplitude here.

        - You can now
            - `...amplitude.uniform`: address all atoms in the field
            - `...amplitude.location(int)`: address a specific atom by its
                index
            - `...amplitude.var(str)`: Address a single atom
                (or multiple via assigning a list of values)

        """
        return RabiAmplitude(self)

    @property
    def phase(self) -> "RabiPhase":
        """
        Specify the real-valued Rabi Phase field.

        Next steps to build your program focus on specifying a spatial
        modulation.

        The spatial modulation, when coupled with a waveform, completes the
        specification of a "Drive". One or more drives can be summed together
        automatically to create a field such as the Rabi Phase here.

        - You can now
            - `...amplitude.uniform`: address all atoms in the field
            - `...amplitude.location(int)`: address a specific atom by its
                index
            - `...amplitude.var(str)`: Address a single atom
                (or multiple via assigning a list of values)

        """
        return RabiPhase(self)


class RabiAmplitude(Field):
    """
    This node represent amplitude of a rabi field.

    Examples:

        - To specify rabi amplitude of rydberg coupling:

        >>> node = bloqade.start.rydberg.rabi.amplitude
        >>> type(node)
        <class 'bloqade.builder.field.Amplitude'>

        - To specify rabi amplitude of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.rabi.amplitude
        >>> type(node)
        <class 'bloqade.builder.field.Amplitude'>

    Note:
        This node is a SpatialModulation node.
        See [`SpatialModulation`][bloqade.builder.field.SpatialModulation]
        for additional options.

    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import rabi

        return rabi.amplitude


class RabiPhase(Field):
    """
    This node represent phase of a rabi field.

    Examples:

        - To specify rabi phase of rydberg coupling:

        >>> node = bloqade.start.rydberg.rabi.phase
        >>> type(node)
        <class 'bloqade.builder.field.Phase'>

        - To specify rabi phase of hyperfine coupling:

        >>> node = bloqade.start.hyperfine.rabi.phase
        >>> type(node)
        <class 'bloqade.builder.field.Phase'>

    Note:
        This node is a SpatialModulation node.
        See [`SpatialModulation`][bloqade.builder.field.SpatialModulation]
        for additional options.
    """

    def __bloqade_ir__(self):
        from bloqade.ir.control.pulse import rabi

        return rabi.phase
