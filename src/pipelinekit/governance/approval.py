"""GM-3 — approval workflow for pipeline change management (SPEC-031).

Records approval requests and decisions for pipeline changes so organizations
have documented SOC 2 CC8 (Change Management) evidence. Approvers and requests
live in ``state.db`` (``gm_approvers``, ``gm_approval_requests``) —
organizational state, not blueprint state (ADR-032, mirrors ADR-024).

**Record-only:** GM-3 never blocks pipeline execution. It maintains the audit
trail; hard enforcement gates are a future GM-6 (Policy Enforcement) capability.
Purely deterministic — no AI.

See: SPEC-031, ADR-032.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from pipelinekit.core.errors import GovernanceError
from pipelinekit.state import db

_PENDING = "PENDING"
_APPROVED = "APPROVED"
_REJECTED = "REJECTED"


@dataclass
class Approver:
    """The person authorized to approve changes for one blueprint."""

    id: str
    blueprint_name: str
    approver_name: str
    approver_email: str
    created_at: str
    updated_at: str


@dataclass
class ApprovalRequest:
    """A request to approve a pipeline change, and its decision."""

    id: str
    request_code: str  # e.g. "REQ-001"
    blueprint_name: str
    change_description: str
    requested_by: str
    status: str  # "PENDING" | "APPROVED" | "REJECTED"
    decided_by: str | None
    decision_reason: str | None
    created_at: str
    decided_at: str | None


def _utc_now() -> str:
    """Return the current time as a timezone-aware ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _row_to_approver(row: dict) -> Approver:
    """Rebuild an ``Approver`` from a stored ``gm_approvers`` row."""
    return Approver(
        id=row["id"],
        blueprint_name=row["blueprint_name"],
        approver_name=row["approver_name"],
        approver_email=row["approver_email"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_request(row: dict) -> ApprovalRequest:
    """Rebuild an ``ApprovalRequest`` from a ``gm_approval_requests`` row."""
    return ApprovalRequest(
        id=row["id"],
        request_code=row["request_code"],
        blueprint_name=row["blueprint_name"],
        change_description=row["change_description"],
        requested_by=row["requested_by"],
        status=row["status"],
        decided_by=row["decided_by"],
        decision_reason=row["decision_reason"],
        created_at=row["created_at"],
        decided_at=row["decided_at"],
    )


def set_approver(
    blueprint_name: str,
    approver_name: str,
    approver_email: str,
    db_path: str,
) -> Approver:
    """Assign or update the approver for a blueprint.

    Preserves ``id`` and ``created_at`` when updating an existing approver.
    """
    existing = db.get_approver(blueprint_name, db_path)
    now = _utc_now()
    if existing is not None:
        approver_id = existing["id"]
        created_at = existing["created_at"]
    else:
        approver_id = str(uuid.uuid4())
        created_at = now

    approver = Approver(
        id=approver_id,
        blueprint_name=blueprint_name,
        approver_name=approver_name,
        approver_email=approver_email,
        created_at=created_at,
        updated_at=now,
    )
    db.upsert_approver(approver, db_path)
    return approver


def get_approver(blueprint_name: str, db_path: str) -> Approver | None:
    """Return the approver for a blueprint, or None if none is set."""
    row = db.get_approver(blueprint_name, db_path)
    return _row_to_approver(row) if row is not None else None


def create_request(
    blueprint_name: str,
    change_description: str,
    requested_by: str,
    db_path: str,
) -> ApprovalRequest:
    """Create a PENDING approval request with a sequential ``REQ-NNN`` code."""
    next_number = db.count_approval_requests(db_path) + 1
    request = ApprovalRequest(
        id=str(uuid.uuid4()),
        request_code=f"REQ-{next_number:03d}",
        blueprint_name=blueprint_name,
        change_description=change_description,
        requested_by=requested_by,
        status=_PENDING,
        decided_by=None,
        decision_reason=None,
        created_at=_utc_now(),
        decided_at=None,
    )
    db.insert_approval_request(request, db_path)
    return request


def _decide(
    request_code: str,
    status: str,
    decided_by: str,
    reason: str | None,
    db_path: str,
) -> ApprovalRequest:
    """Shared decision path for approve/reject. Validates state, then updates.

    Raises:
        GovernanceError: ``PK-GM-005`` if the request does not exist,
            ``PK-GM-006`` if it has already been decided.
    """
    row = db.get_request_by_code(request_code, db_path)
    if row is None:
        raise GovernanceError(
            "PK-GM-005",
            f"Approval request not found: {request_code}",
            {"request_code": request_code},
        )
    if row["status"] != _PENDING:
        raise GovernanceError(
            "PK-GM-006",
            f"Request {request_code} already decided ({row['status']}).",
            {"request_code": request_code, "status": row["status"]},
        )

    decided_at = _utc_now()
    db.update_request_status(
        request_code, status, decided_by, reason, decided_at, db_path
    )
    updated = db.get_request_by_code(request_code, db_path)
    # updated is not None: we just wrote it.
    return _row_to_request(updated) if updated is not None else _row_to_request(row)


def approve_request(
    request_code: str, decided_by: str, db_path: str
) -> ApprovalRequest:
    """Approve a PENDING request.

    Raises:
        GovernanceError: ``PK-GM-005`` if not found, ``PK-GM-006`` if decided.
    """
    return _decide(request_code, _APPROVED, decided_by, None, db_path)


def reject_request(
    request_code: str, decided_by: str, reason: str | None, db_path: str
) -> ApprovalRequest:
    """Reject a PENDING request, recording an optional reason.

    Raises:
        GovernanceError: ``PK-GM-005`` if not found, ``PK-GM-006`` if decided.
    """
    return _decide(request_code, _REJECTED, decided_by, reason, db_path)


def get_pending_requests(db_path: str) -> list[ApprovalRequest]:
    """Return every PENDING approval request."""
    return [_row_to_request(row) for row in db.get_pending_requests(db_path)]


def get_all_requests(blueprint_name: str, db_path: str) -> list[ApprovalRequest]:
    """Return every approval request for a blueprint, regardless of status."""
    return [
        _row_to_request(row)
        for row in db.get_all_requests_for_blueprint(blueprint_name, db_path)
    ]
