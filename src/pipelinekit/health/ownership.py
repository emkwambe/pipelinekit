"""Ownership coverage check — surfaces unowned blueprints (GM-1, SPEC-023).

Reports which installed blueprints have no owner assigned in ``state.db``, and
(GM-4, SPEC-032) how much of each contract's column set has a declared domain
owner. Missing ownership is a governance gap, not a failure: this check returns
``warning`` (never ``error``) so ``health --strict`` flags it without treating
it as a hard fault (ADR-024).

Column coverage is deliberately softer than blueprint coverage: partial column
coverage is reported as detail on an otherwise ``ok`` result, because declaring
every column is a maturity goal rather than a baseline expectation.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.governance.column_ownership import get_blueprint_column_reports
from pipelinekit.governance.ownership import BLUEPRINTS_DIR, get_ownership_report
from pipelinekit.health import OK, WARNING, HealthCheckResult
from pipelinekit.state import db


class OwnershipHealthChecker:
    """Warn when installed blueprints have no assigned owner."""

    name = "ownership"

    def check(self, cwd: Path | None = None) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing ownership coverage.

        Never raises — an empty or missing blueprints directory is ``ok``.
        """
        base = cwd if cwd is not None else Path.cwd()
        blueprints_dir = str(base / BLUEPRINTS_DIR)
        db_path = str(db.get_db_path(base))

        report = get_ownership_report(blueprints_dir, db_path)
        if report.total_blueprints == 0:
            return HealthCheckResult(self.name, OK, "No blueprints installed.")

        all_names = sorted(
            {owner.blueprint_name for owner in report.owners}
            | set(report.unowned_blueprints)
        )
        column_details, declared, total_columns = self._column_coverage(
            all_names, blueprints_dir, db_path
        )

        if report.unowned_blueprints:
            return HealthCheckResult(
                self.name,
                WARNING,
                f"{len(report.unowned_blueprints)} blueprint(s) have no owner.",
                details=[f"{name}: no owner" for name in report.unowned_blueprints]
                + column_details,
                fix_hint=(
                    "Assign owners with "
                    "'pipelinekit governance owner set <blueprint> "
                    "--name <name> --email <email>'."
                ),
            )

        message = f"All {report.total_blueprints} blueprint(s) have an owner."
        if total_columns:
            message += f" {declared}/{total_columns} contract column(s) declared."
        return HealthCheckResult(
            self.name,
            OK,
            message,
            details=column_details or None,
        )

    @staticmethod
    def _column_coverage(
        blueprint_names: list[str], blueprints_dir: str, db_path: str
    ) -> tuple[list[str], int, int]:
        """Return ``(detail lines, declared columns, total columns)`` for GM-4.

        Blueprints with no contracts contribute nothing — they are not a gap.
        """
        details: list[str] = []
        declared = 0
        total = 0
        for name in blueprint_names:
            for column_report in get_blueprint_column_reports(
                name, blueprints_dir, db_path
            ):
                declared += column_report.owned_columns
                total += column_report.total_columns
                details.append(
                    f"{name}/{column_report.contract_file}: "
                    f"{column_report.owned_columns}/{column_report.total_columns} "
                    "columns declared"
                )
        return details, declared, total
