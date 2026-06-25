"""Tests for NotificationDispatcher (SPEC-008). No real delivery — mocked."""

from __future__ import annotations

from unittest.mock import patch

from pipelinekit.config.schema import NotificationsSection
from pipelinekit.contracts.models import (
    ContractResult,
    ContractViolation,
    ViolationType,
)
from pipelinekit.notifications.dispatcher import NotificationDispatcher
from pipelinekit.notifications.models import NotificationChannel, NotificationResult
from pipelinekit.runtime.result import PipelineResult, PipelineStatus, StepResult


def _config(
    enabled: bool = True, notify_on: list[str] | None = None
) -> NotificationsSection:
    return NotificationsSection(
        enabled=enabled,
        provider="resend",
        from_address="pipelinekit@example.com",
        recipients=["data-team@example.com"],
        notify_on=notify_on or ["pipeline_failed", "contract_violated"],
    )


def _failed_result() -> PipelineResult:
    return PipelineResult(
        run_id="run-1",
        pipeline_name="demo",
        status=PipelineStatus.FAILED,
        duration_s=1.0,
        steps=[
            StepResult(
                "ingestion",
                PipelineStatus.FAILED,
                1.0,
                error_code="PK-ADAPTER-001",
                error_msg="unreachable",
            )
        ],
        error_code="PK-ADAPTER-001",
        error_msg="unreachable",
    )


def _ok_result() -> PipelineResult:
    return PipelineResult(
        run_id="run-2",
        pipeline_name="demo",
        status=PipelineStatus.SUCCESS,
        duration_s=1.0,
        steps=[StepResult("ingestion", PipelineStatus.SUCCESS, 1.0, rows_processed=5)],
    )


def test_dispatch_never_raises_on_adapter_failure():
    """dispatch() returns a result even if the adapter blows up."""
    dispatcher = NotificationDispatcher(_config())
    dispatcher.initialize()
    with patch.object(dispatcher._adapter, "send", side_effect=Exception("boom")):
        from pipelinekit.notifications.templates import pipeline_failed_notification

        result = dispatcher.dispatch(pipeline_failed_notification(_failed_result()))
    assert isinstance(result, NotificationResult)
    assert result.sent is False
    assert "PK-NOTIFY-002" in (result.error or "")


def test_notify_sends_on_failed_result():
    """notify_pipeline_result() dispatches on a FAILED pipeline."""
    dispatcher = NotificationDispatcher(_config())
    dispatcher.initialize()
    sent = NotificationResult(
        sent=True, channel=NotificationChannel.EMAIL, recipient="data-team@example.com"
    )
    with patch.object(dispatcher._adapter, "send", return_value=sent) as mock_send:
        results = dispatcher.notify_pipeline_result(_failed_result())
    assert len(results) == 1
    assert results[0].sent is True
    mock_send.assert_called_once()


def test_notify_does_nothing_when_disabled():
    """notify_pipeline_result() sends nothing when notifications are disabled."""
    dispatcher = NotificationDispatcher(_config(enabled=False))
    dispatcher.initialize()
    results = dispatcher.notify_pipeline_result(_failed_result())
    assert results == []


def test_notify_sends_contract_violation():
    """notify_pipeline_result() dispatches a contract-violation notification."""
    dispatcher = NotificationDispatcher(_config(notify_on=["contract_violated"]))
    dispatcher.initialize()
    violation = ContractViolation(
        table="orders",
        violation_type=ViolationType.FRESHNESS,
        column="updated_at",
        error_code="PK-CONTRACT-002",
        message="data is 18h old (max: 12h)",
        evidence={"actual_age_hours": 18},
    )
    contract_results = [
        ContractResult(
            table="orders",
            status="violated",
            violations=[violation],
            checked_at="2026-06-25T00:00:00Z",
        )
    ]
    sent = NotificationResult(
        sent=True, channel=NotificationChannel.EMAIL, recipient="data-team@example.com"
    )
    with patch.object(dispatcher._adapter, "send", return_value=sent) as mock_send:
        results = dispatcher.notify_pipeline_result(_ok_result(), contract_results)
    assert len(results) == 1
    mock_send.assert_called_once()
    notification = mock_send.call_args.args[0]
    assert "Contract violations" in notification.subject
