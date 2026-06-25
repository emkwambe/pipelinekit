"""Evidence collection — the structured, read-only input to every AI diagnosis.

``EvidenceCollector`` assembles an ``EvidencePackage`` from ``state.db``. It is
**read-only**: it never writes state. Evidence is fully JSON-serializable so it
can be handed to any provider unchanged (SPEC-005).

State access note: the existing ``state/db.py`` exposes ``get_db_path`` and
``get_recent_runs`` but no by-id readers, and Phase 4 may only add the
``diagnostic_results`` writer to that module. The collector therefore opens its
own **read-only** sqlite connection via the public ``get_db_path`` — it is the
evidence subsystem whose sole job is reading state, and it never mutates it.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pipelinekit.core.errors import DiagnosticsError
from pipelinekit.state import db


@dataclass
class EvidencePackage:
    """Structured, JSON-serializable evidence for one pipeline run."""

    run_id: str
    pipeline_name: str
    pipeline_result: dict
    step_results: list[dict] = field(default_factory=list)
    contract_results: list[dict] = field(default_factory=list)
    validation_results: list[dict] = field(default_factory=list)
    recent_runs: list[dict] = field(default_factory=list)
    config_snapshot: dict = field(default_factory=dict)
    error_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict of the full package."""
        return asdict(self)


class EvidenceCollector:
    """Assembles evidence from ``state.db``. Read-only — never writes."""

    def _connect(self, cwd: Path | None) -> sqlite3.Connection:
        conn = sqlite3.connect(db.get_db_path(cwd))
        conn.row_factory = sqlite3.Row
        return conn

    def get_most_recent_run_id(self, cwd: Path | None = None) -> str:
        """Return the id of the most recent pipeline run.

        Raises:
            DiagnosticsError: ``PK-DIAG-001`` if no runs exist.
        """
        runs = db.get_recent_runs(n=1, cwd=cwd)
        if not runs:
            raise DiagnosticsError(
                "PK-DIAG-001", "No pipeline runs found in state.db", {}
            )
        return str(runs[0]["id"])

    def collect(self, run_id: str, cwd: Path | None = None) -> EvidencePackage:
        """Assemble an ``EvidencePackage`` for ``run_id`` from state.db.

        Raises:
            DiagnosticsError: ``PK-DIAG-001`` if the run is not found,
                ``PK-DIAG-002`` if evidence cannot be read.
        """
        db.initialize(cwd)
        try:
            with self._connect(cwd) as conn:
                run_row = conn.execute(
                    "SELECT * FROM pipeline_runs WHERE id = ?", (run_id,)
                ).fetchone()
                if run_row is None:
                    raise DiagnosticsError(
                        "PK-DIAG-001",
                        f"Run id not found in state.db: {run_id}",
                        {"run_id": run_id},
                    )
                pipeline_result = dict(run_row)

                contract_rows = conn.execute(
                    "SELECT * FROM contract_results WHERE run_id = ?", (run_id,)
                ).fetchall()
                validation_rows = conn.execute(
                    "SELECT * FROM validation_runs ORDER BY ran_at DESC LIMIT 5"
                ).fetchall()
        except sqlite3.Error as exc:
            raise DiagnosticsError(
                "PK-DIAG-002",
                f"Evidence collection failed for run {run_id}",
                {"run_id": run_id, "detail": str(exc)},
            ) from exc

        contract_results = [self._row_with_json(r, "violations") for r in contract_rows]
        validation_results = [self._row_with_json(r, "errors") for r in validation_rows]
        recent_runs = db.get_recent_runs(n=5, cwd=cwd)

        return EvidencePackage(
            run_id=run_id,
            pipeline_name=str(pipeline_result.get("pipeline", "")),
            pipeline_result=pipeline_result,
            step_results=[],  # per-step rows are not persisted in Phase 2 state
            contract_results=contract_results,
            validation_results=validation_results,
            recent_runs=recent_runs,
            config_snapshot={},  # filled by the engine from the active config
            error_codes=self._error_codes(pipeline_result, contract_results),
        )

    @staticmethod
    def _row_with_json(row: sqlite3.Row, json_field: str) -> dict:
        """Convert a row to a dict, parsing one embedded JSON column."""
        data = dict(row)
        raw = data.get(json_field)
        if isinstance(raw, str) and raw:
            try:
                data[json_field] = json.loads(raw)
            except ValueError:
                pass
        return data

    @staticmethod
    def _error_codes(pipeline_result: dict, contract_results: list[dict]) -> list[str]:
        """Collect all distinct PK-* codes referenced by this run."""
        codes: list[str] = []
        run_code = pipeline_result.get("error_code")
        if run_code:
            codes.append(str(run_code))
        for cr in contract_results:
            violations = cr.get("violations")
            if isinstance(violations, list):
                for v in violations:
                    code = v.get("error_code") if isinstance(v, dict) else None
                    if code:
                        codes.append(str(code))
        # Preserve order, drop duplicates.
        seen: set[str] = set()
        unique: list[str] = []
        for code in codes:
            if code not in seen:
                seen.add(code)
                unique.append(code)
        return unique
