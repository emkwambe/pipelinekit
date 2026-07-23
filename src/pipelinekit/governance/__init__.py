"""Governance Management System (GM) — ownership and naming standards.

GM-1 (SPEC-023) adds deterministic ownership assignment for installed
blueprints, stored in ``state.db``. GM-2 (SPEC-028) adds regex-based naming
convention enforcement. No AI. Governance gaps surface as warnings — never as
blockers.
"""

from __future__ import annotations

from pipelinekit.governance.convention import (
    VALID_SCOPES,
    ConventionCheckResult,
    ConventionViolation,
    NamingConvention,
    add_convention,
    check_blueprint_conventions,
    get_conventions,
    remove_convention,
)
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
    # GM-2 — naming convention enforcement (SPEC-028)
    "VALID_SCOPES",
    "NamingConvention",
    "ConventionViolation",
    "ConventionCheckResult",
    "add_convention",
    "get_conventions",
    "remove_convention",
    "check_blueprint_conventions",
]
