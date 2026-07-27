"""SLO-violations health check — surfaces breached OM-4 SLOs (SPEC-031).

Reports any Service Level Objective currently ``VIOLATED``. A violation is an
``error``; all SLOs OK / NO_DATA (or no SLOs defined) are ``ok`` — ``NO_DATA``
means the pipeline has not run yet, which is not a failure. Never raises; an
unexpected failure degrades to ``info``.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.health import ERROR, INFO, OK, HealthCheckResult
from pipelinekit.state import db


class SLOViolationsHealthChecker:
    """Fail when any defined SLO is currently violated."""

    name = "slo_violations"

    def check(self, cwd: Path | None = None) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing OM-4 SLO compliance."""
        try:
            base = cwd if cwd is not None else Path.cwd()
            db_path = str(db.get_db_path(base))

            from pipelinekit.observability.slo import check_slos, get_all_slos

            all_slos = get_all_slos(db_path)
            if not all_slos:
                return HealthCheckResult(
                    self.name,
                    OK,
                    "No SLOs defined.",
                    fix_hint="Define SLOs with 'pipelinekit observability slo set'.",
                )

            blueprints = sorted({slo.blueprint_name for slo in all_slos})
            violations: list[str] = []
            details: list[str] = []
            for bp_name in blueprints:
                try:
                    for result in check_slos(bp_name, db_path):
                        details.append(
                            f"{bp_name}/{result.slo.table_name} "
                            f"{result.slo.slo_type}: {result.status}"
                        )
                        if result.status == "VIOLATED":
                            violations.append(
                                f"{bp_name}/{result.slo.table_name} "
                                f"{result.slo.slo_type}: "
                                f"current={result.current_value}, "
                                f"threshold={result.slo.threshold}"
                            )
                except Exception:
                    details.append(f"{bp_name}: SLO check unavailable")

            if violations:
                return HealthCheckResult(
                    self.name,
                    ERROR,
                    f"{len(violations)} SLO violation(s) detected.",
                    details=violations,
                    fix_hint="Run 'pipelinekit observability slo check' for details.",
                )
            return HealthCheckResult(
                self.name,
                OK,
                f"All {len(all_slos)} SLO(s) compliant or awaiting data.",
                details=details,
            )
        except Exception as exc:
            return HealthCheckResult(
                self.name, INFO, f"SLO violation check unavailable: {exc}"
            )
