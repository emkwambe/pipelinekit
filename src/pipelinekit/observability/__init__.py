"""Observability Management System (OM) — SLO definition and evaluation.

OM-4 (SPEC-025) adds deterministic Service Level Objective definition for
installed blueprints, stored in ``state.db``. SLOs are evaluated against existing
DC (freshness), QM (row counts), and coverage data — no AI, no warehouse. SLO
violations surface as warnings in ``pipelinekit health --strict``.
"""

from __future__ import annotations

from pipelinekit.observability.slo import (
    VALID_SLO_TYPES,
    SLODefinition,
    SLOResult,
    check_slos,
    get_all_slos,
    get_slos,
    remove_slo,
    set_slo,
)

__all__ = [
    "VALID_SLO_TYPES",
    "SLODefinition",
    "SLOResult",
    "set_slo",
    "get_slos",
    "get_all_slos",
    "remove_slo",
    "check_slos",
]
