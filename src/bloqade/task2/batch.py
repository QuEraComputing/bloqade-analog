from collections import OrderedDict
from itertools import product
import json
from typing import Union, Optional
from .base import Report
from .quera import QuEraTask
from .braket import BraketTask
from .braket_simulator import BraketEmulatorTask
import traceback
import datetime
import sys
import os
from bloqade.submission.ir.task_results import (
    QuEraShotStatusCode,
    QuEraTaskStatusCode,
)
import pandas as pd
import numpy as np
from dataclasses import dataclass
from bloqade.submission.base import ValidationError


@dataclass
class LocalBatch:
    tasks: OrderedDict[int, BraketEmulatorTask]
    name: Optional[str] = None

    def report(self) -> Report:
        ## this potentially can be specialize/disatch
        ## offline
        index = []
        data = []

        for task_number, task in self.tasks.items():
            ## fliter not existing results tasks:
            if (task.task_id is None) or (not task._result_exists()):
                continue

            ## filter has result but is not correctly completed.
            if not task.task_result_ir.status == QuEraTaskStatusCode.Completed:
                continue

            geometry = task.geometry
            perfect_sorting = "".join(map(str, geometry.filling))
            parallel_decoder = geometry.parallel_decoder

            if parallel_decoder:
                cluster_indices = parallel_decoder.get_cluster_indices()
            else:
                cluster_indices = {(0, 0): list(range(len(perfect_sorting)))}

            shot_iter = filter(
                lambda shot: shot.shot_status == QuEraShotStatusCode.Completed,
                task.result().shot_outputs,
            )

            for shot, (cluster_coordinate, cluster_index) in product(
                shot_iter, cluster_indices.items()
            ):
                pre_sequence = "".join(
                    map(
                        str,
                        (shot.pre_sequence[index] for index in cluster_index),
                    )
                )

                post_sequence = np.asarray(
                    [shot.post_sequence[index] for index in cluster_index],
                    dtype=np.int8,
                )

                pfc_sorting = "".join(
                    [perfect_sorting[index] for index in cluster_index]
                )

                key = (
                    task_number,
                    cluster_coordinate,
                    pfc_sorting,
                    pre_sequence,
                )

                index.append(key)
                data.append(post_sequence)

        index = pd.MultiIndex.from_tuples(
            index, names=["task_number", "cluster", "perfect_sorting", "pre_sequence"]
        )

        df = pd.DataFrame(data, index=index)
        df.sort_index(axis="index")

        return Report(df)


# this class get collection of tasks
# basically behaves as a psudo queuing system
# the user only need to store this objecet
@dataclass
class RemoteBatch:
    tasks: OrderedDict[int, Union[QuEraTask, BraketTask]]
    name: Optional[str] = None

    class SubmissionException(Exception):
        pass

    def cancel(self) -> None:
        for task in self.tasks.values():
            task.cancel()

    def fetch(self) -> None:
        # online
        for task in self.tasks.values():
            task.fetch()

    def pull(self) -> None:
        for task in self.tasks.values():
            task.pull()

    def __repr__(self):
        return str(self.tasks_metric())

    def tasks_metric(self):
        # [TODO] more info on current status
        tid = []
        data = []
        for int, task in self.tasks.items():
            tid.append(int)

            dat = [None, None]
            dat[1] = task.task_id
            if task.task_id is not None:
                if task.task_result_ir is not None:
                    dat[2] = task.result().task_status.name
            data.append(dat)

        return pd.DataFrame(data, index=tid, columns=["status", "task ID"])

    def remove_invalid_tasks(self):
        new_tasks = OrderedDict()
        for task_number, task in self.tasks.items():
            try:
                task.validate()
                new_tasks[task_number] = task
            except ValidationError:
                continue

        return RemoteBatch(new_tasks, name=self.name)

    def resubmit(self, shuffle_submit_order: bool = True):
        # online
        self._submit(shuffle_submit_order, force=True)

    def _submit(self, shuffle_submit_order: bool = True, **kwargs):
        # online
        if shuffle_submit_order:
            submission_order = np.random.permutation(list(self.tasks.keys()))
        else:
            submission_order = list(self.tasks.keys())

        for task in self.tasks.values():
            try:
                task.validate()
            except NotImplementedError:
                break

        # submit tasks in random order but store them
        # in the original order of tasks.
        # futures = OrderedDict()
        errors = OrderedDict()
        shuffled_tasks = OrderedDict()
        for task_index in submission_order:
            task = self.tasks[task_index]
            shuffled_tasks[task_index] = task
            try:
                task.submit(**kwargs)
            except BaseException as error:
                # record the error in the error dict
                errors[int(task_index)] = {
                    "exception_type": error.__class__.__name__,
                    "stack trace": traceback.format_exc(),
                }
        self.tasks = shuffled_tasks  # permute order using dump way

        if errors:
            time_stamp = datetime.datetime.now()

            if "win" in sys.platform:
                time_stamp = str(time_stamp).replace(":", "~")

            if self.name:
                future_file = f"{self.name}-partial-batch-future-{time_stamp}.json"
                error_file = f"{self.name}-partial-batch-errors-{time_stamp}.json"
            else:
                future_file = f"partial-batch-future-{time_stamp}.json"
                error_file = f"partial-batch-errors-{time_stamp}.json"

            cwd = os.get_cwd()
            # cloud_batch_result.save_json(future_file, indent=2)
            # saving ?

            with open(error_file, "w") as f:
                json.dump(errors, f, indent=2)

            raise RemoteBatch.SubmissionException(
                "One or more error(s) occured during submission, please see "
                "the following files for more information:\n"
                f"  - {os.path.join(cwd, future_file)}\n"
                f"  - {os.path.join(cwd, error_file)}\n"
            )

        else:
            # TODO: think about if we should automatically save successful submissions
            #       as well.
            pass

    def get_failed_tasks(self) -> "RemoteBatch":
        # offline:
        new_task_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if (task.task_id is not None) and (task._result_exists()):
                if task.task_result_ir.task_status in [
                    QuEraTaskStatusCode.Failed,
                    QuEraTaskStatusCode.Unaccepted,
                ]:
                    new_task_results[task_number] = task

        return RemoteBatch(new_task_results, name=self.name)

    def remove_failed_tasks(self) -> "RemoteBatch":
        # offline:
        new_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if (task.task_id is not None) and (task._result_exists()):
                if task.task_result_ir.task_status in [
                    QuEraTaskStatusCode.Failed,
                    QuEraTaskStatusCode.Unaccepted,
                ]:
                    continue
            new_results[task_number] = task

        return RemoteBatch(new_results, self.name)

    def get_finished_tasks(self) -> "RemoteBatch":
        # offline
        new_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if (task.task_id is not None) and (task._result_exists()):
                new_results[task_number] = task

        return RemoteBatch(new_results, self.name)

    def get_completed_tasks(self) -> "RemoteBatch":
        # offline
        new_results = OrderedDict()
        for task_number, task in self.tasks.items():
            if (task.task_id is not None) and (task._result_exists()):
                if task.task_result_ir.task_status == QuEraShotStatusCode.Completed:
                    new_results[task_number] = task

        return RemoteBatch(new_results, self.name)

    def report(self) -> "Report":
        ## this potentially can be specialize/disatch
        ## offline
        index = []
        data = []

        for task_number, task in self.tasks.items():
            ## fliter not existing results tasks:
            if (task.task_id is None) or (not task._result_exists()):
                continue

            ## filter has result but is not correctly completed.
            if not task.task_result_ir.status == QuEraTaskStatusCode.Completed:
                continue

            geometry = task.geometry
            perfect_sorting = "".join(map(str, geometry.filling))
            parallel_decoder = geometry.parallel_decoder

            if parallel_decoder:
                cluster_indices = parallel_decoder.get_cluster_indices()
            else:
                cluster_indices = {(0, 0): list(range(len(perfect_sorting)))}

            shot_iter = filter(
                lambda shot: shot.shot_status == QuEraShotStatusCode.Completed,
                task.result().shot_outputs,
            )

            for shot, (cluster_coordinate, cluster_index) in product(
                shot_iter, cluster_indices.items()
            ):
                pre_sequence = "".join(
                    map(
                        str,
                        (shot.pre_sequence[index] for index in cluster_index),
                    )
                )

                post_sequence = np.asarray(
                    [shot.post_sequence[index] for index in cluster_index],
                    dtype=np.int8,
                )

                pfc_sorting = "".join(
                    [perfect_sorting[index] for index in cluster_index]
                )

                key = (
                    task_number,
                    cluster_coordinate,
                    pfc_sorting,
                    pre_sequence,
                )

                index.append(key)
                data.append(post_sequence)

        index = pd.MultiIndex.from_tuples(
            index, names=["task_number", "cluster", "perfect_sorting", "pre_sequence"]
        )

        df = pd.DataFrame(data, index=index)
        df.sort_index(axis="index")

        return Report(df)
