"""Ownership coverage check — surfaces unowned blueprints (GM-1, SPEC-023).

Reports which installed blueprints have no owner assigned in ``state.db``.
Missing ownership is a governance gap, not a failure: this check returns
``warning`` (never ``error``) so ``health --strict`` flags it without treating
it as a hard fault (ADR-024).
"""

from __future__ import annotations

from pathlib import Path

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

        if report.unowned_blueprints:
            return HealthCheckResult(
                self.name,
                WARNING,
                f"{len(report.unowned_blueprints)} blueprint(s) have no owner.",
                details=[f"{name}: no owner" for name in report.unowned_blueprints],
                fix_hint=(
                    "Assign owners with "
                    "'pipelinekit governance owner set <blueprint> "
                    "--name <name> --email <email>'."
                ),
            )

        return HealthCheckResult(
            self.name,
            OK,
            f"All {report.total_blueprints} blueprint(s) have an owner.",
        )
