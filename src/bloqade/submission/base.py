from bloqade.submission.ir import QuantumTaskIR
from pydantic import BaseModel


class SubmissionBackend(BaseModel):
    def validate_task(self, task_ir: QuantumTaskIR):
        raise NotImplementedError

    def submit_task(self, task_ir: QuantumTaskIR):
        raise NotImplementedError

    def cancel_task(self, task_id: str):
        raise NotImplementedError

    def task_results(self, task_id: str):
        raise NotImplementedError

    def task_status(self, task_id: str):
        raise NotImplementedError
