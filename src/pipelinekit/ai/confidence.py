"""AI-15 — EMS-Aware Confidence Recalibration (SPEC-039, ADR-040, ADR-043).

Recalibrates the base AI confidence score (AI-4) using the operational signals
already assembled by AI-13 (``EMSContext``). A proposal targeting a healthy
environment (high quality score, no SLO violations) earns a small confidence
boost; one targeting an unreliable environment (Poor quality, active drift, SLO
violations) earns a penalty. The base score is never recomputed — the adjustment
is additive and the final value is clamped to ``[0.0, 1.0]``.

Fully deterministic and defensive: ``has_data=False`` yields no adjustment, and
any error degrades to the unchanged base confidence. AI-15 never raises.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipelinekit.ai.ems_context import EMSContext

# Signed adjustments applied per EMS signal (ADR-040).
ADJUSTMENT_RULES = {
    "quality_score_good_boost": +0.05,  # score >= 80 (Good/Excellent)
    "quality_score_poor_penalty": -0.05,  # score < 50 (Poor)
    "slo_violation_penalty": -0.03,  # per violation, capped at -0.10 total
    "schema_drift_penalty": -0.05,  # any DRIFTED tables
    "no_owner_penalty": -0.02,  # no owner assigned (see note below)
    "all_slos_compliant_boost": +0.03,  # has data, no SLO violations
}

# Bounds on the *total* adjustment before it is applied to the base score.
MAX_BOOST = +0.10
MAX_PENALTY = -0.15
# Per-signal cap for SLO violations regardless of how many there are.
SLO_PENALTY_CAP = -0.10


@dataclass
class ConfidenceAdjustment:
    """The outcome of recalibrating one confidence score with EMS signals."""

    base_confidence: float
    adjusted_confidence: float
    adjustment: float
    reasons: list[str]  # human-readable explanation of each applied adjustment


def compute_ems_adjustment(ems_ctx: EMSContext) -> tuple[float, list[str]]:
    """Compute the total confidence adjustment from EMS signals.

    Returns ``(total_adjustment, reasons)``. Returns ``(0.0, [])`` when the
    context carries no data. The total is clamped to ``[MAX_PENALTY, MAX_BOOST]``.

    Note: ``no_owner_penalty`` is defined by ADR-040 but ``EMSContext`` exposes no
    direct ownership signal (ownership already contributes to the QM-8 quality
    score), so it is not applied here — see the sprint report deviation.
    """
    if not ems_ctx.has_data:
        return 0.0, []

    adjustment = 0.0
    reasons: list[str] = []

    # Quality score signal (QM-8).
    if ems_ctx.quality_score is not None:
        if ems_ctx.quality_score >= 80:
            boost = ADJUSTMENT_RULES["quality_score_good_boost"]
            adjustment += boost
            reasons.append(
                f"Quality score {ems_ctx.quality_score:.0f}/100 "
                f"({ems_ctx.quality_rating}) -> {boost:+.2f}"
            )
        elif ems_ctx.quality_score < 50:
            penalty = ADJUSTMENT_RULES["quality_score_poor_penalty"]
            adjustment += penalty
            reasons.append(
                f"Quality score {ems_ctx.quality_score:.0f}/100 "
                f"({ems_ctx.quality_rating}) -> {penalty:+.2f}"
            )

    # SLO violations (OM-4): penalize per violation, capped; else reward compliance.
    if ems_ctx.slo_violations:
        count = len(ems_ctx.slo_violations)
        slo_penalty = max(
            ADJUSTMENT_RULES["slo_violation_penalty"] * count, SLO_PENALTY_CAP
        )
        adjustment += slo_penalty
        reasons.append(f"{count} SLO violation(s) -> {slo_penalty:+.2f}")
    else:
        boost = ADJUSTMENT_RULES["all_slos_compliant_boost"]
        adjustment += boost
        reasons.append(f"All SLOs compliant -> {boost:+.2f}")

    # Schema drift (QM-7).
    if ems_ctx.schema_drift:
        penalty = ADJUSTMENT_RULES["schema_drift_penalty"]
        adjustment += penalty
        reasons.append(
            f"{len(ems_ctx.schema_drift)} table(s) with schema drift "
            f"-> {penalty:+.2f}"
        )

    # Clamp the total adjustment to its bounds.
    adjustment = max(MAX_PENALTY, min(MAX_BOOST, adjustment))
    return adjustment, reasons


def adjust_confidence(
    base_confidence: float, ems_ctx: EMSContext
) -> ConfidenceAdjustment:
    """Apply the EMS adjustment to ``base_confidence``, clamped to ``[0, 1]``.

    Always returns a valid ``ConfidenceAdjustment`` and never raises — any error
    degrades to the unchanged base confidence.
    """
    try:
        adjustment, reasons = compute_ems_adjustment(ems_ctx)
        adjusted = max(0.0, min(1.0, base_confidence + adjustment))
        return ConfidenceAdjustment(
            base_confidence=base_confidence,
            adjusted_confidence=adjusted,
            adjustment=adjustment,
            reasons=reasons,
        )
    except Exception:
        return ConfidenceAdjustment(
            base_confidence=base_confidence,
            adjusted_confidence=base_confidence,
            adjustment=0.0,
            reasons=["EMS adjustment unavailable"],
        )
