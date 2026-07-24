"""Tests for QM-8 composite quality scorecard (SPEC-030).

Deterministic, no AI, read-only. Every test uses a ``tmp_path`` SQLite database
and minimal blueprint fixtures reached via ``monkeypatch.chdir`` — the real
``blueprints/`` directory and project ``state.db`` are never touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pipelinekit.governance.ownership import set_owner
from pipelinekit.quality.coverage import compute_blueprint_coverage
from pipelinekit.quality.scorecard import (
    BlueprintScore,
    compute_blueprint_score,
    compute_scorecard,
    get_rating,
)

# 2/2 columns tested -> 100% coverage.
_FULL_COVERAGE = """\
version: 2
models:
  - name: orders
    columns:
      - name: order_id
        tests: [unique, not_null]
      - name: customer_id
        tests: [not_null]
"""

# 1/2 columns tested -> 50% coverage.
_HALF_COVERAGE = """\
version: 2
models:
  - name: orders
    columns:
      - name: order_id
        tests: [unique, not_null]
      - name: customer_id
"""


def _install(tmp_path: Path, name: str, schema_body: str) -> str:
    """Create a minimal installed blueprint and return its directory path."""
    bp = tmp_path / "blueprints" / name
    models = bp / "transform" / "models" / "staging"
    models.mkdir(parents=True)
    (bp / "blueprint.json").write_text(f'{{"name": "{name}"}}', encoding="utf-8")
    (models / "schema.yml").write_text(schema_body, encoding="utf-8")
    return str(bp)


def _components(score: BlueprintScore) -> dict:
    """Index a BlueprintScore's components by name."""
    return {c.name: c for c in score.components}


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    """Chdir into a temp project root; return (tmp_path, db_path)."""
    monkeypatch.chdir(tmp_path)
    return tmp_path, str(tmp_path / "state.db")


def test_qm8_compute_score_returns_blueprint_score(env: tuple[Path, str]) -> None:
    """compute_blueprint_score returns a BlueprintScore with four components."""
    tmp_path, db_path = env
    bp_dir = _install(tmp_path, "test-bp", _HALF_COVERAGE)

    score = compute_blueprint_score("test-bp", bp_dir, db_path)

    assert isinstance(score, BlueprintScore)
    assert score.blueprint_name == "test-bp"
    assert isinstance(score.composite_score, float)
    assert score.rating in {"Excellent", "Good", "Fair", "Poor"}
    assert {c.name for c in score.components} == {
        "coverage",
        "volume",
        "drift",
        "ownership",
    }


def test_qm8_ownership_component_100_when_owner_set(env: tuple[Path, str]) -> None:
    """The ownership component scores 100 when an owner is assigned."""
    tmp_path, db_path = env
    bp_dir = _install(tmp_path, "test-bp", _HALF_COVERAGE)
    set_owner("test-bp", "Jane Smith", "jane@company.com", None, None, db_path)

    score = compute_blueprint_score("test-bp", bp_dir, db_path)

    assert _components(score)["ownership"].score == 100.0


def test_qm8_ownership_component_0_when_no_owner(env: tuple[Path, str]) -> None:
    """The ownership component scores 0 when no owner is assigned."""
    tmp_path, db_path = env
    bp_dir = _install(tmp_path, "test-bp", _HALF_COVERAGE)

    score = compute_blueprint_score("test-bp", bp_dir, db_path)

    assert _components(score)["ownership"].score == 0.0


def test_qm8_coverage_component_matches_blueprint_coverage_pct(
    env: tuple[Path, str],
) -> None:
    """The coverage component equals compute_blueprint_coverage's percentage."""
    tmp_path, db_path = env
    bp_dir = _install(tmp_path, "test-bp", _HALF_COVERAGE)

    expected = compute_blueprint_coverage("test-bp", bp_dir).blueprint_coverage_pct
    score = compute_blueprint_score("test-bp", bp_dir, db_path)

    assert _components(score)["coverage"].score == expected
    assert expected == 50.0


def test_qm8_volume_component_50_when_no_history(env: tuple[Path, str]) -> None:
    """The volume component scores 50 when no row-count history exists."""
    tmp_path, db_path = env
    bp_dir = _install(tmp_path, "test-bp", _HALF_COVERAGE)

    score = compute_blueprint_score("test-bp", bp_dir, db_path)

    volume = _components(score)["volume"]
    assert volume.score == 50.0
    assert volume.status == "ESTABLISHING"


def test_qm8_composite_score_uses_correct_weights(env: tuple[Path, str]) -> None:
    """Composite = 0.4*coverage + 0.3*volume + 0.2*drift + 0.1*ownership."""
    tmp_path, db_path = env
    bp_dir = _install(tmp_path, "test-bp", _FULL_COVERAGE)  # coverage 100
    set_owner("test-bp", "Jane", "jane@company.com", None, None, db_path)  # own 100

    score = compute_blueprint_score("test-bp", bp_dir, db_path)
    components = _components(score)

    # No row counts -> volume 50; no contract snapshot -> drift NO_BASELINE 50.
    assert components["coverage"].score == 100.0
    assert components["volume"].score == 50.0
    assert components["drift"].score == 50.0
    assert components["ownership"].score == 100.0
    expected = 0.40 * 100 + 0.30 * 50 + 0.20 * 50 + 0.10 * 100
    assert score.composite_score == pytest.approx(expected)  # 75.0
    assert score.rating == "Good"


def test_qm8_get_rating_returns_excellent_for_high_score() -> None:
    """get_rating returns Excellent at or above 90."""
    assert get_rating(95.0) == "Excellent"
    assert get_rating(90.0) == "Excellent"


def test_qm8_get_rating_returns_poor_for_low_score() -> None:
    """get_rating returns Poor below 50."""
    assert get_rating(10.0) == "Poor"
    assert get_rating(49.9) == "Poor"


def test_qm8_scorecard_report_aggregates_all_blueprints(
    env: tuple[Path, str],
) -> None:
    """compute_scorecard includes a score for every installed blueprint."""
    tmp_path, db_path = env
    _install(tmp_path, "bp-a", _HALF_COVERAGE)
    _install(tmp_path, "bp-b", _HALF_COVERAGE)

    report = compute_scorecard(str(tmp_path / "blueprints"), db_path)

    assert len(report.blueprints) == 2
    assert {s.blueprint_name for s in report.blueprints} == {"bp-a", "bp-b"}
    assert report.average_rating in {"Excellent", "Good", "Fair", "Poor"}
