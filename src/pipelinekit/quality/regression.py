"""QM-9 — quality regression testing over historical scorecard snapshots.

Compares the most recent quality scorecard snapshot for a blueprint against the
average of the previous ``window`` snapshots and flags any component that has
gotten meaningfully *worse*. Fully deterministic — no AI, no warehouse — reading
only the ``qm_scorecard_snapshots`` baselines written by QM-8's scorecard
(``compute_blueprint_score``).

Regression types (see ADR-039):

* ``coverage_drop``      — coverage score fell by more than ``threshold`` points
* ``score_drop``         — composite score fell by more than ``threshold`` points
* ``drift_introduced``   — drift score fell (new schema drift appeared)
* ``ownership_lost``     — ownership score fell (owner removed)

See: SPEC-038, ADR-039.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from pipelinekit.state import db


@dataclass
class QualityRegression:
    """A single detected regression in one scorecard component."""

    blueprint_name: str
    regression_type: str  # coverage_drop | score_drop | drift_introduced | ...
    previous_value: float
    current_value: float
    drop_amount: float
    detail: str


@dataclass
class RegressionReport:
    """The regression outcome for one blueprint over a comparison window."""

    blueprint_name: str
    regressions: list[QualityRegression]
    is_regression: bool
    comparison_window: int
    generated_at: str


def _mean(values: list[float]) -> float:
    """Return the arithmetic mean, or 0.0 for an empty sequence."""
    return sum(values) / len(values) if values else 0.0


def check_regression(
    blueprint_name: str,
    db_path: str,
    window: int = 7,
    threshold: float = 5.0,
) -> RegressionReport:
    """Compare the latest scorecard snapshot against the previous ``window``.

    Reads up to ``window + 1`` most-recent snapshots (newest first). The newest
    is the latest state; the remaining (up to ``window``) form the baseline whose
    per-component averages the latest is compared against. Fewer than two
    snapshots means there is no baseline yet — a clean, non-regression report.

    A component regresses when it drops below ``baseline_avg - threshold`` for the
    magnitude checks (coverage, composite), or below ``baseline_avg`` at all for
    the presence checks (drift, ownership — any regression is meaningful).
    """
    generated_at = datetime.now(timezone.utc).isoformat()
    snapshots = db.get_scorecard_history(blueprint_name, db_path, limit=window + 1)

    if len(snapshots) < 2:
        return RegressionReport(
            blueprint_name=blueprint_name,
            regressions=[],
            is_regression=False,
            comparison_window=window,
            generated_at=generated_at,
        )

    latest = snapshots[0]
    baseline = snapshots[1:]

    baseline_coverage = _mean([s["coverage_score"] for s in baseline])
    baseline_composite = _mean([s["composite_score"] for s in baseline])
    baseline_drift = _mean([s["drift_score"] for s in baseline])
    baseline_ownership = _mean([s["ownership_score"] for s in baseline])

    regressions: list[QualityRegression] = []

    if latest["coverage_score"] < baseline_coverage - threshold:
        regressions.append(
            QualityRegression(
                blueprint_name=blueprint_name,
                regression_type="coverage_drop",
                previous_value=round(baseline_coverage, 2),
                current_value=round(latest["coverage_score"], 2),
                drop_amount=round(baseline_coverage - latest["coverage_score"], 2),
                detail=(
                    f"coverage {baseline_coverage:.1f} → "
                    f"{latest['coverage_score']:.1f} "
                    f"(threshold {threshold:g})"
                ),
            )
        )

    if latest["composite_score"] < baseline_composite - threshold:
        regressions.append(
            QualityRegression(
                blueprint_name=blueprint_name,
                regression_type="score_drop",
                previous_value=round(baseline_composite, 2),
                current_value=round(latest["composite_score"], 2),
                drop_amount=round(baseline_composite - latest["composite_score"], 2),
                detail=(
                    f"composite {baseline_composite:.1f} → "
                    f"{latest['composite_score']:.1f} "
                    f"(threshold {threshold:g})"
                ),
            )
        )

    if latest["drift_score"] < baseline_drift:
        regressions.append(
            QualityRegression(
                blueprint_name=blueprint_name,
                regression_type="drift_introduced",
                previous_value=round(baseline_drift, 2),
                current_value=round(latest["drift_score"], 2),
                drop_amount=round(baseline_drift - latest["drift_score"], 2),
                detail="new schema drift appeared since baseline",
            )
        )

    if latest["ownership_score"] < baseline_ownership:
        regressions.append(
            QualityRegression(
                blueprint_name=blueprint_name,
                regression_type="ownership_lost",
                previous_value=round(baseline_ownership, 2),
                current_value=round(latest["ownership_score"], 2),
                drop_amount=round(baseline_ownership - latest["ownership_score"], 2),
                detail="ownership was removed since baseline",
            )
        )

    return RegressionReport(
        blueprint_name=blueprint_name,
        regressions=regressions,
        is_regression=bool(regressions),
        comparison_window=window,
        generated_at=generated_at,
    )
