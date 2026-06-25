"""Tests for diagnostic models (SPEC-005, diagnostic.schema.json)."""

from __future__ import annotations

import pytest
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction
from pydantic import ValidationError


def test_valid_result_has_required_schema_fields():
    """A DiagnosticResult carries the 5 schema-required fields."""
    result = DiagnosticResult(
        status="diagnosed",
        finding_type="contract_violation",
        confidence=0.9,
        evidence=[{"type": "error_code", "detail": "PK-CONTRACT-002"}],
        recommended_actions=[RecommendedAction(action="increase pool size")],
    )
    assert result.status == "diagnosed"
    assert result.finding_type == "contract_violation"
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.evidence, list)
    assert isinstance(result.recommended_actions, list)


def test_confidence_out_of_range_raises():
    """confidence outside [0.0, 1.0] raises ValidationError."""
    with pytest.raises(ValidationError):
        DiagnosticResult(status="diagnosed", finding_type="unknown", confidence=1.5)


def test_can_auto_fix_defaults_false():
    """can_auto_fix defaults to False (Phase 4 invariant)."""
    result = DiagnosticResult(
        status="diagnosed", finding_type="unknown", confidence=0.5
    )
    assert result.can_auto_fix is False


def test_recommended_action_requires_approval_default_true():
    """RecommendedAction.requires_approval defaults to True."""
    action = RecommendedAction(action="do the thing")
    assert action.requires_approval is True
    assert action.reversible is True
    assert action.risk_level == "low"
