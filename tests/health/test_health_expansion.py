"""Tests for the Sprint B EMS health checks (quality_score, slo_violations,
volume_anomalies, schema_drift, architecture_drift).

Deterministic, no AI. Each test uses a ``tmp_path``; checks resolve state and
blueprints relative to ``cwd`` (passed explicitly), so the real project is never
touched. Follows the ``tests/health`` checker pattern.
"""

from __future__ import annotations

import types
import uuid
from pathlib import Path

import pytest
from pipelinekit.cli.main import app
from pipelinekit.health import ERROR, OK, WARNING
from pipelinekit.health.architecture_drift import ArchitectureDriftHealthChecker
from pipelinekit.health.quality_score import QualityScoreHealthChecker
from pipelinekit.health.schema_drift import SchemaDriftHealthChecker
from pipelinekit.health.slo_violations import SLOViolationsHealthChecker
from pipelinekit.health.volume_anomalies import VolumeAnomaliesHealthChecker
from pipelinekit.quality.scorecard import BlueprintScore
from pipelinekit.state import db
from typer.testing import CliRunner

runner = CliRunner()


def _install(tmp_path: Path, name: str = "test-bp") -> None:
    """Create a minimal installed blueprint under ``tmp_path/blueprints``."""
    bp = tmp_path / "blueprints" / name
    bp.mkdir(parents=True, exist_ok=True)
    (bp / "blueprint.json").write_text(f'{{"name": "{name}"}}', encoding="utf-8")


def _dbp(tmp_path: Path) -> str:
    """Return the CWD-resolved state.db path the checks will read."""
    return str(db.get_db_path(tmp_path))


def _fake_score(composite: float, rating: str):
    """Return a compute_blueprint_score stand-in yielding a fixed score."""

    def _f(name: str, bp_dir: str, db_path: str) -> BlueprintScore:
        return BlueprintScore(
            blueprint_name=name,
            composite_score=composite,
            rating=rating,
            components=[],
        )

    return _f


# --- quality_score --------------------------------------------------------


def test_quality_score_check_passes_when_no_blueprints(tmp_path: Path) -> None:
    """quality_score is OK when no blueprints are installed."""
    result = QualityScoreHealthChecker().check(cwd=tmp_path)
    assert result.status == OK


def test_quality_score_check_warns_on_fair_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """quality_score WARNS when a blueprint scores Fair (< 75)."""
    _install(tmp_path)
    monkeypatch.setattr(
        "pipelinekit.quality.scorecard.compute_blueprint_score",
        _fake_score(60.0, "Fair"),
    )
    result = QualityScoreHealthChecker().check(cwd=tmp_path)
    assert result.status == WARNING


def test_quality_score_check_fails_on_poor_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """quality_score ERRORS when a blueprint scores Poor (< 50)."""
    _install(tmp_path)
    monkeypatch.setattr(
        "pipelinekit.quality.scorecard.compute_blueprint_score",
        _fake_score(30.0, "Poor"),
    )
    result = QualityScoreHealthChecker().check(cwd=tmp_path)
    assert result.status == ERROR


def test_quality_score_skips_proposed_blueprints(tmp_path: Path) -> None:
    """A blueprint with status 'proposed' is skipped, not flagged Poor.

    The bare blueprint would score Poor (~25) if scored; declaring it 'proposed'
    skips it, so the check stays OK instead of erroring.
    """
    bp = tmp_path / "blueprints" / "prop-bp"
    bp.mkdir(parents=True)
    (bp / "blueprint.json").write_text(
        '{"name": "prop-bp", "status": "proposed"}', encoding="utf-8"
    )
    result = QualityScoreHealthChecker().check(cwd=tmp_path)
    assert result.status == OK
    assert any("proposed" in detail for detail in (result.details or []))


# --- slo_violations -------------------------------------------------------


def test_slo_violations_passes_when_no_slos(tmp_path: Path) -> None:
    """slo_violations is OK when no SLOs are defined."""
    result = SLOViolationsHealthChecker().check(cwd=tmp_path)
    assert result.status == OK


def test_slo_violations_fails_on_violation(tmp_path: Path) -> None:
    """slo_violations ERRORS when a defined SLO is VIOLATED."""
    from pipelinekit.observability.slo import set_slo
    from pipelinekit.quality.anomaly import record_row_counts

    db_path = _dbp(tmp_path)
    set_slo("test-bp", "charges", "row_count", 1000.0, "rows", db_path)
    record_row_counts("test-bp", {"charges": 500}, db_path)

    result = SLOViolationsHealthChecker().check(cwd=tmp_path)
    assert result.status == ERROR


# --- volume_anomalies -----------------------------------------------------


def test_volume_anomalies_passes_with_no_history(tmp_path: Path) -> None:
    """volume_anomalies is OK when there is no row count history."""
    _install(tmp_path)
    result = VolumeAnomaliesHealthChecker().check(cwd=tmp_path)
    assert result.status == OK


def test_volume_anomalies_warns_on_anomaly(tmp_path: Path) -> None:
    """volume_anomalies WARNS when a table's latest count is anomalous."""
    from pipelinekit.quality.anomaly import record_row_counts

    _install(tmp_path)
    db_path = _dbp(tmp_path)
    for _ in range(5):
        record_row_counts("test-bp", {"charges": 45000}, db_path)
    record_row_counts("test-bp", {"charges": 500}, db_path)  # 98% drop

    result = VolumeAnomaliesHealthChecker().check(cwd=tmp_path)
    assert result.status == WARNING


# --- schema_drift ---------------------------------------------------------


def test_schema_drift_passes_with_no_snapshots(tmp_path: Path) -> None:
    """schema_drift is OK when no contract snapshots exist (NO_BASELINE=pass)."""
    _install(tmp_path)
    result = SchemaDriftHealthChecker().check(cwd=tmp_path)
    assert result.status == OK


def test_schema_drift_warns_on_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """schema_drift WARNS when a table has drifted from its contract."""
    _install(tmp_path)
    drifted = types.SimpleNamespace(
        table_name="charges", status="DRIFTED", drift_items=[]
    )
    monkeypatch.setattr(
        "pipelinekit.quality.drift.check_blueprint_drift",
        lambda name, bp_dir, db_path: [drifted],
    )
    result = SchemaDriftHealthChecker().check(cwd=tmp_path)
    assert result.status == WARNING


# --- architecture_drift ---------------------------------------------------


def test_architecture_drift_passes_with_no_dependencies(tmp_path: Path) -> None:
    """architecture_drift is OK when no dependencies are documented."""
    result = ArchitectureDriftHealthChecker().check(cwd=tmp_path)
    assert result.status == OK


def test_architecture_drift_fails_on_broken_dependency(tmp_path: Path) -> None:
    """architecture_drift ERRORS when a documented dependency is broken."""
    from pipelinekit.architecture.dependency import BlueprintDependency

    db_path = _dbp(tmp_path)
    dep = BlueprintDependency(
        id=str(uuid.uuid4()),
        from_blueprint="bp-a",
        to_blueprint="bp-gone",
        dependency_type="contract",
        reason=None,
        detected_at="2026-01-01T00:00:00Z",
    )
    db.insert_dependency(dep, db_path)  # neither blueprint dir exists -> broken

    result = ArchitectureDriftHealthChecker().check(cwd=tmp_path)
    assert result.status == ERROR


# --- full --strict run ----------------------------------------------------


def test_health_strict_now_runs_eleven_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`health --strict` output names all 11 checks."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["health", "--strict"])
    for name in [
        "deps",
        "security",
        "blueprints",
        "specs",
        "tests",
        "ownership",
        "quality_score",
        "slo_violations",
        "volume_anomalies",
        "schema_drift",
        "architecture_drift",
    ]:
        assert name in result.output, f"Missing check: {name}"
