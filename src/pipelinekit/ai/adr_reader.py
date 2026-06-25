"""ADR reader — parses ``docs/decisions/`` for compliance checking (SPEC-011).

Read-only: ``ADRReader`` never writes, creates, or deletes ADR files (ADR-015).
Parsing is defensive — a malformed or unreadable file is skipped with a warning,
never raised, and never treated as a violation. A missing ``docs/decisions/``
directory returns an empty list. Catastrophic parse failures map to
``PK-ARCH-003`` (kept available; individual-file failures are skipped).

ADR markdown comes in two historical shapes in this repo:

    # ADR-001: Drop Airbyte        and     # ADR-015: Architecture Intelligence
    Status: Accepted                       **Status:** Accepted

Both are parsed by the same tolerant logic below.
"""

from __future__ import annotations

import re
from pathlib import Path

# "# ADR-015: Architecture Intelligence" / "# ADR-001 - Drop Airbyte"
_HEADING_RE = re.compile(r"^#\s*(ADR-\d+)\s*[:\-—]?\s*(.*)$", re.IGNORECASE)
# "**Status:** Accepted" / "Status: Accepted"
_STATUS_RE = re.compile(
    r"^\s*\*{0,2}status\*{0,2}\s*:\s*\*{0,2}\s*([A-Za-z]+)", re.IGNORECASE
)
# "## Decision" section heading
_SECTION_RE = re.compile(r"^#{1,6}\s*(.+?)\s*$")

_SUMMARY_LIMIT = 320


class ADRReader:
    """Reads and parses ADR files for architectural compliance checking.

    Reads from ``docs/decisions/`` — never modifies ADR files. Returns
    structured summaries suitable for an LLM context window.
    """

    def __init__(self, decisions_dir: Path) -> None:
        self.decisions_dir = decisions_dir
        self.warnings: list[str] = []

    def read_all(self) -> list[dict]:
        """Return structured summaries of all ADR markdown files.

        Never raises: a missing directory yields ``[]``; a malformed file is
        skipped and recorded in ``self.warnings``.
        """
        self.warnings = []
        if not self.decisions_dir.is_dir():
            return []
        summaries: list[dict] = []
        for path in sorted(self.decisions_dir.glob("*.md")):
            parsed = self._parse_file(path)
            if parsed is not None:
                summaries.append(parsed)
            else:
                self.warnings.append(f"Skipped unparseable ADR file: {path.name}")
        return summaries

    def get_adr_summaries(self) -> list[dict]:
        """Return concise summaries suitable for an LLM context window."""
        summaries: list[dict] = []
        for adr in self.read_all():
            summaries.append(
                {
                    "adr_id": adr["adr_id"],
                    "title": adr["title"],
                    "status": adr["status"],
                    "summary": adr["decision"][:_SUMMARY_LIMIT],
                }
            )
        return summaries

    def _parse_file(self, path: Path) -> dict | None:
        """Parse one ADR file into a summary dict, or None if malformed."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None

        adr_id: str | None = None
        title = ""
        status = "unknown"
        for line in text.splitlines():
            heading = _HEADING_RE.match(line)
            if heading and adr_id is None:
                adr_id = heading.group(1).upper()
                title = heading.group(2).strip()
                continue
            status_match = _STATUS_RE.match(line)
            if status_match and status == "unknown":
                status = status_match.group(1).strip().lower()

        if adr_id is None:
            return None  # not a recognizable ADR — skip, do not raise

        return {
            "adr_id": adr_id,
            "title": title,
            "status": status,
            "decision": self._extract_decision(text),
            "path": path.name,
        }

    @staticmethod
    def _extract_decision(text: str) -> str:
        """Return the body of the ``## Decision`` section, else the first prose."""
        lines = text.splitlines()
        decision_lines: list[str] = []
        in_decision = False
        for line in lines:
            section = _SECTION_RE.match(line)
            if section:
                heading = section.group(1).strip().lower()
                if heading == "decision":
                    in_decision = True
                    continue
                if in_decision:
                    break  # next section ends the Decision block
                continue
            if in_decision and line.strip():
                decision_lines.append(line.strip())
        if decision_lines:
            return " ".join(decision_lines)
        # Fallback: first non-heading, non-metadata prose line.
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith(("#", "**", "-", "|", ">")):
                return stripped
        return ""
