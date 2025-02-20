from bloqade.analog.builder.base import Builder
from bloqade.analog.builder.field import Rabi, Detuning


class LevelCoupling(Builder):
    @property
    def detuning(self) -> Detuning:
        """
        Specify the [`Detuning`][bloqade.analog.builder.field.Detuning] [`Field`][bloqade.analog.builder.field.Field] of your program.
        You will be able to specify the spatial modulation afterwards.

        Args:
            None

        Returns:
            [`Detuning`][bloqade.analog.builder.field.Detuning]: A program node representing the detuning field.

        Note:
            The detuning specifies how off-resonant the laser being applied to the atoms is from the atomic energy transition, driven by the Rabi frequency.

            Example:
                ```python
                from bloqade import start
                geometry = start.add_position((0,0))
                coupling = geometry.rydberg
                coupling.detuning
                ```

            - Next Possible Steps
            You may continue building your program via:
            - [`uniform`][bloqade.analog.builder.field.Detuning.uniform]: To address all atoms in the field
            - [`location(locations, scales)`][bloqade.analog.builder.field.Detuning.location]: To address atoms at specific
            locations via indices
            - [`scale(coeffs)`][bloqade.analog.builder.field.Detuning.scale]: To address all atoms with an individual scale factor
        """

        return Detuning(self)

    @property
    def rabi(self) -> Rabi:
        """
        Specify the complex-valued [`Rabi`][bloqade.analog.builder.field.Rabi]
        field of your program.

        The Rabi field is composed of a real-valued Amplitude and Phase field.


        Args:
            None

        Returns:
            Rabi: A program node representing the Rabi field.

        Note:
            Next possible steps to build your program are
            creating the RabiAmplitude field and RabiPhase field of the field:
            - `...rabi.amplitude`: To create the Rabi amplitude field
            - `...rabi.phase`: To create the Rabi phase field
        """

        return Rabi(self)


class Rydberg(LevelCoupling):
    """
    This node represents level coupling of the Rydberg state.

    Examples:

        - To reach the node from the start node:
        >>> from bloqade.analog import start
        >>> node = start.rydberg
        >>> type(node)
        <class 'bloqade.analog.builder.coupling.Rydberg'>

        - Rydberg level coupling has two reachable field nodes:

            - detuning term (See also [`Detuning`][bloqade.analog.builder.field.Detuning])
            - rabi term (See also [`Rabi`][bloqade.analog.builder.field.Rabi])

        >>> ryd_detune = start.rydberg.detuning
        >>> ryd_rabi = start.rydberg.rabi
    """

    def __bloqade_ir__(self):
        """
        Generate the intermediate representation (IR) for the Rydberg level coupling.

        Args:
            None

        Returns:
            IR: An intermediate representation of the Rydberg level coupling sequence.

        Raises:
            None

        Note:
            This method is used internally by the Bloqade framework.
        """
        from bloqade.analog.ir.control.sequence import rydberg

        return rydberg


class Hyperfine(LevelCoupling):
    """
    This node represents level coupling between hyperfine states.

    Examples:

        - To reach the node from the start node:
        >>> from bloqade.analog import start
        >>> node = start.hyperfine
        >>> type(node)
        <class 'bloqade.analog.builder.coupling.Hyperfine'>

        - Hyperfine level coupling has two reachable field nodes:

            - detuning term (See also [`Detuning`][bloqade.analog.builder.field.Detuning])
            - rabi term (See also [`Rabi`][bloqade.analog.builder.field.Rabi])

        >>> hyp_detune = start.hyperfine.detuning
        >>> hyp_rabi = start.hyperfine.rabi
    """

    def __bloqade_ir__(self):
        """
        Generate the intermediate representation (IR) for the Hyperfine level coupling.

        Args:
            None

        Returns:
            IR: An intermediate representation of the Hyperfine level coupling sequence.

        Raises:
            None

        Note:
            This method is used internally by the Bloqade framework.
        """
        from bloqade.analog.ir.control.sequence import hyperfine

        return hyperfine
