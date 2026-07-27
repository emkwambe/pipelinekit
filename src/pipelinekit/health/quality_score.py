"""Quality-score health check — surfaces low QM-8 composite scores (SPEC-030).

Reports each installed blueprint's QM-8 composite quality score. A blueprint
scoring Poor (<50) is an ``error``; Fair (<75) is a ``warning``; Good/Excellent
(and blueprints with no data) are ``ok``. Never raises — any unexpected failure
degrades to ``info`` (the check could not run), never a hard fault.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.blueprints.registry import BLUEPRINTS_DIR
from pipelinekit.health import ERROR, INFO, OK, WARNING, HealthCheckResult
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


class QualityScoreHealthChecker:
    """Flag blueprints whose QM-8 composite quality score is Fair or Poor."""

    name = "quality_score"

    def check(self, cwd: Path | None = None) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing QM-8 quality scores."""
        try:
            base = cwd if cwd is not None else Path.cwd()
            blueprints_dir = base / BLUEPRINTS_DIR
            db_path = str(db.get_db_path(base))

            names = _blueprint_names(blueprints_dir)
            if not names:
                return HealthCheckResult(self.name, OK, "No blueprints installed.")

            from pipelinekit.quality.scorecard import compute_blueprint_score

            poor: list[str] = []
            fair: list[str] = []
            details: list[str] = []
            for name in names:
                try:
                    score = compute_blueprint_score(
                        name, str(blueprints_dir / name), db_path
                    )
                    details.append(
                        f"{name}: {score.composite_score:.0f}/100 ({score.rating})"
                    )
                    if score.composite_score < 50:
                        poor.append(name)
                    elif score.composite_score < 75:
                        fair.append(name)
                except Exception:
                    details.append(f"{name}: score unavailable")

            if poor:
                return HealthCheckResult(
                    self.name,
                    ERROR,
                    f"{len(poor)} blueprint(s) scoring Poor (<50).",
                    details=details,
                    fix_hint="Run 'pipelinekit quality scorecard' for details.",
                )
            if fair:
                return HealthCheckResult(
                    self.name,
                    WARNING,
                    f"{len(fair)} blueprint(s) scoring Fair (<75).",
                    details=details,
                    fix_hint="Run 'pipelinekit quality scorecard' for details.",
                )
            return HealthCheckResult(
                self.name,
                OK,
                f"All {len(names)} blueprint(s) scoring Good or better.",
                details=details,
            )
        except Exception as exc:
            return HealthCheckResult(
                self.name, INFO, f"Quality score check unavailable: {exc}"
            )
