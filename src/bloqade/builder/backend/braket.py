from typing import Optional
from bloqade.builder.base import Builder
from .base import LocalBackend, RemoteBackend

# import bloqade.ir as ir
from bloqade.task.braket import BraketTask
from bloqade.task.braket_simulator import BraketEmulatorTask
import bloqade.submission.braket as braket_submit

# from bloqade.submission.ir.braket import to_braket_task_ir


class BraketService(Builder):
    @property
    def braket(self):
        return BraketDeviceRoute(self)


class BraketDeviceRoute(Builder):
    def aquila(self) -> "Aquila":
        return Aquila(parent=self)

    def local_emulator(self) -> "BraketEmulator":
        return BraketEmulator(parent=self)


class Aquila(RemoteBackend):
    __service_name__ = "braket"
    __device_name__ = "aquila"

    def __init__(
        self,
        # cache_compiled_programs: bool = False,
        parent: Builder | None = None,
    ) -> None:
        # super().__init__(cache_compiled_programs, parent=parent)
        super().__init__(parent=parent)

    """
    def _compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        backend = braket_submit.BraketBackend()

        capabilities = backend.get_capabilities()
        schema_compiler = SchemaCodeGen({}, capabilities=capabilities)
        task_ir = schema_compiler.emit(shots, bloqade_ir)
        task_ir = task_ir.discretize(capabilities)
        return BraketTask(
            task_ir=task_ir,
            backend=backend,
            parallel_decoder=schema_compiler.parallel_decoder,
        )
    """

    def compile_taskdata(self, shots, *args):
        backend = braket_submit.BraketBackend()
        return self._compile_tasks(shots, backend, *args)

    def _compile_taskdata(self, shots, backend, *args):
        from ..compile.quera import QuEraSchemaCompiler

        capabilities = backend.get_capabilities()

        quera_task_data_list = QuEraSchemaCompiler(self, capabilities).compile(
            shots, *args
        )
        return quera_task_data_list

    def compile_tasks(self, shots, *args):
        backend = braket_submit.BraketBackend()
        task_data = self._compile_taskdata(shots, backend, *args)

        return [BraketTask(task_data=dat, backend=backend) for dat in task_data]


class BraketEmulator(LocalBackend):
    __service_name__ = "braket"
    __device_name__ = "local_emulator"

    def __init__(
        self,
        # cache_compiled_programs: bool = False,
        parent: Optional[Builder] = None,
    ) -> None:
        # super().__init__(cache_compiled_programs, parent=parent)
        super().__init__(parent=parent)

    """
    def _compile_task(self, bloqade_ir: ir.Program, shots: int, **metadata):
        from bloqade.codegen.hardware.quera import SchemaCodeGen

        schema_compiler = SchemaCodeGen({})
        task_ir = schema_compiler.emit(shots, bloqade_ir)
        return BraketEmulatorTask(task_ir=to_braket_task_ir(task_ir))
    """

    def compile_taskdata(self, shots, *args):
        from ..compile.braket_simulator import BraketEimulatorCompiler

        braketemu_task_data_list = BraketEimulatorCompiler(self).compile(shots, *args)
        return braketemu_task_data_list

    def compile_tasks(self, shots, *args):
        task_data = self.compile_taskdata(shots, *args)

        return [BraketEmulatorTask(task_data=dat) for dat in task_data]
