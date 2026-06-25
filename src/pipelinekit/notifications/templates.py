"""Message templates that turn pipeline outcomes into notifications.

Each builder returns a :class:`Notification` with ``recipient`` left blank — the
dispatcher fills it per configured recipient. Subjects and messages are
human-readable; ``evidence`` is structured for Phase 4 AI diagnostics (SPEC-008).
"""

from __future__ import annotations

from pipelinekit.contracts.models import ContractResult
from pipelinekit.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationSeverity,
)
from pipelinekit.runtime.result import PipelineResult, PipelineStatus

_PREFIX = "[PipelineKit]"


def _failed_steps(result: PipelineResult) -> list[dict]:
    return [
        {
            "step": s.step,
            "error_code": s.error_code,
            "error_msg": s.error_msg,
        }
        for s in result.steps
        if s.status == PipelineStatus.FAILED
    ]


def pipeline_failed_notification(result: PipelineResult) -> Notification:
    """Build the notification for a failed pipeline run."""
    failed = _failed_steps(result)
    step_lines = "\n".join(
        f"  - {s['step']}: {s['error_code']} {s['error_msg']}" for s in failed
    )
    message = (
        f"Pipeline:   {result.pipeline_name}\n"
        f"Run ID:     {result.run_id}\n"
        f"Status:     FAILED\n"
        f"Error:      {result.error_code} — {result.error_msg}\n"
        f"Duration:   {result.duration_s:.1f}s\n\n"
        f"Failed steps:\n{step_lines or '  (none recorded)'}\n\n"
        "Next steps:\n"
        "  Run 'pipelinekit doctor' to diagnose.\n"
        "  Run 'pipelinekit status' to see run history."
    )
    return Notification(
        channel=NotificationChannel.EMAIL,
        recipient="",
        severity=NotificationSeverity.ERROR,
        subject=f"{_PREFIX} Pipeline failed — {result.pipeline_name}",
        message=message,
        evidence={
            "run_id": result.run_id,
            "status": result.status.value,
            "error_code": result.error_code,
            "error_msg": result.error_msg,
            "failed_steps": failed,
            "duration_s": result.duration_s,
        },
        pipeline_name=result.pipeline_name,
        run_id=result.run_id,
        error_code=result.error_code,
    )


def contract_violated_notification(
    result: PipelineResult, contract_results: list[ContractResult]
) -> Notification:
    """Build the notification for one or more contract violations."""
    violated = [cr for cr in contract_results if not cr.passed()]
    violation_lines = []
    evidence_violations = []
    for cr in violated:
        for v in cr.violations:
            violation_lines.append(f"  {cr.table}: [{v.error_code}] {v.message}")
            evidence_violations.append(
                {
                    "table": cr.table,
                    "error_code": v.error_code,
                    "violation_type": v.violation_type.value,
                    "column": v.column,
                    "evidence": v.evidence,
                }
            )
    total = len(evidence_violations)
    message = (
        f"Pipeline:   {result.pipeline_name}\n"
        f"Run ID:     {result.run_id}\n"
        f"Tables:     {total} violation(s) across {len(violated)} table(s)\n\n"
        f"Violations:\n{chr(10).join(violation_lines) or '  (none)'}\n\n"
        "Next steps:\n"
        "  Run 'pipelinekit validate --contracts' to recheck."
    )
    return Notification(
        channel=NotificationChannel.EMAIL,
        recipient="",
        severity=NotificationSeverity.WARNING,
        subject=f"{_PREFIX} Contract violations — {result.pipeline_name}",
        message=message,
        evidence={
            "run_id": result.run_id,
            "violation_count": total,
            "table_count": len(violated),
            "violations": evidence_violations,
        },
        pipeline_name=result.pipeline_name,
        run_id=result.run_id,
    )


def pipeline_succeeded_notification(result: PipelineResult) -> Notification:
    """Build the (opt-in) notification for a successful pipeline run."""
    rows = sum(s.rows_processed for s in result.steps)
    message = (
        f"Pipeline:   {result.pipeline_name}\n"
        f"Run ID:     {result.run_id}\n"
        f"Status:     SUCCESS\n"
        f"Duration:   {result.duration_s:.1f}s\n"
        f"Rows:       {rows:,}"
    )
    return Notification(
        channel=NotificationChannel.EMAIL,
        recipient="",
        severity=NotificationSeverity.INFO,
        subject=f"{_PREFIX} Pipeline succeeded — {result.pipeline_name}",
        message=message,
        evidence={
            "run_id": result.run_id,
            "status": result.status.value,
            "rows_processed": rows,
            "duration_s": result.duration_s,
        },
        pipeline_name=result.pipeline_name,
        run_id=result.run_id,
    )
