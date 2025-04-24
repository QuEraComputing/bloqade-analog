import os
import abc
import uuid
import json
import re

from beartype.typing import Dict

from bloqade.analog.task.base import Geometry, CustomRemoteTaskABC
from bloqade.analog.builder.typing import ParamType
from bloqade.analog.submission.ir.parallel import ParallelDecoder
from bloqade.analog.submission.ir.task_results import (
    QuEraTaskResults,
    QuEraTaskStatusCode,
)
from bloqade.analog.submission.ir.task_specification import QuEraTaskSpecification
from requests import Response, request, get


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
    def __init__(self, zapier_webhook_url: str, zapier_webhook_key: str, vercel_api_url: str):
        self.zapier_webhook_url = zapier_webhook_url
        self.zapier_webhook_key = zapier_webhook_key
        self.verrcel_api_url = vercel_api_url

    def submit_task_via_zapier(self, task_ir: QuEraTaskSpecification, task_id: str, task_note: str):
        # implement http request logic to submit task via Zapier
        request_options = dict(
            params={"key": self.zapier_webhook_key, "note": task_id})

        # for metadata, task_ir in self._compile_single(shots, use_experimental, args):
        json_request_body = task_ir.json(exclude_none=True, exclude_unset=True)

        request_options.update(data=json_request_body)
        response = request("POST", self.zapier_webhook_url, **request_options)

        if response.status_code == 200:
            response_data = response.json()
            submit_status = response_data.get("status", None)
            return submit_status
        else:
            print(
                f"HTTP request failed with status code: {response.status_code}")
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
        return QuEraTaskStatusCode(status)


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
            print(
                f"HTTP request failed with status code: {response.status_code}")
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
            # test_google_doc = "https://drive.usercontent.google.com/download?id=1hvUlzzpIpl5FIsXDjetGeQQKoYW9LrAn&export=download&authuser=0"
            googledoc = record.get("resultsFileUrl")

            # convert the preview URL to download URL
            googledoc = convert_preview_to_download(
                googledoc)
            res = get(googledoc)
            res.raise_for_status()
            data = res.json()

            task_results = QuEraTaskResults(**data)
        return task_results


class TestHTTPHandler(HTTPHandlerABC):
    pass


class ExclusiveRemoteTask(CustomRemoteTaskABC):
    def __init__(
        self,
        task_ir: QuEraTaskSpecification,
        metadata: Dict[str, ParamType],
        parallel_decoder: ParallelDecoder | None,
        http_handler: HTTPHandlerABC | None = None,
    ):
        self.zapier_webhook_url = os.environ["ZAPIER_WEBHOOK_URL"]
        self.zapier_webhook_key = os.environ["ZAPIER_WEBHOOK_KEY"]
        self.vercel_api_url = os.environ["VERCEL_API_URL"]
        self._http_handler = http_handler or HTTPHandler(zapier_webhook_url=self.zapier_webhook_url,
                                                         zapier_webhook_key=self.zapier_webhook_key,
                                                         vercel_api_url=self.vercel_api_url)
        self._task_ir = task_ir
        self._metadata = metadata
        self._parallel_decoder = parallel_decoder
        float_sites = list(
            map(lambda x: (float(x[0]), float(x[1])), task_ir.lattice.sites)
        )
        self._geometry = Geometry(
            float_sites, task_ir.lattice.filling, parallel_decoder
        )
        self._task_id = None
        self._task_result_ir = None
        # self.air_table_url = os.environ["AIR_TABLE_URL"]
        # self.air_table_api_key = os.environ["AIR_TABLE_API_KEY"]

    @classmethod
    def from_compile_results(cls, task_ir, metadata, parallel_decoder):
        return cls(
            task_ir=task_ir,
            metadata=metadata,
            parallel_decoder=parallel_decoder,
        )

    def _submit(self, force: bool = False) -> "ExclusiveRemoteTask":
        if not force:
            if self._task_id is not None:
                raise ValueError(
                    "the task is already submitted with %s" % (self._task_id)
                )
        self._task_id = str(uuid.uuid4())
        if self._http_handler.submit_task_via_zapier(self._task_ir, self._task_id, None) == "success":
            self._task_result_ir = QuEraTaskResults(
                task_status=QuEraTaskStatusCode.Accepted)
        else:
            self._task_result_ir = QuEraTaskResults(
                task_status=QuEraTaskStatusCode.Failed)
        print(self.task_result_ir)
        return self

    def fetch(self):
        if self.task_result_ir.task_status is QuEraTaskStatusCode.Unsubmitted:
            raise ValueError("Task ID not found.")

        if self.task_result_ir.task_status in [
            QuEraTaskStatusCode.Completed,
            QuEraTaskStatusCode.Partial,
            QuEraTaskStatusCode.Failed,
            QuEraTaskStatusCode.Unaccepted,
            QuEraTaskStatusCode.Cancelled,
        ]:
            return self

        status = self.status()
        if status in [QuEraTaskStatusCode.Completed, QuEraTaskStatusCode.Partial]:
            self.task_result_ir = self._http_handler.fetch_results(
                self.task_id)
        else:
            self.task_result_ir = QuEraTaskResults(task_status=status)

        return self

    def pull(self):
        # Please avoid use this method, it's blocking and the wating time is hours long
        pass

    def cancel(self):
        pass

    def validate(self) -> str:
        pass

    def status(self) -> QuEraTaskStatusCode:
        if self._task_id is None:
            return QuEraTaskStatusCode.Unsubmitted
        print("status: self._task_id = ", self._task_id)
        res = self._http_handler.query_task_status(self._task_id)
        if res != "Not Found":
            return res
        elif res == "Failed":
            # through an error
            raise ValueError("Query task status failed.")
        else:
            return self.task_result_ir.task_status

    def _result_exists(self):
        if self.task_result_ir is None:
            return False
        else:
            if self.task_result_ir.task_status == QuEraTaskStatusCode.Completed:
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


# @ExclusiveRemoteTask.set_serializer
# def _serialze(obj: ExclusiveRemoteTask) -> Dict[str, ParamType]:
#    # TODO: Not tested, once it's done, resolve the DEBUG flag
#    return {
#        "task_id": obj.task_id or None,
#        "task_ir": obj.task_ir.dict(by_alias=True, exclude_none=True),
#        "metadata": obj.metadata,
#        "zapier_webhook_url": obj.zapier_webhook_url,
#        "zapier_webhook_key": obj.zapier_webhook_key,
#        "vercel_api_url": obj.vercel_api_url,
#        "parallel_decoder": (
#            obj.parallel_decoder.dict() or None
#        ),
#        "geometry": obj.geometry.dict() or None,
#        "task_result_ir": obj.task_result_ir.dict() if obj.task_result_ir else None,
#    }


# @ExclusiveRemoteTask.set_deserializer
# def _deserializer(d: Dict[str, Any]) -> ExclusiveRemoteTask:
#     # TODO: Not tested, once it's done, resolve the DEBUG flag
#     d["task_ir"] = QuEraTaskSpecification(**d["task_ir"])
#     d["parallel_decoder"] = (
#         ParallelDecoder(**d["parallel_decoder"]
#                         ) if d["parallel_decoder"] else None
#     )
#     d["http_handler"] = HTTPHandler(
#         zapier_webhook_url=d["zapier_webhook_url"],
#         zapier_webhook_key=d["zapier_webhook_key"],
#         vercel_api_url=d["vercel_api_url"],
#     )

#     return ExclusiveRemoteTask(**d)
