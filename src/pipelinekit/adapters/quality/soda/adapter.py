"""Soda quality-check adapter.

Runs Soda checks from ``config.checks_dir`` and returns structured pass/fail/warn
counts. **All Soda imports stay inside this file** (lazily, inside ``execute``)
— never in runtime, cli, config, state, or core (SPEC-009).

Soda failures map to ``PK-ADAPTER-002``; a missing checks directory maps to
``PK-ADAPTER-001``.
"""

from __future__ import annotations

import time
from pathlib import Path

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.config.schema import QualitySection
from pipelinekit.runtime.result import PipelineStatus, StepResult

_STEP = "quality"


class SodaQualityAdapter(BaseAdapter):
    """Soda adapter. All Soda-specific logic stays inside this file."""

    def __init__(self, config: QualitySection) -> None:
        self.config = config
        self._last_summary: dict = {}

    # -- BaseAdapter ---------------------------------------------------------

    def initialize(self) -> None:
        """Verify the checks directory exists."""
        if not Path(self.config.checks_dir).is_dir():
            return

    def validate(self) -> StepResult:
        """Confirm the checks directory exists without executing checks."""
        start = time.perf_counter()
        if not Path(self.config.checks_dir).is_dir():
            return StepResult(
                _STEP,
                PipelineStatus.INVALID,
                time.perf_counter() - start,
                error_code="PK-ADAPTER-001",
                error_msg=f"Checks directory not found: {self.config.checks_dir}",
            )
        return StepResult(_STEP, PipelineStatus.VALID, time.perf_counter() - start)

    def execute(self) -> StepResult:
        """Run Soda checks and report pass/fail/warn counts."""
        start = time.perf_counter()
        try:
            from soda.scan import Scan  # type: ignore  # provider lib: treated as Any

            scan = Scan()
            scan.add_sodacl_yaml_files(self.config.checks_dir)
            scan.execute()
            passed, failed, warned = self._count_outcomes(scan)
        except Exception as exc:
            return StepResult(
                _STEP,
                PipelineStatus.FAILED,
                time.perf_counter() - start,
                error_code="PK-ADAPTER-002",
                error_msg=f"Soda scan failed: {exc}",
            )

        self._last_summary = {"passed": passed, "failed": failed, "warned": warned}
        if failed > 0:
            return StepResult(
                _STEP,
                PipelineStatus.FAILED,
                time.perf_counter() - start,
                rows_processed=passed,
                error_code="PK-ADAPTER-002",
                error_msg=f"Soda reported {failed} failing check(s)",
            )
        return StepResult(
            _STEP,
            PipelineStatus.SUCCESS,
            time.perf_counter() - start,
            rows_processed=passed,
        )

    def status(self) -> dict:
        """Return the last Soda scan summary."""
        return {
            "adapter": "soda",
            "step": _STEP,
            "checks_dir": self.config.checks_dir,
            **self._last_summary,
        }

    # -- Soda result parsing -------------------------------------------------

    @staticmethod
    def _count_outcomes(scan: object) -> tuple[int, int, int]:
        """Count (passed, failed, warned) from a Soda scan's results.

        soda-core removed ``get_checks_pass_count``/``fail_count``/``warn_count``;
        the public ``get_scan_results()`` carries each check's ``outcome``
        (``CheckOutcome``: ``pass`` | ``warn`` | ``fail``). Outcomes are
        normalized to lower-case strings so the count is tolerant of either the
        serialized string form or an enum. Missing/empty results count as zero —
        no checks ran.
        """
        get_results = getattr(scan, "get_scan_results", None)
        results = get_results() if callable(get_results) else {}
        checks = results.get("checks") or [] if isinstance(results, dict) else []

        passed = failed = warned = 0
        for check in checks:
            if not isinstance(check, dict):
                continue
            outcome = check.get("outcome")
            outcome = getattr(outcome, "value", outcome)
            outcome = str(outcome).lower() if outcome is not None else ""
            if outcome == "pass":
                passed += 1
            elif outcome == "fail":
                failed += 1
            elif outcome == "warn":
                warned += 1
        return passed, failed, warned
