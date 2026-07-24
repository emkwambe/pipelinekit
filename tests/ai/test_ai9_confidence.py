"""Tests for AI-9 EMS-aware confidence recalibration (SPEC-039).

Deterministic, no AI, no state.db. ``EMSContext`` is constructed directly so each
adjustment rule can be exercised in isolation.
"""

from __future__ import annotations

import pytest
from pipelinekit.ai.confidence import (
    ConfidenceAdjustment,
    adjust_confidence,
    compute_ems_adjustment,
)
from pipelinekit.ai.ems_context import EMSContext


def _ctx(
    *,
    quality_score: float | None = None,
    quality_rating: str | None = None,
    slo_violations: list[dict] | None = None,
    schema_drift: list[dict] | None = None,
    has_data: bool = True,
) -> EMSContext:
    """Build an EMSContext with only the signals a test cares about."""
    return EMSContext(
        blueprint_name="test-bp",
        quality_score=quality_score,
        quality_rating=quality_rating,
        slo_violations=slo_violations or [],
        volume_anomalies=[],
        schema_drift=schema_drift or [],
        pending_notifications=[],
        has_data=has_data,
        summary="",
    )


def test_ai9_high_quality_score_boosts_confidence() -> None:
    """Quality score >= 80 (plus SLO compliance) raises confidence."""
    ctx = _ctx(quality_score=85.0, quality_rating="Good")

    result = adjust_confidence(0.82, ctx)

    assert isinstance(result, ConfidenceAdjustment)
    assert result.adjusted_confidence > result.base_confidence
    assert result.adjustment == pytest.approx(0.08)  # +0.05 quality, +0.03 SLO
    assert any("Quality score" in r for r in result.reasons)


def test_ai9_poor_quality_score_penalizes_confidence() -> None:
    """Quality score < 50 lowers confidence relative to the base."""
    ctx = _ctx(quality_score=32.0, quality_rating="Poor")

    result = adjust_confidence(0.82, ctx)

    assert result.adjusted_confidence < result.base_confidence
    assert any("Quality score" in r and "-0.05" in r for r in result.reasons)


def test_ai9_slo_violations_penalize_confidence() -> None:
    """Each SLO violation subtracts 0.03, capped at -0.10 total."""
    two = _ctx(slo_violations=[{"table": "a"}, {"table": "b"}])
    five = _ctx(slo_violations=[{"table": str(i)} for i in range(5)])

    adj_two, _ = compute_ems_adjustment(two)
    adj_five, _ = compute_ems_adjustment(five)

    assert adj_two == pytest.approx(-0.06)  # 2 * -0.03
    assert adj_five == pytest.approx(-0.10)  # capped, not -0.15


def test_ai9_schema_drift_penalizes_confidence() -> None:
    """Schema drift lowers confidence and is reported as a reason."""
    ctx = _ctx(schema_drift=[{"table": "charges", "drift_items": []}])

    result = adjust_confidence(0.82, ctx)

    assert result.adjusted_confidence < result.base_confidence
    assert any("schema drift" in r for r in result.reasons)


def test_ai9_all_slos_compliant_boosts_confidence() -> None:
    """Having EMS data with no SLO violations adds +0.03."""
    ctx = _ctx()  # has_data=True, no violations, no quality signal

    adjustment, reasons = compute_ems_adjustment(ctx)

    assert adjustment == pytest.approx(0.03)
    assert any("All SLOs compliant" in r for r in reasons)


def test_ai9_confidence_clamped_to_zero_minimum() -> None:
    """A very low base with heavy penalties never drops below 0.0."""
    ctx = _ctx(
        quality_score=32.0,
        quality_rating="Poor",
        slo_violations=[{"table": str(i)} for i in range(5)],
        schema_drift=[{"table": "charges", "drift_items": []}],
    )

    result = adjust_confidence(0.02, ctx)

    assert result.adjusted_confidence == 0.0


def test_ai9_confidence_clamped_to_one_maximum() -> None:
    """A very high base with boosts never exceeds 1.0."""
    ctx = _ctx(quality_score=90.0, quality_rating="Excellent")

    result = adjust_confidence(0.98, ctx)

    assert result.adjusted_confidence == 1.0


def test_ai9_no_ems_data_returns_unchanged_confidence() -> None:
    """has_data=False returns the base confidence unchanged, no adjustment."""
    ctx = _ctx(has_data=False)

    result = adjust_confidence(0.82, ctx)

    assert result.adjusted_confidence == 0.82
    assert result.adjustment == 0.0
    assert result.reasons == []
