"""Governance Management System (GM) — ownership and accountability.

GM-1 (SPEC-023) adds deterministic ownership assignment for installed
blueprints, stored in ``state.db``. No AI. Ownership gaps surface as warnings in
``pipelinekit health --strict``.
"""

from __future__ import annotations

from pipelinekit.governance.ownership import (
    BlueprintOwner,
    OwnershipReport,
    get_owner,
    get_ownership_report,
    remove_owner,
    set_owner,
    validate_email,
)

__all__ = [
    "BlueprintOwner",
    "OwnershipReport",
    "set_owner",
    "get_owner",
    "get_ownership_report",
    "remove_owner",
    "validate_email",
]
