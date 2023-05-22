from pydantic import BaseModel
from bloqade.submission.ir.task_results import QuEraTaskResults
from bloqade.submission.mock import DumbMockBackend
from bloqade.submission.quera import QuEraBackend
from bloqade.submission.braket import BraketBackend
from bloqade.submission.ir.braket import BraketTaskSpecification
from bloqade.submission.ir.task_specification import (
    QuEraTaskSpecification,
)
from bloqade.submission.ir.task_results import QuEraTaskStatusCode

from .base import Task, TaskFuture, Future, Job

from typing import Optional, List

import numpy as np


class TaskDataModel(BaseModel):
    # note that the separate types here are because pydantic
    # will automatically convert between the types in a Union
    quera_task_ir: Optional[QuEraTaskSpecification] = None
    braket_task_ir: Optional[BraketTaskSpecification] = None
    mock_backend: Optional[DumbMockBackend] = None
    quera_backend: Optional[QuEraBackend] = None
    braket_backend: Optional[BraketBackend] = None

    def _check_fields(self) -> None:
        if self.quera_task_ir is None and self.braket_task_ir is None:
            raise AttributeError("Missing task_ir.")

        if (
            self.braket_backend is None
            and self.mock_backend is None
            and self.quera_backend is None
        ):
            raise AttributeError("No backend found for hardware task.")


class HardwareTask(TaskDataModel, Task):
    def submit(self) -> "HardwareTaskFuture":
        self._check_fields()
        if self.braket_backend:
            task_id = self.braket_backend.submit_task(self.braket_task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                braket_task_ir=self.braket_task_ir,
                braket_backend=self.braket_backend,
            )
        if self.quera_backend:
            task_id = self.quera_backend.submit_task(self.quera_task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                quera_task_ir=self.quera_task_ir,
                quera_backend=self.quera_backend,
            )
        if self.mock_backend:
            task_id = self.mock_backend.submit_task(self.quera_task_ir)
            return HardwareTaskFuture(
                task_id=task_id,
                quera_task_ir=self.quera_task_ir,
                mock_backend=self.mock_backend,
            )

    def run_validation(self) -> None:
        self._check_fields()

        if self.braket_backend:
            self.braket_backend.validate_task(self.braket_task_ir)

        if self.quera_backend:
            self.quera_backend.validate_task(self.quera_task_ir)

        if self.mock_backend:
            self.mock_backend.validate_task(self.quera_task_ir)


class TaskFutureDataModel(TaskDataModel):
    task_id: Optional[str] = None

    def _check_fields(self):
        super()._check_fields()

        if self.task_id is None:
            raise AttributeError("Missing task_id.")


class HardwareTaskFuture(TaskFutureDataModel, TaskFuture):
    def status(self) -> QuEraTaskStatusCode:
        self._check_fields()

        if self.braket_backend:
            self.braket_backend.task_status(self.task_id)

        if self.quera_backend:
            self.quera_backend.task_status(self.task_id)

        if self.mock_backend:
            self.mock_backend.task_status(self.task_id)

    def cancel(self) -> None:
        self._check_fields()
        if self.status() in [
            QuEraTaskStatusCode.Complete,
            QuEraTaskStatusCode.Running,
            QuEraTaskStatusCode.Accepted,
        ]:
            return

        if self.braket_backend:
            self.braket_backend.cancel_task(self.task_id)

        if self.quera_backend:
            self.quera_backend.cancel_task(self.task_id)

        if self.mock_backend:
            self.mock_backend.cancel_task(self.task_id)

    def fetch(self) -> QuEraTaskResults:
        self._check_fields()
        if self.braket_backend:
            return self.braket_backend.task_results(self.task_id)

        if self.quera_backend:
            return self.quera_backend.task_results(self.task_id)

        if self.mock_backend:
            return self.mock_backend.task_results(self.task_id)


class HardwareJob(BaseModel, Job):
    tasks: List[HardwareTask]
    task_submit_order: List[int]

    def __init__(self, tasks: List[HardwareTask], task_submit_order=None):
        if task_submit_order is None:
            task_submit_order = list(np.random.permutation(len(tasks)))

        super().__init__(tasks=tasks, task_submit_order=task_submit_order)

    def submit(self) -> "HardwareFuture":
        try:
            self.tasks[0].run_validation()
            has_validation = True
        except NotImplementedError:
            has_validation = False

        if has_validation:
            for task in self.tasks[1:]:
                task.run_validation()

        # submit tasks in random order but store them
        # in the original order of tasks.
        futures = [None for task in self.tasks]
        for task_index in self.task_submit_order:
            try:
                futures[task_index] = self.tasks[task_index].submit()
            except BaseException as e:
                for future in futures:
                    if future is not None:
                        future.cancel()
                raise e

        return HardwareFuture(futures=futures)

    def json(self, exclude_none=True, by_alias=True, **json_options) -> str:
        return super().json(
            exclude_none=exclude_none, by_alias=by_alias, **json_options
        )


class HardwareFuture(Future):
    futures: List[HardwareTaskFuture]

    def __init__(self, futures: List[HardwareTaskFuture]):
        super().__init__(futures=futures, task_results_ir=None)

    def cancel(self) -> None:
        for future in self.futures:
            future.cancel()

    def fetch(self) -> List[QuEraTaskResults]:
        return [future.fetch() for future in self.futures]

    def json(self, exclude_none=True, by_alias=True, **json_options) -> str:
        return super().json(
            exclude_none=exclude_none, by_alias=by_alias, **json_options
        )
