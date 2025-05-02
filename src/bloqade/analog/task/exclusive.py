import os
import abc
import uuid
import re
import time

from beartype.typing import Dict
from dataclasses import dataclass, field

from bloqade.analog.task.base import Geometry, CustomRemoteTaskABC
from bloqade.analog.builder.typing import ParamType
from bloqade.analog.submission.ir.parallel import ParallelDecoder
from bloqade.analog.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
)
from bloqade.analog.submission.ir.task_specification import QuEraTaskSpecification
from requests import request, get
from bloqade.analog.serialize import Serializer


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


def convert_preview_to_download(preview_url):
    # help function to convert the googledrive preview URL to download URL
    # Only used in http handler
    match = re.search(r"/d/([^/]+)/", preview_url)
    if not match:
        raise ValueError("Invalid preview URL format")
    file_id = match.group(1)
    return f"https://drive.usercontent.google.com/download?id={file_id}&export=download"


class HTTPHandler(HTTPHandlerABC):
    def __init__(
        self,
        zapier_webhook_url: str = None,
        zapier_webhook_key: str = None,
        vercel_api_url: str = None,
    ):
        self.zapier_webhook_url = zapier_webhook_url or os.environ["ZAPIER_WEBHOOK_URL"]
        self.zapier_webhook_key = zapier_webhook_key or os.environ["ZAPIER_WEBHOOK_KEY"]
        self.verrcel_api_url = vercel_api_url or os.environ["VERCEL_API_URL"]

    def submit_task_via_zapier(
        self, task_ir: QuEraTaskSpecification, task_id: str, task_note: str
    ):
        # implement http request logic to submit task via Zapier
        request_options = dict(params={"key": self.zapier_webhook_key, "note": task_id})

        # for metadata, task_ir in self._compile_single(shots, use_experimental, args):
        json_request_body = task_ir.json(exclude_none=True, exclude_unset=True)

        request_options.update(data=json_request_body)
        response = request("POST", self.zapier_webhook_url, **request_options)

        if response.status_code == 200:
            response_data = response.json()
            submit_status = response_data.get("status", None)
            return submit_status
        else:
            print(f"HTTP request failed with status code: {response.status_code}")
            print("HTTP responce: ", response.text)
            return "Failed"

    def query_task_status(self, task_id: str):
        response = request(
            "GET",
            self.verrcel_api_url,
            params={
                "searchPattern": task_id,
                "magicToken": self.zapier_webhook_key,
                "useRegex": False,
            },
        )
        if response.status_code != 200:
            return "Not Found"
        response_data = response.json()
        # Get "matched" from the response
        matches = response_data.get("matches", None)
        # The return is a list of dictionaries
        # Verify if the list contains only one element
        if matches is None:
            print("No task found with the given ID.")
            return "Failed"
        elif len(matches) > 1:
            print("Multiple tasks found with the given ID.")
            return "Failed"

        # Extract the status from the first dictionary
        status = matches[0].get("status")
        return status

    def fetch_results(self, task_id: str):
        response = request(
            "GET",
            self.verrcel_api_url,
            params={
                "searchPattern": task_id,
                "magicToken": self.zapier_webhook_key,
                "useRegex": False,
            },
        )
        if response.status_code != 200:
            print(f"HTTP request failed with status code: {response.status_code}")
            print("HTTP responce: ", response.text)
            return None

        response_data = response.json()
        # Get "matched" from the response
        matches = response_data.get("matches", None)
        # The return is a list of dictionaries
        # Verify if the list contains only one element
        if matches is None:
            print("No task found with the given ID.")
            return None
        elif len(matches) > 1:
            print("Multiple tasks found with the given ID.")
            return None
        record = matches[0]
        if record.get("status") == "Completed":
            googledoc = record.get("resultsFileUrl")

            # convert the preview URL to download URL
            googledoc = convert_preview_to_download(googledoc)
            res = get(googledoc)
            res.raise_for_status()
            data = res.json()

            task_results = QuEraTaskResults(**data)
        return task_results


class TestHTTPHandler(HTTPHandlerABC):
    pass


@dataclass
@Serializer.register
class ExclusiveRemoteTask(CustomRemoteTaskABC):
    _task_ir: QuEraTaskSpecification | None
    _metadata: Dict[str, ParamType]
    _parallel_decoder: ParallelDecoder | None
    _http_handler: HTTPHandlerABC = field(default_factory=HTTPHandler)
    _task_id: str | None = None
    _task_result_ir: QuEraTaskResults | None = None

    def __post_init__(self):
        float_sites = list(
            map(lambda x: (float(x[0]), float(x[1])), self._task_ir.lattice.sites)
        )
        self._geometry = Geometry(
            float_sites, self._task_ir.lattice.filling, self._parallel_decoder
        )

    @classmethod
    def from_compile_results(cls, task_ir, metadata, parallel_decoder):
        return cls(
            _task_ir=task_ir,
            _metadata=metadata,
            _parallel_decoder=parallel_decoder,
        )

    def _submit(self, force: bool = False) -> "ExclusiveRemoteTask":
        if not force:
            if self._task_id is not None:
                raise ValueError(
                    "the task is already submitted with %s" % (self._task_id)
                )
        self._task_id = str(uuid.uuid4())

        if (
            self._http_handler.submit_task_via_zapier(
                self._task_ir, self._task_id, None
            )
            == "success"
        ):
            self._task_result_ir = QuEraTaskResults(
                task_status=QuEraTaskStatusCode.Accepted
            )
        else:
            self._task_result_ir = QuEraTaskResults(
                task_status=QuEraTaskStatusCode.Failed
            )
        return self

    def fetch(self):
        if self._task_result_ir.task_status is QuEraTaskStatusCode.Unsubmitted:
            raise ValueError("Task ID not found.")

        if self._task_result_ir.task_status in [
            QuEraTaskStatusCode.Completed,
            QuEraTaskStatusCode.Partial,
            QuEraTaskStatusCode.Failed,
            QuEraTaskStatusCode.Unaccepted,
            QuEraTaskStatusCode.Cancelled,
        ]:
            return self

        status = self.status()
        if status in [QuEraTaskStatusCode.Completed, QuEraTaskStatusCode.Partial]:
            self._task_result_ir = self._http_handler.fetch_results(self._task_id)
        else:
            self._task_result_ir = QuEraTaskResults(task_status=status)

        return self

    def pull(self, poll_interval: float = 20):
        """
        Blocking pull to get the task result.
        poll_interval is the time interval to poll the task status.
        Please ensure that it is relatively large, otherwise
        the server could get overloaded with queries.
        """

        while True:
            if self._task_result_ir.task_status is QuEraTaskStatusCode.Unsubmitted:
                raise ValueError("Task ID not found.")

            if self._task_result_ir.task_status in [
                QuEraTaskStatusCode.Completed,
                QuEraTaskStatusCode.Partial,
                QuEraTaskStatusCode.Failed,
                QuEraTaskStatusCode.Unaccepted,
                QuEraTaskStatusCode.Cancelled,
            ]:
                return self

            status = self.status()
            if status in [QuEraTaskStatusCode.Completed, QuEraTaskStatusCode.Partial]:
                self._task_result_ir = self._http_handler.fetch_results(self._task_id)
                return self

            time.sleep(poll_interval)

    def cancel(self):
        # This is not supported
        raise NotImplementedError("Cancelling is not supported.")

    def status(self) -> QuEraTaskStatusCode:
        if self._task_id is None:
            return QuEraTaskStatusCode.Unsubmitted
        res = self._http_handler.query_task_status(self._task_id)
        if res == "Failed":
            raise ValueError("Query task status failed.")
        elif res == "Submitted":
            return QuEraTaskStatusCode.Enqueued
        # TODO: please add all possible status
        elif res == "Completed":
            return QuEraTaskStatusCode.Completed
        elif res == "Running":
            # Not covered by test
            return QuEraTaskStatusCode.Executing
        else:
            return self._task_result_ir.task_status

    def _result_exists(self):
        if self._task_result_ir is None:
            return False
        else:
            if self._task_result_ir.task_status == QuEraTaskStatusCode.Completed:
                return True
            else:
                return False

    def result(self):
        if self._task_result_ir is None:
            raise ValueError("Task result not found.")
        return self._task_result_ir

    @property
    def metadata(self):
        return self._metadata

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

    @property
    def parallel_decoder(self):
        return self._parallel_decoder

    @task_result_ir.setter
    def task_result_ir(self, task_result_ir: QuEraTaskResults):
        self._task_result_ir = task_result_ir


@ExclusiveRemoteTask.set_serializer
def _serialze(obj: ExclusiveRemoteTask) -> Dict[str, ParamType]:
    return {
        "task_id": obj.task_id or None,
        "task_ir": obj.task_ir.dict(by_alias=True, exclude_none=True),
        "metadata": obj.metadata,
        "parallel_decoder": (
            obj.parallel_decoder.dict() if obj.parallel_decoder else None
        ),
        "task_result_ir": obj.task_result_ir.dict() if obj.task_result_ir else None,
    }


@ExclusiveRemoteTask.set_deserializer
def _deserializer(d: Dict[str, any]) -> ExclusiveRemoteTask:
    d1 = dict()
    d1["_task_ir"] = QuEraTaskSpecification(**d["task_ir"])
    d1["_parallel_decoder"] = (
        ParallelDecoder(**d["parallel_decoder"]) if d["parallel_decoder"] else None
    )
    d1["_metadata"] = d["metadata"]
    d1["_task_result_ir"] = (
        QuEraTaskResults(**d["task_result_ir"]) if d["task_result_ir"] else None
    )
    d1["_task_id"] = d["task_id"]

    return ExclusiveRemoteTask(**d1)
