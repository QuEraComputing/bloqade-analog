from bloqade.builder.base import ParamType
from bloqade.submission.ir.parallel import ParallelDecoder
from bloqade.task.base import Geometry, RemoteTask
from bloqade.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.submission.braket import BraketBackend

from bloqade.submission.base import ValidationError
from bloqade.submission.ir.task_results import QuEraTaskResults, QuEraTaskStatusCode
import warnings
from dataclasses import dataclass
from typing import Dict, Optional


## keep the old conversion for now,
## we will remove conversion btwn QuEraTask <-> BraketTask,
## and specialize/dispatching here.
@dataclass
class BraketTask(RemoteTask):
    task_id: Optional[str]
    backend: BraketBackend
    task_ir: QuEraTaskSpecification
    metadata: Dict[str, ParamType]
    parallel_decoder: Optional[ParallelDecoder]
    task_result_ir: Optional[QuEraTaskResults] = None

    def submit(self, force: bool = False) -> None:
        if not force:
            if self.task_id is not None:
                raise ValueError(
                    "the task is already submitted with %s" % (self.task_id)
                )
        self.task_id = self.backend.submit_task(self.task_ir)

        return self

    def validate(self) -> str:
        try:
            self.backend.validate_task(self.task_ir)
        except ValidationError as e:
            return str(e)

        return self

    def fetch(self) -> None:
        # non-blocking, pull only when its completed
        if self.task_id is None:
            raise ValueError("Task ID not found.")

        if self.status() == QuEraTaskStatusCode.Completed:
            self.task_result_ir = self.backend.task_results(self.task_id)

        return self

    def pull(self) -> None:
        # blocking, force pulling, even its completed
        if self.task_id is None:
            raise ValueError("Task ID not found.")

        self.task_result_ir = self.backend.task_results(self.task_id)

        return self

    def result(self) -> QuEraTaskResults:
        # blocking, caching
        if self.task_result_ir is None:
            self.pull()

        return self.task_result_ir

    def status(self) -> QuEraTaskStatusCode:
        return self.backend.task_status(self.task_id)

    def cancel(self) -> None:
        if self.task_id is None:
            warnings.warn("Cannot cancel task, missing task id.")
            return

        self.backend.cancel_task(self.task_id)

    @property
    def nshots(self):
        return self.task_ir.nshots

    def _geometry(self) -> Geometry:
        return Geometry(
            sites=self.task_ir.lattice.sites,
            filling=self.task_ir.lattice.filling,
            parallel_decoder=self.parallel_decoder,
        )

    def _result_exists(self) -> bool:
        return self.task_result_ir is not None

    # def submit_no_task_id(self) -> "HardwareTaskShotResults":
    #    return HardwareTaskShotResults(hardware_task=self)
