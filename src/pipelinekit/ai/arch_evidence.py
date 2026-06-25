"""Architecture context collection — read-only input to architectural reasoning.

``ArchitectureContextCollector`` assembles an ``ArchitectureContext`` from
``state.db`` (read-only), the local blueprint registry, and ``docs/decisions/``
(via ``ADRReader``). It never writes state (ADR-015). The context is fully
JSON-serializable so it can be handed to any provider unchanged.

State access mirrors the Phase 4 ``EvidenceCollector``: it opens its own
read-only sqlite connection via the public ``get_db_path`` and never mutates.

See: SPEC-011, ADR-015.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pipelinekit.ai.adr_reader import ADRReader
from pipelinekit.core.errors import ArchitectureError, StateError
from pipelinekit.state import db

# repo_root/src/pipelinekit/ai/arch_evidence.py -> parents[3] == repo root
_DEFAULT_DECISIONS_DIR = Path(__file__).resolve().parents[3] / "docs" / "decisions"

MIN_RUNS = 5
RUN_WINDOW = 30
CONTRACT_WINDOW_DAYS = 30


@dataclass
class ArchitectureContext:
    """Structured, JSON-serializable evidence for architectural reasoning."""

    config: dict = field(default_factory=dict)
    blueprint_metadata: list[dict] = field(default_factory=list)
    adr_summaries: list[dict] = field(default_factory=list)
    run_history: list[dict] = field(default_factory=list)  # last 30 runs
    contract_violations: list[dict] = field(default_factory=list)  # last 30 days
    current_tools: dict = field(default_factory=dict)  # source/dest/transform/quality
    volume_profile: dict = field(default_factory=dict)  # rows/day estimate
    diagnostic_history: list[dict] = field(default_factory=list)  # Phase 4 results

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict of the full context."""
        return asdict(self)


class ArchitectureContextCollector:
    """Assembles ``ArchitectureContext`` from state, blueprints, and ADRs.

    Read-only — never writes to ``state.db`` or any ADR file.
    """

    def __init__(self, decisions_dir: Path | None = None) -> None:
        self.decisions_dir = decisions_dir or _DEFAULT_DECISIONS_DIR

    def collect(self, cwd: Path | None = None) -> ArchitectureContext:
        """Assemble an ``ArchitectureContext`` from local state.

        Raises:
            ArchitectureError: ``PK-ARCH-001`` if collection fails,
                ``PK-ARCH-004`` if fewer than five runs exist in history.
        """
        try:
            db.initialize(cwd)
            run_history = db.get_recent_runs(n=RUN_WINDOW, cwd=cwd)
        except StateError as exc:
            raise ArchitectureError(
                "PK-ARCH-001",
                "Architecture context collection failed reading run history",
                {"detail": str(exc)},
            ) from exc

        if len(run_history) < MIN_RUNS:
            raise ArchitectureError(
                "PK-ARCH-004",
                f"Insufficient run history for analysis: {len(run_history)} runs "
                f"(need at least {MIN_RUNS}).",
                {"runs": len(run_history), "required": MIN_RUNS},
            )

        try:
            contract_violations = self._contract_violations(cwd)
            diagnostic_history = self._diagnostic_history(cwd)
            blueprint_metadata = self._blueprint_metadata(cwd)
            adr_summaries = ADRReader(self.decisions_dir).get_adr_summaries()
            volume_profile = self._volume_profile(run_history)
        except sqlite3.Error as exc:
            raise ArchitectureError(
                "PK-ARCH-001",
                "Architecture context collection failed assembling evidence",
                {"detail": str(exc)},
            ) from exc

        return ArchitectureContext(
            config={},  # filled by the engine from the active config
            blueprint_metadata=blueprint_metadata,
            adr_summaries=adr_summaries,
            run_history=run_history,
            contract_violations=contract_violations,
            current_tools={},  # filled by the engine from the active config
            volume_profile=volume_profile,
            diagnostic_history=diagnostic_history,
        )

    def _connect(self, cwd: Path | None) -> sqlite3.Connection:
        conn = sqlite3.connect(db.get_db_path(cwd))
        conn.row_factory = sqlite3.Row
        return conn

    def _contract_violations(self, cwd: Path | None) -> list[dict]:
        """Return recent contract violations within the 30-day window."""
        cutoff = self._cutoff(CONTRACT_WINDOW_DAYS)
        with self._connect(cwd) as conn:
            rows = conn.execute(
                """
                SELECT run_id, table_name, status, violation_count, checked_at
                FROM contract_results
                WHERE violation_count > 0 AND checked_at >= ?
                ORDER BY checked_at DESC
                LIMIT 50
                """,
                (cutoff,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _diagnostic_history(self, cwd: Path | None) -> list[dict]:
        """Return recent Phase 4 diagnostic results — what keeps failing."""
        with self._connect(cwd) as conn:
            rows = conn.execute(
                """
                SELECT run_id, status, finding_type, confidence, diagnosed_at
                FROM diagnostic_results
                ORDER BY diagnosed_at DESC
                LIMIT ?
                """,
                (RUN_WINDOW,),
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _blueprint_metadata(cwd: Path | None) -> list[dict]:
        """Return metadata for installed blueprints (read-only). Never fatal."""
        try:
            from pipelinekit.blueprints.registry import BlueprintRegistry

            base = cwd if cwd is not None else Path.cwd()
            registry = BlueprintRegistry(base / "blueprints")
            return [bp.model_dump() for bp in registry.list()]
        except Exception:
            return []

    @staticmethod
    def _volume_profile(run_history: list[dict]) -> dict:
        """Estimate throughput characteristics from run timestamps.

        State stores no row counts, so this reports an honest run-rate profile
        (runs/day, success/failure split) rather than fabricated row volumes.
        """
        timestamps = sorted(
            ts
            for ts in (
                ArchitectureContextCollector._parse_ts(r.get("started_at"))
                for r in run_history
            )
            if ts is not None
        )
        total = len(run_history)
        failed = sum(1 for r in run_history if r.get("status") == "failed")
        succeeded = sum(
            1 for r in run_history if r.get("status") in ("success", "completed")
        )

        if len(timestamps) >= 2:
            span_seconds = (timestamps[-1] - timestamps[0]).total_seconds()
            window_days = max(span_seconds / 86400.0, 1.0 / 24.0)
        else:
            window_days = 1.0 / 24.0

        return {
            "runs_observed": total,
            "window_days": round(window_days, 3),
            "runs_per_day": round(total / window_days, 2) if window_days else total,
            "failed_runs": failed,
            "succeeded_runs": succeeded,
            "failure_rate": round(failed / total, 3) if total else 0.0,
        }

    @staticmethod
    def _parse_ts(value: object) -> datetime | None:
        """Parse an ISO 8601 UTC timestamp string, tolerating a trailing Z."""
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return None

    @staticmethod
    def _cutoff(days: int) -> str:
        """Return the ISO 8601 UTC cutoff string ``days`` before now."""
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - days * 86400
        return datetime.fromtimestamp(cutoff, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
