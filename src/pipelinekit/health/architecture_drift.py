"""Architecture-drift health check — surfaces broken AM-5 dependencies (SPEC-037).

Reports documented blueprint dependencies (AM-4) that no longer hold. A broken
dependency (``DEPENDENCY_BROKEN`` / ``BLUEPRINT_MISSING``) is an ``error``; all
dependencies valid — or none defined — is ``ok``. Never raises; an unexpected
failure degrades to ``info``.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.blueprints.registry import BLUEPRINTS_DIR
from pipelinekit.health import ERROR, INFO, OK, HealthCheckResult
from pipelinekit.state import db


class ArchitectureDriftHealthChecker:
    """Fail when any documented blueprint dependency is broken."""

    name = "architecture_drift"

    def check(self, cwd: Path | None = None) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing AM-5 architecture drift."""
        try:
            base = cwd if cwd is not None else Path.cwd()
            blueprints_dir = str(base / BLUEPRINTS_DIR)
            db_path = str(db.get_db_path(base))

            from pipelinekit.architecture.drift import detect_architecture_drift

            report = detect_architecture_drift(blueprints_dir, db_path)

            if report.total_dependencies == 0:
                return HealthCheckResult(
                    self.name,
                    OK,
                    "No dependencies defined.",
                    fix_hint=(
                        "Document dependencies with "
                        "'pipelinekit architect dependency add'."
                    ),
                )

            if report.drifted_dependencies:
                details = [
                    f"{d.from_blueprint} → {d.to_blueprint}: {d.drift_type}"
                    for d in report.drifted_dependencies
                ]
                return HealthCheckResult(
                    self.name,
                    ERROR,
                    f"{len(report.drifted_dependencies)} dependency(ies) broken.",
                    details=details,
                    fix_hint="Run 'pipelinekit architect drift' for details.",
                )

            return HealthCheckResult(
                self.name,
                OK,
                f"All {report.total_dependencies} dependency(ies) valid.",
                details=[f"{report.clean_dependencies} clean"],
            )
        except Exception as exc:
            return HealthCheckResult(
                self.name, INFO, f"Architecture drift check unavailable: {exc}"
            )
