"""Tests for QM-4 quality coverage monitoring (SPEC-022).

Deterministic, read-only, no AI. Every test builds minimal schema.yml and
checks.yaml fixtures under ``tmp_path`` — the real ``blueprints/`` directory is
never touched.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.quality.coverage import (
    compute_blueprint_coverage,
    compute_coverage_report,
    scan_dbt_coverage,
    scan_soda_coverage,
)

_SCHEMA = """\
version: 2
models:
  - name: test_model
    columns:
      - name: id
        tests:
          - unique
          - not_null
      - name: name
        tests: []
"""

_SCHEMA_DICT_TEST = """\
version: 2
models:
  - name: dict_model
    columns:
      - name: status
        tests:
          - accepted_values:
              arguments:
                values: ['a', 'b']
"""

_CHECKS = """\
checks for test_table:
  - row_count > 0
  - missing_count(id) = 0
  - freshness(created_at) < 24h
"""


def _write_schema(blueprint_dir: Path, relative: str, content: str) -> None:
    """Write a schema.yml under the blueprint's transform/models tree."""
    path = blueprint_dir / "transform" / "models" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_checks(blueprint_dir: Path, content: str) -> None:
    """Write a quality/checks.yaml under the blueprint."""
    path = blueprint_dir / "quality" / "checks.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_qm4_scan_dbt_coverage_finds_models_and_columns(tmp_path: Path) -> None:
    """scan_dbt_coverage returns ModelCoverage for each model in schema.yml."""
    bp = tmp_path / "bp"
    _write_schema(bp, "staging/schema.yml", _SCHEMA)

    models = scan_dbt_coverage(str(bp))

    assert len(models) == 1
    assert models[0].name == "test_model"
    assert models[0].total_columns == 2
    assert models[0].tested_columns == 1
    assert models[0].schema_file == "transform/models/staging/schema.yml"


def test_qm4_scan_dbt_coverage_handles_string_tests(tmp_path: Path) -> None:
    """Parses 'unique' and 'not_null' string test format correctly."""
    bp = tmp_path / "bp"
    _write_schema(bp, "staging/schema.yml", _SCHEMA)

    models = scan_dbt_coverage(str(bp))
    id_col = models[0].columns[0]

    assert id_col.name == "id"
    assert id_col.test_types == ["unique", "not_null"]
    assert id_col.is_tested is True


def test_qm4_scan_dbt_coverage_handles_dict_tests(tmp_path: Path) -> None:
    """Parses 'accepted_values' dict test format correctly."""
    bp = tmp_path / "bp"
    _write_schema(bp, "core/schema.yml", _SCHEMA_DICT_TEST)

    models = scan_dbt_coverage(str(bp))
    status_col = models[0].columns[0]

    assert status_col.name == "status"
    assert status_col.test_types == ["accepted_values"]
    assert status_col.is_tested is True


def test_qm4_scan_dbt_coverage_skips_target_directory(tmp_path: Path) -> None:
    """Does not scan transform/target/ compiled files."""
    bp = tmp_path / "bp"
    _write_schema(bp, "staging/schema.yml", _SCHEMA)
    # A schema.yml under a target/ directory must be skipped.
    _write_schema(bp, "target/compiled/schema.yml", _SCHEMA_DICT_TEST)

    models = scan_dbt_coverage(str(bp))

    names = [m.name for m in models]
    assert names == ["test_model"]
    assert "dict_model" not in names


def test_qm4_scan_dbt_coverage_returns_empty_when_no_models_dir(tmp_path: Path) -> None:
    """Returns [] when transform/models/ does not exist."""
    assert scan_dbt_coverage(str(tmp_path)) == []


def test_qm4_scan_soda_coverage_parses_checks_yaml(tmp_path: Path) -> None:
    """scan_soda_coverage returns SodaCoverage with correct check types."""
    bp = tmp_path / "bp"
    _write_checks(bp, _CHECKS)

    soda = scan_soda_coverage(str(bp))

    assert len(soda) == 1
    assert soda[0].table_name == "test_table"
    assert soda[0].total_checks == 3
    assert set(soda[0].check_types) == {"row_count", "missing_count", "freshness"}


def test_qm4_scan_soda_coverage_returns_empty_when_no_checks_yaml(
    tmp_path: Path,
) -> None:
    """Returns [] when quality/checks.yaml does not exist."""
    assert scan_soda_coverage(str(tmp_path)) == []


def test_qm4_blueprint_coverage_pct_is_correct(tmp_path: Path) -> None:
    """coverage_pct = tested_columns / total_columns * 100."""
    bp = tmp_path / "bp"
    _write_schema(bp, "staging/schema.yml", _SCHEMA)

    bc = compute_blueprint_coverage("bp", str(bp))

    assert bc.total_columns == 2
    assert bc.total_tested_columns == 1
    assert bc.blueprint_coverage_pct == 50.0


def test_qm4_untested_columns_list_is_correct(tmp_path: Path) -> None:
    """untested_column_names contains columns with no tests."""
    bp = tmp_path / "bp"
    _write_schema(bp, "staging/schema.yml", _SCHEMA)

    models = scan_dbt_coverage(str(bp))
    bc = compute_blueprint_coverage("bp", str(bp))

    assert models[0].untested_column_names == ["name"]
    assert bc.untested_columns == [("test_model", "name")]


def test_qm4_coverage_report_includes_all_blueprints(tmp_path: Path) -> None:
    """CoverageReport contains one BlueprintCoverage per installed blueprint."""
    blueprints_dir = tmp_path / "blueprints"
    for name in ("bp_one", "bp_two"):
        _write_schema(blueprints_dir / name, "staging/schema.yml", _SCHEMA)

    report = compute_coverage_report(str(blueprints_dir))

    assert len(report.blueprints) == 2
    assert {bc.blueprint_name for bc in report.blueprints} == {"bp_one", "bp_two"}
    assert report.generated_at != ""
