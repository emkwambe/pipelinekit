"""Governance Management System (GM) — ownership, naming, and approvals.

GM-1 (SPEC-023) adds deterministic ownership assignment for installed
blueprints, stored in ``state.db``. GM-2 (SPEC-028) adds regex-based naming
convention enforcement. GM-3 (SPEC-031) adds a record-only approval workflow for
pipeline changes. GM-4 (SPEC-032) extends ownership from the blueprint down to
the column level. No AI. Governance gaps surface as warnings — never as blockers.
"""

from __future__ import annotations

from pipelinekit.governance.approval import (
    ApprovalRequest,
    Approver,
    approve_request,
    create_request,
    get_all_requests,
    get_approver,
    get_pending_requests,
    reject_request,
    set_approver,
)
from pipelinekit.governance.column_ownership import (
    ColumnOwner,
    ColumnOwnershipReport,
    get_all_column_owners,
    get_blueprint_column_reports,
    get_column_owner,
    get_column_owners_for_contract,
    get_column_ownership_report,
    get_contract_columns,
    list_contract_files,
    remove_column_owner,
    set_column_owner,
)
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
    # GM-3 — approval workflow (SPEC-031)
    "Approver",
    "ApprovalRequest",
    "set_approver",
    "get_approver",
    "create_request",
    "approve_request",
    "reject_request",
    "get_pending_requests",
    "get_all_requests",
    # GM-4 — column-level domain ownership (SPEC-032)
    "ColumnOwner",
    "ColumnOwnershipReport",
    "set_column_owner",
    "get_column_owner",
    "get_all_column_owners",
    "get_column_owners_for_contract",
    "get_column_ownership_report",
    "get_blueprint_column_reports",
    "get_contract_columns",
    "list_contract_files",
    "remove_column_owner",
]
