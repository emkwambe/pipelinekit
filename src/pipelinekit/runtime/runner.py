"""The pipeline runtime orchestrator.

``PipelineRunner`` coordinates ingestion → transformation → quality through the
``AdapterFactory``, records every execution in the state store, and returns a
structured ``PipelineResult``. It never calls providers directly, never prints,
and never calls AI. The run record is *always* updated — even on failure — via
a ``try/finally`` (SPEC-003).
"""

from __future__ import annotations

import time
import uuid

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.adapters.factory import AdapterFactory
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import PipelineKitError
from pipelinekit.notifications.dispatcher import NotificationDispatcher
from pipelinekit.runtime.executor import execute_step, validate_step
from pipelinekit.runtime.result import PipelineResult, PipelineStatus, StepResult
from pipelinekit.state import db


def _new_run_id() -> str:
    """Generate a run id of the form ``run-<8 hex chars>`` (SPEC-007)."""
    return f"run-{uuid.uuid4().hex[:8]}"


def _aggregate_run_status(steps: list[StepResult]) -> PipelineStatus:
    """Reduce per-step outcomes to an overall run status."""
    if not steps:
        return PipelineStatus.SUCCESS
    failed = [s for s in steps if s.status == PipelineStatus.FAILED]
    if not failed:
        return PipelineStatus.SUCCESS
    succeeded = [s for s in steps if s.status == PipelineStatus.SUCCESS]
    if not succeeded:
        return PipelineStatus.FAILED
    return PipelineStatus.PARTIAL


def _aggregate_validation_status(steps: list[StepResult]) -> PipelineStatus:
    """Reduce per-step validation outcomes to an overall status."""
    if all(s.status == PipelineStatus.VALID for s in steps):
        return PipelineStatus.VALID
    return PipelineStatus.INVALID


class PipelineRunner:
    """Executes and validates a pipeline described by ``PipelineConfig``."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    def _adapters(self) -> list[tuple[str, BaseAdapter]]:
        """Build the ordered, enabled (step_name, adapter) list via the factory."""
        candidates = [
            ("ingestion", AdapterFactory.create_ingestion(self.config)),
            ("transformation", AdapterFactory.create_transformation(self.config)),
            ("quality", AdapterFactory.create_quality(self.config)),
        ]
        return [(name, a) for name, a in candidates if a is not None]

    def run(self) -> PipelineResult:
        """Execute the full pipeline, always recording the run in state."""
        run_id = _new_run_id()
        name = self.config.pipeline.name
        db.insert_run(run_id, name)

        steps: list[StepResult] = []
        status = PipelineStatus.FAILED
        error_code: str | None = "PK-RUNTIME-001"
        error_msg: str | None = None
        start = time.perf_counter()
        try:
            for step_name, adapter in self._adapters():
                steps.append(execute_step(step_name, adapter))
            status = _aggregate_run_status(steps)
            if status == PipelineStatus.SUCCESS:
                error_code, error_msg = None, None
            else:
                first_failed = next(
                    (s for s in steps if s.status == PipelineStatus.FAILED), None
                )
                if first_failed is not None:
                    error_code = first_failed.error_code
                    error_msg = first_failed.error_msg
        except PipelineKitError as exc:
            status, error_code, error_msg = (
                PipelineStatus.FAILED,
                exc.code,
                exc.message,
            )
        except Exception as exc:
            status, error_code, error_msg = (
                PipelineStatus.FAILED,
                "PK-RUNTIME-001",
                str(exc),
            )
        finally:
            # 1. Always update state first — this must never be skipped.
            duration = time.perf_counter() - start
            db.update_run(run_id, status.value, duration, error_code, error_msg)
            result = PipelineResult(
                run_id=run_id,
                pipeline_name=name,
                status=status,
                duration_s=duration,
                steps=steps,
                error_code=error_code,
                error_msg=error_msg,
            )
            # 2. Then dispatch notifications — failure must not corrupt state.
            if self.config.notifications.enabled:
                try:
                    dispatcher = NotificationDispatcher(self.config.notifications)
                    dispatcher.initialize()
                    dispatcher.notify_pipeline_result(result, None)
                except Exception:
                    pass  # Notification failure is never propagated (SPEC-008).

        return result

    def validate(self) -> PipelineResult:
        """Validate config and adapter connectivity without executing."""
        run_id = _new_run_id()
        name = self.config.pipeline.name
        steps: list[StepResult] = []
        start = time.perf_counter()
        try:
            for step_name, adapter in self._adapters():
                steps.append(validate_step(step_name, adapter))
            status = _aggregate_validation_status(steps)
            error_code: str | None = None
            error_msg: str | None = None
            if status == PipelineStatus.INVALID:
                first_invalid = next(
                    (s for s in steps if s.status == PipelineStatus.INVALID), None
                )
                if first_invalid is not None:
                    error_code = first_invalid.error_code
                    error_msg = first_invalid.error_msg
        except PipelineKitError as exc:
            status, error_code, error_msg = (
                PipelineStatus.INVALID,
                exc.code,
                exc.message,
            )
        except Exception as exc:
            status, error_code, error_msg = (
                PipelineStatus.INVALID,
                "PK-RUNTIME-002",
                str(exc),
            )
        duration = time.perf_counter() - start

        return PipelineResult(
            run_id=run_id,
            pipeline_name=name,
            status=status,
            duration_s=duration,
            steps=steps,
            error_code=error_code,
            error_msg=error_msg,
        )
