"""SPEC status drift check (SPEC-012).

Reads ``**Status:**`` headers in ``docs/specifications/`` and compares them
against the set of SPECs known to be implemented. An implemented SPEC still
marked ``Approved`` is drift. ``check()`` never modifies files; ``fix()``
rewrites the status header in place for drifted SPECs only.
"""

from __future__ import annotations

import re
from pathlib import Path

from pipelinekit.health import OK, WARNING, HealthCheckResult

# repo_root/src/pipelinekit/health/specs.py -> parents[3] == repo root
_DEFAULT_SPECS_DIR = Path(__file__).resolve().parents[3] / "docs" / "specifications"

# SPECs whose implementation has shipped — their headers should read Implemented.
_IMPLEMENTED_SPECS = frozenset(
    {
        "SPEC-001",
        "SPEC-002",
        "SPEC-003",
        "SPEC-004",
        "SPEC-006",
        "SPEC-007",
        "SPEC-008",
        "SPEC-009",
        "SPEC-010",
        "SPEC-011",
        # Phase 2 capabilities
        "SPEC-020",  # DC-8 Schema Versioning
        "SPEC-021",  # DC-9 Breaking Change Detection
        "SPEC-022",  # QM-4 Coverage Monitoring
        "SPEC-023",  # GM-1 Ownership Assignment
    }
)

_DRIFT_STATUS = "approved"
_TARGET_STATUS = "Implemented"

_SPEC_ID_RE = re.compile(r"^(SPEC-\d+)", re.IGNORECASE)
# "**Status:** Approved" — captures the prefix and the value separately.
_STATUS_RE = re.compile(r"^(\*\*Status:\*\*\s*)(.+?)\s*$", re.MULTILINE | re.IGNORECASE)


class SpecDriftChecker:
    """Check SPEC status headers against known implementation state."""

    name = "specs"

    def __init__(self, specs_dir: Path | None = None) -> None:
        self.specs_dir = specs_dir if specs_dir is not None else _DEFAULT_SPECS_DIR

    def check(self, specs_dir: Path | None = None) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing SPEC status drift."""
        base = self._resolve(specs_dir)
        if not base.is_dir():
            return HealthCheckResult(
                self.name, OK, "No specifications directory found."
            )

        drifted = self._drifted(base)
        if not drifted:
            return HealthCheckResult(
                self.name, OK, "All SPEC status headers consistent."
            )

        return HealthCheckResult(
            self.name,
            WARNING,
            f"{len(drifted)} SPEC(s) show status drift.",
            details=[
                f"{spec_id}: Approved — should be Implemented" for spec_id in drifted
            ],
            fix_hint="Run 'pipelinekit health specs --fix' to update headers.",
        )

    def fix(self, specs_dir: Path | None = None) -> int:
        """Rewrite drifted ``Approved`` headers to ``Implemented`` in place.

        Returns the number of SPEC files updated.
        """
        base = self._resolve(specs_dir)
        if not base.is_dir():
            return 0

        fixed = 0
        for path in sorted(base.glob("SPEC-*.md")):
            spec_id = self._spec_id(path)
            if spec_id is None or spec_id not in _IMPLEMENTED_SPECS:
                continue
            text = path.read_text(encoding="utf-8")
            new_text = self._rewrite_status(text)
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
                fixed += 1
        return fixed

    def _drifted(self, base: Path) -> list[str]:
        """Return the ids of implemented SPECs still marked ``Approved``."""
        drifted: list[str] = []
        for path in sorted(base.glob("SPEC-*.md")):
            spec_id = self._spec_id(path)
            if spec_id is None or spec_id not in _IMPLEMENTED_SPECS:
                continue
            status = self._status(path)
            if status is not None and status.lower() == _DRIFT_STATUS:
                drifted.append(spec_id)
        return drifted

    def _resolve(self, specs_dir: Path | None) -> Path:
        """Resolve the specs directory, preferring an explicit argument."""
        if specs_dir is not None:
            return specs_dir
        return self.specs_dir

    @staticmethod
    def _spec_id(path: Path) -> str | None:
        """Extract the ``SPEC-NNN`` id from a filename."""
        match = _SPEC_ID_RE.match(path.name)
        return match.group(1).upper() if match else None

    @staticmethod
    def _status(path: Path) -> str | None:
        """Return the first ``**Status:**`` header value, or None."""
        match = _STATUS_RE.search(path.read_text(encoding="utf-8"))
        return match.group(2).strip() if match else None

    @staticmethod
    def _rewrite_status(text: str) -> str:
        """Replace an ``Approved`` status header value with ``Implemented``."""

        def _replace(match: re.Match[str]) -> str:
            value = match.group(2).strip()
            if value.lower() == _DRIFT_STATUS:
                return f"{match.group(1)}{_TARGET_STATUS}"
            return match.group(0)

        # Only rewrite the first status header (the file's own header).
        return _STATUS_RE.sub(_replace, text, count=1)
