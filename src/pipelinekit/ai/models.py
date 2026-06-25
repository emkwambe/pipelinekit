"""Diagnostic result models.

Every field maps to a required field in ``schemas/diagnostic.schema.json``.
``can_auto_fix`` is always False in Phase 4 (ADR-007, ADR-014); no code path
executes a ``RecommendedAction``.

See: SPEC-005.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RecommendedAction(BaseModel):
    """A single recommended action. Always requires human approval in Phase 4."""

    action: str
    command: Optional[str] = None
    risk_level: str = "low"  # low | medium | high
    reversible: bool = True
    requires_approval: bool = True


class DiagnosticResult(BaseModel):
    """Structured AI diagnosis — validated against diagnostic.schema.json.

    No additional fields without a schema update. ``confidence`` is constrained
    to [0.0, 1.0]; ``can_auto_fix`` is forced False by the engine in Phase 4.
    """

    status: str  # diagnosed | inconclusive | error
    finding_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[dict] = []
    recommended_actions: list[RecommendedAction] = []
    can_auto_fix: bool = False
    explanation: str = ""
    run_id: str = ""
    pipeline_name: str = ""

    @field_validator("confidence")
    @classmethod
    def confidence_must_be_valid(cls, v: float) -> float:
        """Confidence must lie within the closed interval [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v
