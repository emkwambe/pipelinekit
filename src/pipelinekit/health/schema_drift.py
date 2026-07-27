"""Schema-drift health check — surfaces QM-7 contract/schema drift (SPEC-029).

Reports tables whose ``schema.yml`` has drifted from their contract snapshot.
Drift is a ``warning``; CLEAN and NO_BASELINE (no snapshot taken yet) are ``ok``
— NO_BASELINE is not a failure. Never raises; an unexpected failure degrades to
``info``.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.blueprints.registry import BLUEPRINTS_DIR
from pipelinekit.health import INFO, OK, WARNING, HealthCheckResult
from pipelinekit.state import db


def _blueprint_names(blueprints_dir: Path) -> list[str]:
    """Return the names of installed blueprints (immediate subdirectories)."""
    if not blueprints_dir.is_dir():
        return []
    return sorted(
        entry.name
        for entry in blueprints_dir.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )


class SchemaDriftHealthChecker:
    """Warn when any table has drifted from its contract snapshot."""

    name = "schema_drift"

    def check(self, cwd: Path | None = None) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing QM-7 schema drift."""
        try:
            base = cwd if cwd is not None else Path.cwd()
            blueprints_dir = base / BLUEPRINTS_DIR
            db_path = str(db.get_db_path(base))

            names = _blueprint_names(blueprints_dir)
            if not names:
                return HealthCheckResult(self.name, OK, "No blueprints installed.")

            from pipelinekit.quality.drift import check_blueprint_drift

            drifted: list[str] = []
            details: list[str] = []
            for bp_name in names:
                try:
                    for result in check_blueprint_drift(
                        bp_name, str(blueprints_dir / bp_name), db_path
                    ):
                        details.append(
                            f"{bp_name}/{result.table_name}: {result.status}"
                        )
                        if result.status == "DRIFTED":
                            summary = ", ".join(
                                f"{item.drift_type.value}: {item.name}"
                                for item in result.drift_items
                            )
                            drifted.append(f"{bp_name}/{result.table_name}: {summary}")
                except Exception:
                    details.append(f"{bp_name}: drift check unavailable")

            if drifted:
                return HealthCheckResult(
                    self.name,
                    WARNING,
                    f"{len(drifted)} table(s) with schema drift.",
                    details=drifted,
                    fix_hint="Run 'pipelinekit quality check-drift' for details.",
                )
            return HealthCheckResult(
                self.name, OK, "No schema drift detected.", details=details
            )
        except Exception as exc:
            return HealthCheckResult(
                self.name, INFO, f"Schema drift check unavailable: {exc}"
            )
