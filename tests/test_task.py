import os
import glob

import pytest

from bloqade.analog.task.batch import RemoteBatch
from bloqade.analog.atom_arrangement import Chain


def test_batch_error(*args):
    with pytest.raises(RemoteBatch.SubmissionException):
        (
            Chain(5, lattice_spacing=6.1)
            .rydberg.detuning.uniform.linear(-10, 10, 3.0)
            .quera.mock(submission_error=True)
            .run_async(100)
        )

    error_files = glob.glob("partial-batch-errors-*")
    batch_files = glob.glob("partial-batch-future-*")

    for error_file, batch_file in zip(error_files, batch_files):
        os.remove(error_file)
        os.remove(batch_file)

    assert len(error_files) == 1
    assert len(batch_files) == 1


def test_batch_warn():
    with pytest.warns():
        (
            Chain(5, lattice_spacing=6.1)
            .rydberg.detuning.uniform.linear(-10, 10, 3.0)
            .quera.mock(submission_error=True)
            .run_async(100, ignore_submission_error=True)
        )

    error_files = glob.glob("partial-batch-errors-*")
    batch_files = glob.glob("partial-batch-future-*")

    for error_file, batch_file in zip(error_files, batch_files):
        os.remove(error_file)
        os.remove(batch_file)

    assert len(error_files) == 1
    assert len(batch_files) == 1


def test_batch_get_and_remove_tasks_with_none_task_result_ir():
    from collections import OrderedDict
    from bloqade.analog.submission.ir.task_results import (
        QuEraTaskResults,
        QuEraTaskStatusCode,
    )

    class MockTask:
        def __init__(self, status):
            self.task_result_ir = (
                QuEraTaskResults(task_status=status) if status else None
            )

    tasks = OrderedDict(
        [
            (0, MockTask(QuEraTaskStatusCode.Completed)),
            (1, MockTask(None)),
            (2, MockTask(QuEraTaskStatusCode.Failed)),
        ]
    )
    batch = RemoteBatch(None, tasks)

    # get_tasks should include only task 0, ignoring None result without AttributeError
    completed_batch = batch.get_tasks("Completed")
    assert list(completed_batch.tasks.keys()) == [0]

    # remove_tasks should filter out task 2 and keep task 0 and task 1
    non_failed_batch = batch.remove_tasks("Failed")
    assert list(non_failed_batch.tasks.keys()) == [0, 1]
