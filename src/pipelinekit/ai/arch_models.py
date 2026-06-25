"""Architecture reasoning models (SPEC-011, architecture.schema.json).

These models are the Phase 5 parallel of the Phase 4 ``DiagnosticResult``.
``can_auto_apply`` is always False in Phase 5 (ADR-015, ADR-007); no code path
applies an ``ArchitectureRecommendation``. ``requires_approval`` on a
recommendation is always True in Phase 5.

See: SPEC-011, ADR-015.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ArchitectureTradeoff(BaseModel):
    """One dimension of a proposed architectural change."""

    dimension: str  # cost | reliability | complexity | vendor_lock | maintainability
    current: str
    proposed: str
    direction: str  # better | worse | neutral
    evidence: str


class ADRComplianceCheck(BaseModel):
    """A single ADR compliance verdict. Advisory — never a definitive ruling."""

    adr_id: str  # "ADR-004", "ADR-007", etc.
    compliant: bool
    note: str = ""


class ArchitectureRecommendation(BaseModel):
    """A recommended architectural change. Always requires human approval."""

    action: str
    tool_from: Optional[str] = None
    tool_to: Optional[str] = None
    rationale: str = ""
    effort: str = "medium"  # low | medium | high
    reversible: bool = True
    requires_approval: bool = True  # always True in Phase 5


class ArchitectureResult(BaseModel):
    """Structured architectural reasoning — validated against the schema.

    ``confidence`` is constrained to [0.0, 1.0]; ``can_auto_apply`` is forced
    False by the engine in Phase 5 (ADR-015, Smell 13).
    """

    reasoning_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    current_state: dict = {}
    recommendation: ArchitectureRecommendation
    tradeoffs: list[ArchitectureTradeoff] = []
    evidence: list[dict] = []
    adr_compliance: list[ADRComplianceCheck] = []
    can_auto_apply: bool = False  # always False in Phase 5
    estimated_impact: dict = {}
    explanation: str = ""

    @field_validator("confidence")
    @classmethod
    def confidence_must_be_valid(cls, v: float) -> float:
        """Confidence must lie within the closed interval [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v
