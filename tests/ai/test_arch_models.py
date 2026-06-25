"""Tests for architecture models (SPEC-011, architecture.schema.json)."""

from __future__ import annotations

import pytest
from pipelinekit.ai.arch_models import (
    ADRComplianceCheck,
    ArchitectureRecommendation,
    ArchitectureResult,
    ArchitectureTradeoff,
)
from pydantic import ValidationError


def _result(**overrides) -> ArchitectureResult:
    data = {
        "reasoning_type": "tool_selection",
        "confidence": 0.8,
        "current_state": {"description": "dbt on duckdb"},
        "recommendation": ArchitectureRecommendation(
            action="switch dbt to sqlmesh", rationale="fewer incremental failures"
        ),
        "tradeoffs": [
            ArchitectureTradeoff(
                dimension="reliability",
                current="dbt",
                proposed="sqlmesh",
                direction="better",
                evidence="3 failed incremental runs",
            )
        ],
        "evidence": [{"type": "run", "detail": "PK-ADAPTER-002"}],
        "adr_compliance": [
            ADRComplianceCheck(adr_id="ADR-005", compliant=True, note="Apache 2.0")
        ],
    }
    data.update(overrides)
    return ArchitectureResult(**data)


def test_valid_result_has_required_schema_fields():
    """An ArchitectureResult carries the 7 schema-required fields."""
    result = _result()
    assert result.reasoning_type == "tool_selection"
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.current_state, dict)
    assert isinstance(result.recommendation, ArchitectureRecommendation)
    assert isinstance(result.tradeoffs, list)
    assert isinstance(result.evidence, list)
    assert isinstance(result.adr_compliance, list)


def test_can_auto_apply_defaults_false():
    """can_auto_apply defaults to False (Phase 5 invariant)."""
    assert _result().can_auto_apply is False


def test_confidence_out_of_range_raises():
    """confidence outside [0.0, 1.0] raises ValidationError."""
    with pytest.raises(ValidationError):
        _result(confidence=1.5)


def test_recommendation_requires_approval_default_true():
    """ArchitectureRecommendation.requires_approval defaults to True."""
    rec = ArchitectureRecommendation(action="do the thing")
    assert rec.requires_approval is True
    assert rec.reversible is True
    assert rec.effort == "medium"
