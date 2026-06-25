"""Health checks — the programmed Sustainability Policy (SPEC-012).

Each checker returns a ``HealthCheckResult``: a structured, status-coded verdict.
Checks never raise for the conditions they inspect — a missing tool, an empty
project, or an outdated dependency all resolve to a result, not an exception.
This keeps ``pipelinekit health`` non-blocking by default (it exits 0 even with
warnings; only ``--strict`` exits 1).

See: SPEC-012, docs/reference/Sustainability-Policy.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Status vocabulary shared across all checkers and the CLI renderer.
OK = "ok"
WARNING = "warning"
ERROR = "error"
INFO = "info"


@dataclass
class HealthCheckResult:
    """A single health check's verdict.

    ``status`` is one of ``ok | warning | error | info``. ``info`` means the
    check could not run (e.g. a tool is not installed) — it is never a failure.
    """

    name: str
    status: str
    message: str
    details: Optional[list[str]] = None
    fix_hint: Optional[str] = None

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict of the result."""
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details or [],
            "fix_hint": self.fix_hint,
        }
