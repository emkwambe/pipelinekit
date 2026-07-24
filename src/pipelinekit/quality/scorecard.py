"""QM-8 — composite quality scorecard aggregating all quality signals (SPEC-030).

Combines four existing signals into a single 0-100 score per blueprint:

* coverage (40%) — dbt test coverage (QM-4 ``compute_blueprint_coverage``)
* volume   (30%) — volume anomaly status (QM-6 ``check_volume_anomalies``)
* drift    (20%) — schema drift status (QM-7 ``check_blueprint_drift``)
* ownership(10%) — owner assigned (GM-1 ``get_owner``)

Read-only and deterministic — no AI, no new ``state.db`` tables. Every signal is
gathered defensively: any failure or missing data yields a component score of 0
(volume/drift use 50 when there is simply no baseline yet). QM-8 never crashes.

See: SPEC-030, ADR-031.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pipelinekit.governance.ownership import get_owner
from pipelinekit.quality.anomaly import check_volume_anomalies, get_row_count_history
from pipelinekit.quality.coverage import compute_blueprint_coverage
from pipelinekit.quality.drift import check_blueprint_drift
from pipelinekit.state import db

WEIGHTS = {"coverage": 0.40, "volume": 0.30, "drift": 0.20, "ownership": 0.10}
RATINGS = [(90, "Excellent"), (75, "Good"), (50, "Fair"), (0, "Poor")]

_CHECK = "✓"
_WARN = "⚠"
_DASH = "—"


@dataclass
class ComponentScore:
    """One weighted signal contributing to a blueprint's composite score."""

    name: str  # coverage | volume | drift | ownership
    score: float  # 0-100
    status: str  # display value, e.g. "82.6%", "OK", "CLEAN", "Set"
    symbol: str  # ✓ | ⚠ | —


@dataclass
class BlueprintScore:
    """A blueprint's composite quality score and its component breakdown."""

    blueprint_name: str
    composite_score: float
    rating: str  # Excellent | Good | Fair | Poor
    components: list[ComponentScore]


@dataclass
class ScorecardReport:
    """Aggregate scorecard across all installed blueprints."""

    blueprints: list[BlueprintScore]
    average_score: float
    average_rating: str
    generated_at: str


def get_rating(score: float) -> str:
    """Return the rating label for a score against ``RATINGS`` thresholds."""
    for threshold, label in RATINGS:
        if score >= threshold:
            return label
    return "Poor"


def _coverage_component(blueprint_name: str, blueprint_dir: str) -> ComponentScore:
    """dbt coverage percentage as a 0-100 component (QM-4)."""
    try:
        coverage = compute_blueprint_coverage(blueprint_name, blueprint_dir)
        score = float(coverage.blueprint_coverage_pct)
        symbol = _CHECK if score >= 50 else _WARN
        return ComponentScore("coverage", score, f"{score:.1f}%", symbol)
    except Exception:
        return ComponentScore("coverage", 0.0, "0.0%", _WARN)


def _volume_component(blueprint_name: str, db_path: str) -> ComponentScore:
    """Volume anomaly status as a 0-100 component (QM-6).

    No recorded row counts → 50 (ESTABLISHING); any anomaly → 0; otherwise 100.
    """
    try:
        tables = db.get_all_tables_for_blueprint(blueprint_name, db_path)
        if not tables:
            return ComponentScore("volume", 50.0, "ESTABLISHING", _DASH)
        current: dict[str, int] = {}
        for table in tables:
            history = get_row_count_history(blueprint_name, table, db_path, limit=1)
            if history:
                current[table] = history[0].row_count
        anomalies = check_volume_anomalies(blueprint_name, current, db_path)
        if any(a.is_anomaly for a in anomalies):
            return ComponentScore("volume", 0.0, "ANOMALY", _WARN)
        return ComponentScore("volume", 100.0, "OK", _CHECK)
    except Exception:
        return ComponentScore("volume", 0.0, "N/A", _DASH)


def _drift_component(
    blueprint_name: str, blueprint_dir: str, db_path: str
) -> ComponentScore:
    """Schema drift status as a 0-100 component (QM-7).

    No models / all NO_BASELINE → 50; any DRIFTED → 0; otherwise 100.
    """
    try:
        results = check_blueprint_drift(blueprint_name, blueprint_dir, db_path)
        if not results:
            return ComponentScore("drift", 50.0, "NO_BASELINE", _DASH)
        if any(r.status == "DRIFTED" for r in results):
            return ComponentScore("drift", 0.0, "DRIFTED", _WARN)
        if all(r.status == "NO_BASELINE" for r in results):
            return ComponentScore("drift", 50.0, "NO_BASELINE", _DASH)
        return ComponentScore("drift", 100.0, "CLEAN", _CHECK)
    except Exception:
        return ComponentScore("drift", 0.0, "N/A", _DASH)


def _ownership_component(blueprint_name: str, db_path: str) -> ComponentScore:
    """Ownership assignment as a 0-100 component (GM-1)."""
    try:
        owner = get_owner(blueprint_name, db_path)
        if owner is not None:
            return ComponentScore("ownership", 100.0, "Set", _CHECK)
        return ComponentScore("ownership", 0.0, "None", _WARN)
    except Exception:
        return ComponentScore("ownership", 0.0, "None", _WARN)


def compute_blueprint_score(
    blueprint_name: str,
    blueprint_dir: str,
    db_path: str,
) -> BlueprintScore:
    """Gather every quality signal and compute the weighted composite score.

    Each component is gathered defensively — a missing or failing signal scores
    0 (or 50 for a not-yet-established baseline) rather than raising.
    """
    components = [
        _coverage_component(blueprint_name, blueprint_dir),
        _volume_component(blueprint_name, db_path),
        _drift_component(blueprint_name, blueprint_dir, db_path),
        _ownership_component(blueprint_name, db_path),
    ]
    composite = sum(c.score * WEIGHTS[c.name] for c in components)
    composite = round(composite, 2)
    return BlueprintScore(
        blueprint_name=blueprint_name,
        composite_score=composite,
        rating=get_rating(composite),
        components=components,
    )


def compute_scorecard(blueprints_dir: str, db_path: str) -> ScorecardReport:
    """Compute a ``BlueprintScore`` for every installed blueprint.

    Each immediate subdirectory of ``blueprints_dir`` is treated as an installed
    blueprint. Returns a ``ScorecardReport`` with the average across blueprints.
    """
    root = Path(blueprints_dir)
    scores: list[BlueprintScore] = []
    if root.is_dir():
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                scores.append(compute_blueprint_score(entry.name, str(entry), db_path))

    if scores:
        average = round(sum(s.composite_score for s in scores) / len(scores), 2)
    else:
        average = 0.0
    return ScorecardReport(
        blueprints=scores,
        average_score=average,
        average_rating=get_rating(average),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
