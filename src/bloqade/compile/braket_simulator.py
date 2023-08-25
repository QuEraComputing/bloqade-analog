from bloqade.codegen.common.static_assign import StaticAssignProgram
from bloqade.codegen.hardware.quera import SchemaCodeGen
from bloqade.ir.program import Program
from bloqade.submission.ir.braket import to_braket_task_ir

from pydantic.dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bloqade.task.batch import LocalBatch


@dataclass
class BraketLocalEmulatorBatchCompiler:
    program: Program

    def compile(self, shots, args, name: Optional[str]) -> "LocalBatch":
        from bloqade.task.braket_simulator import BraketEmulatorTask
        from bloqade.task.batch import LocalBatch
        from bloqade.ir import ParallelRegister

        if isinstance(self.program.register, ParallelRegister):
            raise ValueError(
                "Braket local emulator does not support parallel registers."
            )

        params = self.program.parse_args(*args)
        static_params = {**params, **self.program.static_params}

        precompiled_program = StaticAssignProgram(static_params).visit(self.program)

        tasks = []
        for batch_parmas in self.program.batch_params:
            metadata = {**batch_parmas, **params}

            quera_task_ir, parallel_decoder = SchemaCodeGen(batch_parmas).emit(
                shots, precompiled_program
            )

            task = BraketEmulatorTask(
                task_id=None,
                task_ir=to_braket_task_ir(quera_task_ir),
                metadata=metadata,
                task_result_ir=None,
            )

            tasks.append(task)

        return LocalBatch(tasks, name)
