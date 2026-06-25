"""Structured result objects produced by the runtime.

These dataclasses are the contract between the runtime and the CLI. The CLI
renders them; the runtime produces them. They are also evidence for Phase 4 AI
diagnostics, so every field is human-readable and explicit (ADR-010).

See: SPEC-003.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PipelineStatus(str, Enum):
    """Outcome of a pipeline run, a single step, or a validation pass."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    VALID = "valid"
    INVALID = "invalid"


@dataclass
class StepResult:
    """Result of a single execution step (ingestion, transformation, quality)."""

    step: str
    status: PipelineStatus
    duration_s: float
    rows_processed: int = 0
    error_code: str | None = None
    error_msg: str | None = None


@dataclass
class PipelineResult:
    """Aggregate result of a full pipeline run or validation pass."""

    run_id: str
    pipeline_name: str
    status: PipelineStatus
    duration_s: float
    steps: list[StepResult] = field(default_factory=list)
    error_code: str | None = None
    error_msg: str | None = None

    def succeeded(self) -> bool:
        """Return True when the pipeline completed successfully."""
        return self.status == PipelineStatus.SUCCESS

    def failed(self) -> bool:
        """Return True when the pipeline failed outright."""
        return self.status == PipelineStatus.FAILED
