"""Tests for runtime result objects (SPEC-003)."""

from __future__ import annotations

from pipelinekit.runtime.result import PipelineResult, PipelineStatus, StepResult


def test_succeeded_true_on_success():
    """PipelineResult.succeeded() is True for a SUCCESS status."""
    result = PipelineResult("run-1", "demo", PipelineStatus.SUCCESS, 1.0)
    assert result.succeeded() is True
    assert result.failed() is False


def test_failed_true_on_failed():
    """PipelineResult.failed() is True for a FAILED status."""
    result = PipelineResult("run-1", "demo", PipelineStatus.FAILED, 1.0)
    assert result.failed() is True
    assert result.succeeded() is False


def test_step_result_stores_error_fields():
    """StepResult stores error_code and error_msg correctly."""
    step = StepResult(
        step="ingestion",
        status=PipelineStatus.FAILED,
        duration_s=2.5,
        error_code="PK-ADAPTER-002",
        error_msg="boom",
    )
    assert step.error_code == "PK-ADAPTER-002"
    assert step.error_msg == "boom"
    assert step.rows_processed == 0
