import abc
import os
import uuid

from beartype.typing import Dict

from bloqade.analog.task.base import CustomRemoteTaskABC
from bloqade.analog.builder.typing import ParamType
from bloqade.analog.submission.ir.parallel import ParallelDecoder
from bloqade.analog.submission.ir.task_specification import QuEraTaskSpecification
from bloqade.analog.submission.ir.task_results import QuEraTaskResults, QuEraTaskStatusCode
from bloqade.analog.task.base import Geometry


class HTTPHandlerABC:
    @abc.abstractmethod
    def submit_task_via_zapier(task_ir: QuEraTaskSpecification, task_id: str):
        """Submit a task and add task_id to the task fields for querying later.
        
        args:
            task_ir: The task to be submitted.
            task_id: The task id to be added to the task fields.
        
        returns 
            response: The response from the Zapier webhook. used for error handling
        
        """
        ...
        
    @abc.abstractmethod
    def query_task_status(task_id: str):
        """Query the task status from the AirTable.
        
        args:
            task_id: The task id to be queried.
        
        returns 
            response: The response from the AirTable. used for error handling
        
        """
        ...
        
    @abc.abstractmethod
    def fetch_results(task_id: str):
        """Fetch the task results from the AirTable.
        
        args:
            task_id: The task id to be queried.
        
        returns 
            response: The response from the AirTable. used for error handling
        
        """
        ...

class HTTPHandler(HTTPHandlerABC):
    pass

class TestHTTPHandler(HTTPHandlerABC):
    pass



class ExclusiveRemoteTask(CustomRemoteTaskABC):
    def __init__(
        self,
        task_ir: QuEraTaskSpecification,
        metadata: Dict[str, ParamType],
        parallel_decoder: ParallelDecoder | None,
        http_handler: HTTPHandlerABC| None = None,
    ):
        if http_handler is None:
            http_handler = HTTPHandler()
        
        self._task_ir = task_ir
        self._metadata = metadata
        self._parallel_decoder = parallel_decoder
        float_sites = list(map(lambda x: (float(x[0]), float(x[1])), task_ir.lattice.sites))
        self._geometry = Geometry(
            float_sites, task_ir.lattice.filling, parallel_decoder)
        self._task_id = None
        self._task_result_ir = None
        self.air_table_url = os.environ["AIR_TABLE_URL"]
        self.air_table_api_key = os.environ["AIR_TABLE_API_KEY"]
        self.zapier_webhook_url = os.environ["ZAPIER_WEBHOOK_URL"]
        self.zapier_webhook_key = os.environ["ZAPIER_WEBHOOK_KEY"]

    def pull(self):
        """Block execution until the task is completed and fetch the results."""
        raise NotImplementedError    
    

    @property
    def geometry(self):
        return self._geometry
    
    @property
    def task_ir(self):
        return self._task_ir

    @property
    def task_id(self) -> str:
        assert isinstance(self._task_id, str), "Task ID is not set"
        return self._task_id

    @property
    def task_result_ir(self):
        return self._task_result_ir

    def _submit(self):
        self._task_id = str(uuid.uuid4())

        
