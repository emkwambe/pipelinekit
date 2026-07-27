"""Volume-anomaly health check — surfaces abnormal row counts (QM-6, SPEC-024).

Reports tables whose latest row count deviates sharply from their rolling
baseline. An active anomaly is a ``warning``; tables that are OK or still
ESTABLISHING a baseline (and blueprints with no history) are ``ok``. Never
raises; an unexpected failure degrades to ``info``.
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


class VolumeAnomaliesHealthChecker:
    """Warn when any table shows an active volume anomaly."""

    name = "volume_anomalies"

    def check(self, cwd: Path | None = None) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing QM-6 volume anomalies."""
        try:
            base = cwd if cwd is not None else Path.cwd()
            blueprints_dir = base / BLUEPRINTS_DIR
            db_path = str(db.get_db_path(base))

            from pipelinekit.quality.anomaly import check_volume_anomalies

            anomalies: list[str] = []
            details: list[str] = []
            checked = 0
            for bp_name in _blueprint_names(blueprints_dir):
                try:
                    for table in db.get_all_tables_for_blueprint(bp_name, db_path):
                        history = db.get_row_count_history(bp_name, table, 1, db_path)
                        if not history:
                            continue
                        current = {table: history[0]["row_count"]}
                        for result in check_volume_anomalies(bp_name, current, db_path):
                            checked += 1
                            details.append(f"{bp_name}/{table}: {result.status}")
                            if result.is_anomaly:
                                anomalies.append(
                                    f"{bp_name}/{table}: "
                                    f"{result.current_count:,} rows "
                                    f"({result.deviation_pct:+.1f}% from baseline)"
                                )
                except Exception:
                    details.append(f"{bp_name}: anomaly check unavailable")

            if not checked:
                return HealthCheckResult(
                    self.name,
                    OK,
                    "No row count history.",
                    fix_hint=(
                        "Record counts with 'pipelinekit quality record-counts' "
                        "after pipeline runs."
                    ),
                )
            if anomalies:
                return HealthCheckResult(
                    self.name,
                    WARNING,
                    f"{len(anomalies)} volume anomaly(ies) detected.",
                    details=anomalies,
                    fix_hint="Run 'pipelinekit quality check-anomalies' for details.",
                )
            return HealthCheckResult(
                self.name,
                OK,
                f"No volume anomalies detected across {checked} table(s).",
                details=details,
            )
        except Exception as exc:
            return HealthCheckResult(
                self.name, INFO, f"Volume anomaly check unavailable: {exc}"
            )
