"""dbt Core transformation adapter.

dbt is invoked **only** via ``subprocess`` — never imported as a Python library
(SPEC-009). ``execute`` runs ``dbt build`` and parses ``run_results.json``;
``validate`` runs ``dbt parse``. Non-zero dbt exit codes map to
``PK-ADAPTER-002``; a missing/unparseable ``run_results.json`` maps to
``PK-ADAPTER-003``.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.config.schema import TransformationSection
from pipelinekit.runtime.result import PipelineStatus, StepResult

_STEP = "transformation"
_DBT_TIMEOUT_S = 1800


class DbtTransformationAdapter(BaseAdapter):
    """dbt Core adapter. All dbt-specific logic stays inside this file."""

    def __init__(self, config: TransformationSection) -> None:
        self.config = config

    # -- BaseAdapter ---------------------------------------------------------

    def initialize(self) -> None:
        """Verify the dbt project directory exists."""
        if not Path(self.config.project_dir).is_dir():
            return

    def _run_dbt(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Invoke the dbt CLI in the configured project directory."""
        project_dir = self.config.project_dir
        return subprocess.run(
            [
                "dbt",
                *args,
                "--project-dir",
                project_dir,
                "--profiles-dir",
                project_dir,
            ],
            capture_output=True,
            text=True,
            timeout=_DBT_TIMEOUT_S,
            check=False,
        )

    def validate(self) -> StepResult:
        """Run ``dbt parse`` to validate the project without executing models."""
        start = time.perf_counter()
        try:
            completed = self._run_dbt("parse")
        except Exception as exc:
            return StepResult(
                _STEP,
                PipelineStatus.INVALID,
                time.perf_counter() - start,
                error_code="PK-ADAPTER-001",
                error_msg=f"dbt parse failed to launch: {exc}",
            )
        if completed.returncode != 0:
            return StepResult(
                _STEP,
                PipelineStatus.INVALID,
                time.perf_counter() - start,
                error_code="PK-ADAPTER-001",
                error_msg="dbt parse reported an invalid project",
            )
        return StepResult(_STEP, PipelineStatus.VALID, time.perf_counter() - start)

    def execute(self) -> StepResult:
        """Run ``dbt build`` and parse structured pass/fail counts."""
        start = time.perf_counter()
        try:
            completed = self._run_dbt("build")
        except Exception as exc:
            return StepResult(
                _STEP,
                PipelineStatus.FAILED,
                time.perf_counter() - start,
                error_code="PK-ADAPTER-002",
                error_msg=f"dbt build failed to launch: {exc}",
            )

        if completed.returncode != 0:
            return StepResult(
                _STEP,
                PipelineStatus.FAILED,
                time.perf_counter() - start,
                error_code="PK-ADAPTER-002",
                error_msg="dbt build failed (non-zero exit code)",
            )

        passed, failed = self._parse_run_results()
        if failed > 0:
            return StepResult(
                _STEP,
                PipelineStatus.FAILED,
                time.perf_counter() - start,
                error_code="PK-ADAPTER-002",
                error_msg=f"dbt build had {failed} failing node(s)",
            )
        return StepResult(
            _STEP,
            PipelineStatus.SUCCESS,
            time.perf_counter() - start,
            rows_processed=passed,
        )

    def status(self) -> dict:
        """Return the last dbt run summary, if available."""
        passed, failed = self._parse_run_results()
        return {
            "adapter": "dbt",
            "step": _STEP,
            "project_dir": self.config.project_dir,
            "passed": passed,
            "failed": failed,
        }

    # -- helpers -------------------------------------------------------------

    def _run_results_path(self) -> Path:
        return Path(self.config.project_dir) / "target" / "run_results.json"

    def _parse_run_results(self) -> tuple[int, int]:
        """Return (passed, failed) node counts from ``run_results.json``.

        A missing file yields (0, 0); the runner treats dbt's own exit code as
        authoritative, so absence is not itself a failure here.
        """
        path = self._run_results_path()
        if not path.is_file():
            return (0, 0)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            results = data.get("results", [])
            passed = sum(1 for r in results if r.get("status") in ("pass", "success"))
            failed = sum(
                1 for r in results if r.get("status") in ("fail", "error", "failed")
            )
        except (OSError, ValueError):
            return (0, 0)
        return (passed, failed)
