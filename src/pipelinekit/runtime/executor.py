"""Step execution helpers used by :class:`PipelineRunner`.

These functions wrap a single adapter call so that no provider exception ever
escapes the runtime: everything is mapped to a structured ``StepResult`` with a
PK error code. Adapters already map their own provider errors; this is the
final safety net (SPEC-003: "All exceptions caught and mapped to PK codes").
"""

from __future__ import annotations

import time

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.core.errors import PipelineKitError
from pipelinekit.runtime.result import PipelineStatus, StepResult


def execute_step(step: str, adapter: BaseAdapter) -> StepResult:
    """Run one adapter's ``execute()``, never raising.

    Returns the adapter's ``StepResult`` on success, or a FAILED ``StepResult``
    carrying a PK error code if the adapter raised.
    """
    start = time.perf_counter()
    try:
        return adapter.execute()
    except PipelineKitError as exc:
        return StepResult(
            step,
            PipelineStatus.FAILED,
            time.perf_counter() - start,
            error_code=exc.code,
            error_msg=exc.message,
        )
    except Exception as exc:
        return StepResult(
            step,
            PipelineStatus.FAILED,
            time.perf_counter() - start,
            error_code="PK-RUNTIME-001",
            error_msg=str(exc),
        )


def validate_step(step: str, adapter: BaseAdapter) -> StepResult:
    """Run one adapter's ``validate()``, never raising.

    Returns the adapter's ``StepResult`` (status VALID or INVALID), or an
    INVALID ``StepResult`` with a PK error code if the adapter raised.
    """
    start = time.perf_counter()
    try:
        return adapter.validate()
    except PipelineKitError as exc:
        return StepResult(
            step,
            PipelineStatus.INVALID,
            time.perf_counter() - start,
            error_code=exc.code,
            error_msg=exc.message,
        )
    except Exception as exc:
        return StepResult(
            step,
            PipelineStatus.INVALID,
            time.perf_counter() - start,
            error_code="PK-ADAPTER-001",
            error_msg=str(exc),
        )
