"""Test suite status check (SPEC-012).

Reports the coverage percentage from the last run's ``.coverage`` file. Does
not re-run the suite by default (slow). If no ``.coverage`` file exists the
check resolves to ``info`` — tests have simply not been run yet.
"""

from __future__ import annotations

import io
from pathlib import Path

from pipelinekit.health import INFO, OK, HealthCheckResult

COVERAGE_FILE = ".coverage"


class TestsChecker:
    """Report the last test run's coverage from the ``.coverage`` file."""

    name = "tests"

    def check(self, cwd: Path | None = None) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing the last test run.

        Never raises — unreadable coverage data resolves to ``info``.
        """
        base = cwd if cwd is not None else Path.cwd()
        coverage_file = base / COVERAGE_FILE
        if not coverage_file.is_file():
            return HealthCheckResult(
                self.name,
                INFO,
                "No coverage data — tests have not been run yet.",
                fix_hint="Run 'pytest --cov=src/pipelinekit' to record coverage.",
            )

        try:
            import coverage  # noqa: PLC0415 — dev tool imported lazily

            cov = coverage.Coverage(data_file=str(coverage_file))
            cov.load()
            total = cov.report(file=io.StringIO())
        except Exception as exc:  # coverage raises bare exceptions on bad data
            return HealthCheckResult(
                self.name,
                INFO,
                "Coverage data could not be read.",
                details=[str(exc)],
                fix_hint="Run 'pytest --cov=src/pipelinekit' to refresh coverage.",
            )

        return HealthCheckResult(
            self.name,
            OK,
            f"Last run coverage: {total:.2f}%.",
        )
