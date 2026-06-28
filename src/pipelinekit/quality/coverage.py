"""QM-4 — quality coverage monitoring (SPEC-022).

Measures how much of each installed blueprint is covered by quality checks by
reading the blueprint files on disk: dbt ``schema.yml`` files (primary) and Soda
``checks.yaml`` files (secondary). Purely deterministic and read-only — no AI, no
warehouse connection, and no writes to ``state.db`` (ADR-023).

Two coverage sources:

* dbt test coverage — for each model in ``transform/models/**/schema.yml``, count
  the columns that declare at least one test. Compiled artifacts under
  ``transform/target/`` are skipped (they are not declared-intent sources).
* Soda check coverage — for each ``checks for {table}:`` block in
  ``quality/checks.yaml``, classify and count the checks.

See: SPEC-022, ADR-023.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from pipelinekit.core.errors import QualityError

# Soda check classification — first matching pattern wins; default is "custom".
CHECK_PATTERNS: list[tuple[str, str]] = [
    ("freshness", r"freshness\("),
    ("row_count", r"row_count"),
    ("missing_count", r"missing_count\("),
    ("duplicate_count", r"duplicate_count\("),
    ("invalid_count", r"invalid_count\("),
]


@dataclass
class ColumnCoverage:
    """Coverage for a single dbt model column."""

    name: str
    test_types: list[str]
    is_tested: bool


@dataclass
class ModelCoverage:
    """Coverage for a single dbt model defined in a schema.yml."""

    name: str
    schema_file: str
    total_columns: int
    tested_columns: int
    coverage_pct: float
    columns: list[ColumnCoverage]
    untested_column_names: list[str]


@dataclass
class SodaCoverage:
    """Coverage for a single Soda ``checks for {table}:`` block."""

    table_name: str
    check_types: list[str]
    total_checks: int


@dataclass
class BlueprintCoverage:
    """Aggregated coverage for one installed blueprint."""

    blueprint_name: str
    models: list[ModelCoverage]
    soda_checks: list[SodaCoverage]
    total_columns: int
    total_tested_columns: int
    blueprint_coverage_pct: float
    untested_columns: list[tuple[str, str]]  # (model_name, column_name)


@dataclass
class CoverageReport:
    """A full coverage report across every installed blueprint."""

    blueprints: list[BlueprintCoverage] = field(default_factory=list)
    generated_at: str = ""


def _classify_check(check: object) -> str:
    """Classify a Soda check string into a known type, or ``custom``."""
    text = str(check)
    for type_name, pattern in CHECK_PATTERNS:
        if re.search(pattern, text):
            return type_name
    return "custom"


def scan_dbt_coverage(blueprint_dir: str) -> list[ModelCoverage]:
    """Scan ``{blueprint_dir}/transform/models/`` for dbt model coverage.

    Walks every ``*.yml`` under ``transform/models/``, skipping any path under a
    ``target/`` directory (compiled artifacts). Handles both test formats — a
    bare string (``unique``) and a single-key dict (``accepted_values: {...}``).

    Returns an empty list if ``transform/models/`` does not exist.

    Raises:
        QualityError: ``PK-QM-002`` if a ``.yml`` file cannot be parsed.
    """
    root = Path(blueprint_dir)
    models_dir = root / "transform" / "models"
    if not models_dir.is_dir():
        return []

    models: list[ModelCoverage] = []
    for schema_path in sorted(models_dir.rglob("*.yml")):
        relative = schema_path.relative_to(root).as_posix()
        if "/target/" in f"/{relative}/":
            continue
        try:
            data = yaml.safe_load(schema_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise QualityError(
                "PK-QM-002",
                f"Schema file could not be parsed: {relative}",
                {"path": str(schema_path), "detail": str(exc)},
            ) from exc

        for model in data.get("models") or []:
            models.append(_model_coverage(model, relative))
    return models


def _model_coverage(model: dict, schema_file: str) -> ModelCoverage:
    """Build a ``ModelCoverage`` from a single parsed dbt model entry."""
    columns: list[ColumnCoverage] = []
    for col in model.get("columns") or []:
        test_types: list[str] = []
        for test in col.get("tests") or []:
            if isinstance(test, str):
                test_types.append(test)
            elif isinstance(test, dict) and test:
                test_types.append(next(iter(test.keys())))
            # Unknown formats are skipped.
        columns.append(
            ColumnCoverage(
                name=col.get("name", ""),
                test_types=test_types,
                is_tested=len(test_types) > 0,
            )
        )

    total = len(columns)
    tested = sum(1 for c in columns if c.is_tested)
    coverage_pct = (tested / total * 100) if total > 0 else 0.0
    untested = [c.name for c in columns if not c.is_tested]
    return ModelCoverage(
        name=model.get("name", ""),
        schema_file=schema_file,
        total_columns=total,
        tested_columns=tested,
        coverage_pct=coverage_pct,
        columns=columns,
        untested_column_names=untested,
    )


def scan_soda_coverage(blueprint_dir: str) -> list[SodaCoverage]:
    """Scan ``{blueprint_dir}/quality/checks.yaml`` for Soda check coverage.

    Returns an empty list if the file does not exist. Each top-level
    ``checks for {table}:`` key becomes one ``SodaCoverage``.
    """
    checks_path = Path(blueprint_dir) / "quality" / "checks.yaml"
    if not checks_path.is_file():
        return []

    data = yaml.safe_load(checks_path.read_text(encoding="utf-8")) or {}
    coverage: list[SodaCoverage] = []
    for key, checks in data.items():
        if not isinstance(key, str) or not key.startswith("checks for "):
            continue
        table_name = key.replace("checks for ", "").strip()
        check_list = checks or []
        check_types = [_classify_check(check) for check in check_list]
        coverage.append(
            SodaCoverage(
                table_name=table_name,
                check_types=check_types,
                total_checks=len(check_list),
            )
        )
    return coverage


def compute_blueprint_coverage(
    blueprint_name: str, blueprint_dir: str
) -> BlueprintCoverage:
    """Aggregate dbt and Soda coverage for a single blueprint."""
    models = scan_dbt_coverage(blueprint_dir)
    soda_checks = scan_soda_coverage(blueprint_dir)

    total_columns = sum(m.total_columns for m in models)
    total_tested = sum(m.tested_columns for m in models)
    blueprint_pct = (total_tested / total_columns * 100) if total_columns > 0 else 0.0
    untested = [(m.name, col) for m in models for col in m.untested_column_names]

    return BlueprintCoverage(
        blueprint_name=blueprint_name,
        models=models,
        soda_checks=soda_checks,
        total_columns=total_columns,
        total_tested_columns=total_tested,
        blueprint_coverage_pct=blueprint_pct,
        untested_columns=untested,
    )


def compute_coverage_report(blueprints_dir: str) -> CoverageReport:
    """Build a coverage report across every installed blueprint.

    Each immediate subdirectory of ``blueprints_dir`` is treated as an installed
    blueprint. Returns an empty report if the directory does not exist.
    """
    root = Path(blueprints_dir)
    blueprints: list[BlueprintCoverage] = []
    if root.is_dir():
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                blueprints.append(compute_blueprint_coverage(entry.name, str(entry)))

    generated_at = datetime.now(timezone.utc).isoformat()
    return CoverageReport(blueprints=blueprints, generated_at=generated_at)
