from pydantic.dataclasses import dataclass
from bloqade.builder.start import ProgramStart
from numpy.typing import NDArray
from typing import List, Generator
from bokeh.plotting import show
import numpy as np


class AtomArrangement(ProgramStart):
    def __init__(self) -> None:
        super().__init__(register=self)

    def enumerate(self) -> Generator[NDArray, None, None]:
        """enumerate all positions in the register."""
        raise NotImplementedError

    def figure(self):
        """plot the register."""
        raise NotImplementedError

    def show(self) -> None:
        """show the register."""
        show(self.figure())

    @property
    def n_atoms(self):
        raise NotImplementedError

    @property
    def n_dims(self):
        raise NotImplementedError

    def multiplex(self, cluster_spacing: float) -> "MultuplexRegister":
        if self.n_atoms > 0:
            # calculate bounding box
            # of this register
            x_min = np.inf
            x_max = -np.inf
            y_min = np.inf
            y_max = -np.inf

            for x, y in self.enumerate():
                x_min = min(x, x_min)
                x_max = max(x, x_max)
                y_min = min(y, y_min)
                y_max = max(y, y_max)

            shift_x = (x_max - x_min) + cluster_spacing
            shift_y = (y_max - y_min) + cluster_spacing

            register_sites = [list(position) for position in self.enumerate()]
            return MultuplexRegister(
                register_sites=register_sites,
                shift_vectors=[[shift_x, 0], [0, shift_y]],
            )
        else:
            raise ValueError("No locations to multiplex.")


@dataclass(init=False)
class MultuplexRegister(ProgramStart):
    register_sites: List[List[float]]
    shift_vectors: List[List[float]]

    def __init__(
        self, register_sites: List[List[float]], shift_vectors: List[List[float]]
    ):
        self.register_sites = register_sites
        self.shift_vectors = shift_vectors
        super().__init__(register=self)
