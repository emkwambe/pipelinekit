"""QM-10 — best-practices checker (SPEC-040).

Evaluates whether the tests a blueprint declares follow industry best practices,
not merely that tests exist. Where QM-4 asks "what percentage of columns have
tests?", QM-10 asks "are they the *right* tests?".

Seven best practices are checked (dbt Labs, DAMA-DMBOK2, Monte Carlo, ODCS):

* BP-001 Primary key integrity (CRITICAL) — a column with unique + not_null.
* BP-002 Source freshness declaration (HIGH) — sources.yml declares freshness.
* BP-003 Model documentation (MEDIUM) — every model has a description.
* BP-004 Column coverage >= 80% (HIGH).
* BP-005 Accepted values on categorical columns (MEDIUM).
* BP-006 Staging naming convention stg_{source}__{entity} (LOW).
* BP-007 Contract coverage (MEDIUM) — every tested model has a contract.

Fully deterministic and read-only — no AI, no warehouse. Reuses QM-4's
``scan_dbt_coverage`` for column/test data.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from pipelinekit.quality.coverage import ModelCoverage, scan_dbt_coverage


class BPSeverity(str, Enum):
    """Best-practice severity, ordered from most to least severe."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BPStatus(str, Enum):
    """Per-practice evaluation status."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"  # insufficient data to check


@dataclass
class BestPracticeViolation:
    """One best-practice violation found in one model."""

    code: str
    name: str
    severity: BPSeverity
    model_name: str
    detail: str
    recommendation: str


@dataclass
class BestPracticeResult:
    """A blueprint's best-practice outcome, with score and letter grade."""

    blueprint_name: str
    violations: list[BestPracticeViolation] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    score: float = 0.0
    grade: str = "F"


@dataclass
class BestPracticesReport:
    """Best-practice outcomes across every installed blueprint."""

    blueprints: list[BestPracticeResult]
    total_violations: int
    critical_violations: int
    generated_at: str


# (code, name, severity, source citation)
BEST_PRACTICES: list[tuple[str, str, BPSeverity, str]] = [
    (
        "BP-001",
        "Primary key integrity",
        BPSeverity.CRITICAL,
        "dbt Best Practices: every model needs unique+not_null on primary key",
    ),
    (
        "BP-002",
        "Source freshness declaration",
        BPSeverity.HIGH,
        "dbt Best Practices: sources must declare freshness thresholds",
    ),
    (
        "BP-003",
        "Model documentation",
        BPSeverity.MEDIUM,
        "DAMA-DMBOK2: every model must have a description",
    ),
    (
        "BP-004",
        "Column coverage threshold (>= 80%)",
        BPSeverity.HIGH,
        "Monte Carlo 2024: 80% column test coverage threshold",
    ),
    (
        "BP-005",
        "Accepted values on categorical columns",
        BPSeverity.MEDIUM,
        "dbt Best Practices: categorical columns need accepted_values",
    ),
    (
        "BP-006",
        "Staging model naming convention",
        BPSeverity.LOW,
        "dbt Best Practices: stg_{source}__{entity} naming",
    ),
    (
        "BP-007",
        "Contract coverage",
        BPSeverity.MEDIUM,
        "ODCS/PipelineKit: every tested model needs a contract",
    ),
]

_SEVERITY_WEIGHT = {
    BPSeverity.CRITICAL: 40,
    BPSeverity.HIGH: 25,
    BPSeverity.MEDIUM: 20,
    BPSeverity.LOW: 15,
}
_SEVERITY_BY_CODE = {code: sev for code, _name, sev, _src in BEST_PRACTICES}

_CATEGORICAL_NAMES = {
    "status",
    "type",
    "category",
    "state",
    "kind",
    "tier",
    "plan",
    "role",
    "currency",
    "country",
}
_STAGING_PATTERN = re.compile(r"^stg_[a-z0-9]+__[a-z0-9_]+$")


def _model_descriptions(blueprint_dir: Path) -> dict[str, str]:
    """Map model name -> description by reading the schema.yml files directly.

    ``ModelCoverage`` does not carry the model description, so BP-003 reads it
    here. Unreadable/malformed schema files are skipped, never raised.
    """
    descriptions: dict[str, str] = {}
    models_dir = blueprint_dir / "transform" / "models"
    if not models_dir.is_dir():
        return descriptions
    for schema_path in sorted(models_dir.rglob("*.yml")):
        if "/target/" in schema_path.as_posix():
            continue
        try:
            data = yaml.safe_load(schema_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        for model in data.get("models") or []:
            if isinstance(model, dict) and model.get("name"):
                descriptions[model["name"]] = str(
                    model.get("description") or ""
                ).strip()
    return descriptions


def _has_freshness(blueprint_dir: Path) -> bool | None:
    """Return whether any source declares freshness, or None if no sources.yml."""
    sources_yml = blueprint_dir / "transform" / "models" / "staging" / "sources.yml"
    if not sources_yml.is_file():
        return None
    try:
        data = yaml.safe_load(sources_yml.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    return any(
        isinstance(src, dict) and "freshness" in src
        for src in (data.get("sources") or [])
    )


def _has_contract(model: ModelCoverage, contracts_dir: Path) -> bool:
    """Return whether a contract file plausibly governs ``model``.

    Matches on the model's entity (the segment after ``__``, else the whole
    name): a contract governs the model if its file stem equals the entity, the
    entity contains the stem, or the stem appears in the model name. This is
    source-agnostic (unlike a hard-coded ``stg_postgres__`` strip).
    """
    if not contracts_dir.is_dir():
        return False
    entity = model.name.split("__")[-1]
    for contract in contracts_dir.iterdir():
        if contract.suffix not in (".yaml", ".yml"):
            continue
        stem = contract.stem
        if stem == entity or stem in entity or stem in model.name:
            return True
    return False


def _blueprint_has_contract_in_state(blueprint_name: str, db_path: str) -> bool:
    """Return whether ``dc_contract_versions`` holds any contract for a blueprint."""
    try:
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT 1 FROM dc_contract_versions "
                "WHERE blueprint_name = ? LIMIT 1",
                (blueprint_name,),
            ).fetchone()
        finally:
            conn.close()
        return row is not None
    except sqlite3.Error:
        return False


def check_blueprint_best_practices(
    blueprint_name: str,
    blueprints_dir: str,
    db_path: str,
) -> BestPracticeResult:
    """Check one blueprint against all seven best practices (QM-10)."""
    blueprint_dir = Path(blueprints_dir) / blueprint_name
    try:
        models = scan_dbt_coverage(str(blueprint_dir))
    except Exception:
        models = []

    if not models:
        # No schema.yml models — nothing to evaluate.
        return BestPracticeResult(
            blueprint_name=blueprint_name,
            skipped=[bp[0] for bp in BEST_PRACTICES],
            score=0.0,
            grade="N/A",
        )

    violations: list[BestPracticeViolation] = []
    skipped: set[str] = set()
    descriptions = _model_descriptions(blueprint_dir)
    contracts_dir = blueprint_dir / "contracts"

    # BP-001 — primary key integrity.
    for model in models:
        has_pk = any(
            "unique" in [t.lower() for t in col.test_types]
            and "not_null" in [t.lower() for t in col.test_types]
            for col in model.columns
        )
        if not has_pk:
            violations.append(
                BestPracticeViolation(
                    "BP-001",
                    "Primary key integrity",
                    BPSeverity.CRITICAL,
                    model.name,
                    f"No column with both unique+not_null tests in {model.name}.",
                    "Add 'unique' and 'not_null' tests to the primary key column "
                    f"of {model.name} in schema.yml.",
                )
            )

    # BP-002 — source freshness declaration.
    freshness = _has_freshness(blueprint_dir)
    if freshness is None:
        skipped.add("BP-002")
    elif not freshness:
        violations.append(
            BestPracticeViolation(
                "BP-002",
                "Source freshness declaration",
                BPSeverity.HIGH,
                "sources.yml",
                "No freshness thresholds declared in sources.yml.",
                "Add 'freshness: {warn_after, error_after}' to each source in "
                "sources.yml.",
            )
        )

    # BP-003 — model documentation.
    for model in models:
        if not descriptions.get(model.name, "").strip():
            violations.append(
                BestPracticeViolation(
                    "BP-003",
                    "Model documentation",
                    BPSeverity.MEDIUM,
                    model.name,
                    f"No description for model {model.name}.",
                    f"Add a 'description:' to {model.name} in schema.yml.",
                )
            )

    # BP-004 — column coverage >= 80%.
    for model in models:
        if model.total_columns > 0 and model.coverage_pct < 80.0:
            violations.append(
                BestPracticeViolation(
                    "BP-004",
                    "Column coverage threshold (>= 80%)",
                    BPSeverity.HIGH,
                    model.name,
                    f"{model.name}: {model.coverage_pct:.1f}% column coverage "
                    f"({model.tested_columns}/{model.total_columns} tested); "
                    "industry standard is >= 80%.",
                    f"Add tests to the untested columns of {model.name}; focus on "
                    "foreign keys and business-critical fields first.",
                )
            )

    # BP-005 — accepted_values on categorical columns.
    for model in models:
        for col in model.columns:
            if col.name.lower() in _CATEGORICAL_NAMES:
                has_accepted = any(
                    "accepted_values" in t.lower() for t in col.test_types
                )
                if not has_accepted:
                    violations.append(
                        BestPracticeViolation(
                            "BP-005",
                            "Accepted values on categorical columns",
                            BPSeverity.MEDIUM,
                            model.name,
                            f"{model.name}.{col.name} looks categorical but has "
                            "no accepted_values test.",
                            f"Add an accepted_values test to {model.name}.{col.name} "
                            "listing the valid values.",
                        )
                    )

    # BP-006 — staging naming convention.
    staging_models = [m for m in models if m.name.startswith("stg_")]
    if not staging_models:
        skipped.add("BP-006")
    else:
        for model in staging_models:
            if not _STAGING_PATTERN.match(model.name):
                violations.append(
                    BestPracticeViolation(
                        "BP-006",
                        "Staging model naming convention",
                        BPSeverity.LOW,
                        model.name,
                        f"{model.name} does not follow stg_{{source}}__{{entity}} "
                        "(double underscore).",
                        f"Rename {model.name} to stg_{{source}}__{{entity}} format, "
                        "e.g. stg_postgres__orders.",
                    )
                )

    # BP-007 — contract coverage (only models that have tests).
    tested_models = [m for m in models if m.tested_columns > 0]
    if not tested_models:
        skipped.add("BP-007")
    else:
        state_has_contract = _blueprint_has_contract_in_state(blueprint_name, db_path)
        for model in tested_models:
            if not _has_contract(model, contracts_dir) and not state_has_contract:
                violations.append(
                    BestPracticeViolation(
                        "BP-007",
                        "Contract coverage",
                        BPSeverity.MEDIUM,
                        model.name,
                        f"{model.name} has dbt tests but no PipelineKit contract.",
                        f"Create contracts/{model.name.split('__')[-1]}.yaml and run "
                        f"'pipelinekit contract snapshot'.",
                    )
                )

    # Score: deduct each distinct failed practice's severity weight once, so the
    # score reflects which practices fail — not how many models a blueprint has.
    failed = {v.code for v in violations}
    passed = [
        code
        for code, _n, _s, _src in BEST_PRACTICES
        if code not in failed and code not in skipped
    ]
    total_weight = sum(
        _SEVERITY_WEIGHT[_SEVERITY_BY_CODE[code]]
        for code, _n, _s, _src in BEST_PRACTICES
        if code not in skipped
    )
    violation_weight = sum(_SEVERITY_WEIGHT[_SEVERITY_BY_CODE[c]] for c in failed)
    score = (
        max(0.0, (total_weight - violation_weight) / total_weight * 100)
        if total_weight > 0
        else 100.0
    )

    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    return BestPracticeResult(
        blueprint_name=blueprint_name,
        violations=violations,
        passed=passed,
        skipped=sorted(skipped),
        score=round(score, 1),
        grade=grade,
    )


def check_all_best_practices(
    blueprints_dir: str,
    db_path: str,
) -> BestPracticesReport:
    """Check every installed blueprint against the best practices (QM-10)."""
    root = Path(blueprints_dir)
    results: list[BestPracticeResult] = []
    if root.is_dir():
        for entry in sorted(root.iterdir()):
            if entry.is_dir() and not entry.name.startswith("."):
                results.append(
                    check_blueprint_best_practices(entry.name, blueprints_dir, db_path)
                )

    total_violations = sum(len(r.violations) for r in results)
    critical_violations = sum(
        1 for r in results for v in r.violations if v.severity == BPSeverity.CRITICAL
    )
    return BestPracticesReport(
        blueprints=results,
        total_violations=total_violations,
        critical_violations=critical_violations,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
