"""Structured error hierarchy for PipelineKit.

Every error carries a stable PK error code (``PK-[AREA]-[NUMBER]``) so that
failures are deterministic, scriptable, and machine-readable. The CLI renders
these codes; it never surfaces raw stack traces to the user.

See: docs/reference/Error-Codes.md, SPEC-002, SPEC-007.
"""

from __future__ import annotations


class PipelineKitError(Exception):
    """Base class for all PipelineKit errors.

    Args:
        code: Stable error code, e.g. ``PK-CONFIG-001``.
        message: Human-readable description of the failure.
        context: Optional structured detail (field names, paths, sub-errors).
    """

    def __init__(self, code: str, message: str, context: dict | None = None) -> None:
        self.code = code
        self.message = message
        self.context = context or {}
        super().__init__(f"[{code}] {message}")


class ConfigurationError(PipelineKitError):
    """Raised when ``pipelinekit.yaml`` is missing, malformed, or invalid."""


class StateError(PipelineKitError):
    """Raised when the local state store cannot be opened or written."""


class RuntimeError(
    PipelineKitError
):  # noqa: A001 — domain error, shadows builtin by design
    """Raised when pipeline execution fails (Phase 2)."""


class ContractError(PipelineKitError):
    """Raised when a data contract is violated (Phase 2+)."""


class BlueprintError(PipelineKitError):
    """Raised when a blueprint is missing, invalid, or cannot be executed."""


class DiagnosticsError(PipelineKitError):
    """Raised when evidence collection or the diagnostics engine fails."""


class LLMError(PipelineKitError):
    """Raised when an AI provider is unavailable or returns invalid output."""


class ArchitectureError(PipelineKitError):
    """Raised when architecture context collection or reasoning fails."""


class HealthError(PipelineKitError):
    """Raised when a health check cannot run (tooling unavailable or failed)."""
