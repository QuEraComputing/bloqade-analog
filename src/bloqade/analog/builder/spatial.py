from beartype import beartype
from beartype.typing import TYPE_CHECKING, List, Union, Optional

from bloqade.analog.builder.base import Builder
from bloqade.analog.builder.typing import ScalarType, LiteralType
from bloqade.analog.builder.waveform import WaveformAttachable

if TYPE_CHECKING:
    from bloqade.analog.ir.control.field import (
        RunTimeVector,
        ScaledLocations,
        UniformModulation,
        AssignedRunTimeVector,
    )


class SpatialModulation(WaveformAttachable):
    pass


class Uniform(SpatialModulation):
    """
    The node specify a uniform spacial modulation. Which is ready to apply waveform
    (See [`Waveform`][bloqade.builder.waveform] for available waveform options)

    Examples:

        - To hit this node from the start node:

        >>> reg = bloqade.start.add_position([(0,0),(1,1),(2,2),(3,3)])
        >>> loc = reg.rydberg.detuning.uniform

        - Apply Linear waveform:

        >>> wv = bloqade.ir.Linear(start=0,stop=1,duration=0.5)
        >>> reg = bloqade.start.add_position([(0,0),(1,1),(2,2),(3,3)])
        >>> loc = reg.rydberg.detuning.uniform.apply(wv)

    """

    def __bloqade_ir__(self) -> "UniformModulation":
        from bloqade.analog.ir import Uniform

        return Uniform


class Location(SpatialModulation):
    @beartype
    def __init__(
        self,
        labels: List[int],
        scales: List[ScalarType],
        parent: Optional[Builder] = None,
    ) -> None:
        from bloqade.analog.ir.scalar import cast
        from bloqade.analog.ir.control.field import Location

        super().__init__(parent)
        self._scaled_locations = {
            Location(label): cast(scale) for label, scale in zip(labels, scales)
        }

    def __bloqade_ir__(self) -> "ScaledLocations":
        from bloqade.analog.ir import ScaledLocations

        return ScaledLocations(self._scaled_locations)


class Scale(SpatialModulation):
    @beartype
    def __init__(
        self,
        name_or_list: Union[str, List[LiteralType]],
        parent: Optional[Builder] = None,
    ) -> None:
        super().__init__(parent)
        self._name_or_list = name_or_list

    def __bloqade_ir__(self) -> Union["RunTimeVector", "AssignedRunTimeVector"]:
        from bloqade.analog.ir import RunTimeVector, AssignedRunTimeVector

        if isinstance(self._name_or_list, str):
            return RunTimeVector(self._name_or_list)
        else:
            return AssignedRunTimeVector(None, self._name_or_list)
