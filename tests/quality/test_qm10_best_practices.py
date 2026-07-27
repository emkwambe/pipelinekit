"""Tests for QM-10 best-practices checker (SPEC-040).

Deterministic, no AI. Each test installs a targeted blueprint under ``tmp_path``
so a single best practice can be exercised in isolation. The final test checks
the shipped ``postgres-to-duckdb`` reference blueprint against its own standard.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.quality.best_practices import (
    BPSeverity,
    check_all_best_practices,
    check_blueprint_best_practices,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]

_COMPLIANT_SCHEMA = """\
version: 2
models:
  - name: stg_pg__orders
    description: "Staged orders. One row per order."
    columns:
      - name: order_id
        description: "Primary key"
        tests: [unique, not_null]
      - name: status
        description: "Order status"
        tests:
          - not_null
          - accepted_values:
              values: ['pending', 'shipped']
"""

_SOURCES_WITH_FRESHNESS = """\
version: 2
sources:
  - name: pg_raw
    freshness:
      warn_after: {count: 12, period: hour}
    loaded_at_field: _loaded_at
    tables:
      - name: orders
"""

_ORDERS_CONTRACT = """\
table: orders
version: "1.0.0"
columns:
  - name: order_id
    type: integer
    nullable: false
    unique: true
"""


def _install(
    tmp_path: Path,
    name: str,
    schema_yml: str,
    *,
    sources_yml: str | None = None,
    contracts: dict[str, str] | None = None,
) -> str:
    """Install a minimal blueprint; return the blueprints_dir path."""
    bp = tmp_path / "blueprints" / name
    models = bp / "transform" / "models" / "staging"
    models.mkdir(parents=True)
    (bp / "blueprint.json").write_text(f'{{"name": "{name}"}}', encoding="utf-8")
    (models / "schema.yml").write_text(schema_yml, encoding="utf-8")
    if sources_yml is not None:
        (models / "sources.yml").write_text(sources_yml, encoding="utf-8")
    if contracts:
        cdir = bp / "contracts"
        cdir.mkdir()
        for fname, content in contracts.items():
            (cdir / fname).write_text(content, encoding="utf-8")
    return str(tmp_path / "blueprints")


def _dbp(tmp_path: Path) -> str:
    return str(tmp_path / "state.db")


def _codes(result) -> set[str]:
    return {v.code for v in result.violations}


def test_qm10_passes_all_checks_for_compliant_blueprint(tmp_path: Path) -> None:
    """A fully compliant blueprint passes all 7 best practices."""
    bp_dir = _install(
        tmp_path,
        "good",
        _COMPLIANT_SCHEMA,
        sources_yml=_SOURCES_WITH_FRESHNESS,
        contracts={"orders.yaml": _ORDERS_CONTRACT},
    )
    result = check_blueprint_best_practices("good", bp_dir, _dbp(tmp_path))
    assert result.violations == []
    assert result.grade == "A"
    assert len(result.passed) == 7


def test_qm10_detects_missing_primary_key_bp001(tmp_path: Path) -> None:
    """BP-001 fails when no column has both unique+not_null."""
    schema = (
        "version: 2\nmodels:\n  - name: stg_pg__orders\n"
        '    description: "x"\n    columns:\n      - name: order_id\n'
        "        tests: [not_null]\n"
    )
    bp_dir = _install(tmp_path, "bp", schema)
    result = check_blueprint_best_practices("bp", bp_dir, _dbp(tmp_path))
    assert "BP-001" in _codes(result)


def test_qm10_detects_missing_source_freshness_bp002(tmp_path: Path) -> None:
    """BP-002 fails when sources.yml has no freshness declaration."""
    sources = "version: 2\nsources:\n  - name: pg_raw\n    tables:\n      - name: o\n"
    bp_dir = _install(tmp_path, "bp", _COMPLIANT_SCHEMA, sources_yml=sources)
    result = check_blueprint_best_practices("bp", bp_dir, _dbp(tmp_path))
    assert "BP-002" in _codes(result)


def test_qm10_detects_missing_model_description_bp003(tmp_path: Path) -> None:
    """BP-003 fails when a model has no description."""
    schema = (
        "version: 2\nmodels:\n  - name: stg_pg__orders\n    columns:\n"
        "      - name: order_id\n        tests: [unique, not_null]\n"
    )
    bp_dir = _install(tmp_path, "bp", schema)
    result = check_blueprint_best_practices("bp", bp_dir, _dbp(tmp_path))
    assert "BP-003" in _codes(result)


def test_qm10_detects_low_column_coverage_bp004(tmp_path: Path) -> None:
    """BP-004 fails when column coverage < 80%."""
    schema = (
        "version: 2\nmodels:\n  - name: stg_pg__orders\n"
        '    description: "x"\n    columns:\n'
        "      - name: order_id\n        tests: [unique, not_null]\n"
        "      - name: a\n      - name: b\n"  # 1/3 tested = 33%
    )
    bp_dir = _install(tmp_path, "bp", schema)
    result = check_blueprint_best_practices("bp", bp_dir, _dbp(tmp_path))
    assert "BP-004" in _codes(result)


def test_qm10_detects_categorical_without_accepted_values_bp005(
    tmp_path: Path,
) -> None:
    """BP-005 fails when a status/type column has no accepted_values test."""
    schema = (
        "version: 2\nmodels:\n  - name: stg_pg__orders\n"
        '    description: "x"\n    columns:\n'
        "      - name: order_id\n        tests: [unique, not_null]\n"
        "      - name: status\n        tests: [not_null]\n"  # categorical, no accepted
    )
    bp_dir = _install(tmp_path, "bp", schema)
    result = check_blueprint_best_practices("bp", bp_dir, _dbp(tmp_path))
    assert "BP-005" in _codes(result)


def test_qm10_detects_wrong_staging_naming_bp006(tmp_path: Path) -> None:
    """BP-006 fails when a staging model uses the wrong naming convention."""
    schema = (
        "version: 2\nmodels:\n  - name: stg_orders\n"  # no double underscore
        '    description: "x"\n    columns:\n'
        "      - name: order_id\n        tests: [unique, not_null]\n"
    )
    bp_dir = _install(tmp_path, "bp", schema)
    result = check_blueprint_best_practices("bp", bp_dir, _dbp(tmp_path))
    assert "BP-006" in _codes(result)


def test_qm10_detects_missing_contract_bp007(tmp_path: Path) -> None:
    """BP-007 fails when a tested model has no contract."""
    bp_dir = _install(tmp_path, "bp", _COMPLIANT_SCHEMA)  # no contracts dir
    result = check_blueprint_best_practices("bp", bp_dir, _dbp(tmp_path))
    assert "BP-007" in _codes(result)


def test_qm10_grade_a_for_100_score(tmp_path: Path) -> None:
    """Grade A (score 100) for a blueprint with zero violations."""
    bp_dir = _install(
        tmp_path,
        "good",
        _COMPLIANT_SCHEMA,
        sources_yml=_SOURCES_WITH_FRESHNESS,
        contracts={"orders.yaml": _ORDERS_CONTRACT},
    )
    result = check_blueprint_best_practices("good", bp_dir, _dbp(tmp_path))
    assert result.score == 100.0
    assert result.grade == "A"


def test_qm10_grade_f_for_critical_violation(tmp_path: Path) -> None:
    """A blueprint failing many practices (incl. a CRITICAL) grades F."""
    schema = (
        "version: 2\nmodels:\n  - name: stg_bad\n    columns:\n"  # bad naming, no desc
        "      - name: id\n        tests: [not_null]\n"  # no unique -> no PK
        "      - name: x\n"  # untested -> low coverage
    )
    bp_dir = _install(tmp_path, "bad", schema)  # no sources, no contracts
    result = check_blueprint_best_practices("bad", bp_dir, _dbp(tmp_path))
    assert result.grade == "F"
    assert any(v.severity == BPSeverity.CRITICAL for v in result.violations)


def test_qm10_report_aggregates_all_blueprints(tmp_path: Path) -> None:
    """check_all_best_practices returns one result per installed blueprint."""
    _install(tmp_path, "a", _COMPLIANT_SCHEMA)
    _install(tmp_path, "b", _COMPLIANT_SCHEMA)
    report = check_all_best_practices(str(tmp_path / "blueprints"), _dbp(tmp_path))
    assert len(report.blueprints) == 2
    assert {r.blueprint_name for r in report.blueprints} == {"a", "b"}


def test_qm10_postgres_to_duckdb_blueprint_passes_all(tmp_path: Path) -> None:
    """The shipped postgres-to-duckdb reference blueprint passes all 7 (Grade A)."""
    blueprints_dir = str(_REPO_ROOT / "blueprints")
    result = check_blueprint_best_practices(
        "postgres-to-duckdb", blueprints_dir, _dbp(tmp_path)
    )
    assert result.grade == "A", f"reference graded {result.grade}: {result.violations}"
    assert result.violations == []
    assert len(result.passed) == 7
