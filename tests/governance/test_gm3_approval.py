"""Tests for GM-3 approval workflow (SPEC-031).

Deterministic, no AI, record-only. Every test uses a ``tmp_path`` SQLite database
— the real ``blueprints/`` directory and project ``state.db`` are never touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pipelinekit.core.errors import GovernanceError
from pipelinekit.governance.approval import (
    Approver,
    approve_request,
    create_request,
    get_all_requests,
    get_pending_requests,
    reject_request,
    set_approver,
)


def _db(tmp_path: Path) -> str:
    """Return a path to an isolated state database for this test."""
    return str(tmp_path / "state.db")


def test_gm3_set_approver_creates_record(tmp_path: Path) -> None:
    """set_approver creates Approver with correct fields."""
    db_path = _db(tmp_path)

    approver = set_approver("bp", "Jane Smith", "jane@company.com", db_path)

    assert isinstance(approver, Approver)
    assert approver.blueprint_name == "bp"
    assert approver.approver_name == "Jane Smith"
    assert approver.approver_email == "jane@company.com"
    assert approver.id
    assert approver.created_at
    assert approver.updated_at


def test_gm3_create_request_returns_pending_status(tmp_path: Path) -> None:
    """create_request returns ApprovalRequest with PENDING status."""
    db_path = _db(tmp_path)

    request = create_request("bp", "Upgrade to v1.1.0", "eng@company.com", db_path)

    assert request.request_code == "REQ-001"
    assert request.status == "PENDING"
    assert request.decided_by is None
    assert request.decision_reason is None
    assert request.decided_at is None
    assert request.requested_by == "eng@company.com"


def test_gm3_request_code_is_sequential(tmp_path: Path) -> None:
    """Second request gets REQ-002 when REQ-001 exists."""
    db_path = _db(tmp_path)
    first = create_request("bp", "change one", "eng@company.com", db_path)
    second = create_request("bp", "change two", "eng@company.com", db_path)

    assert first.request_code == "REQ-001"
    assert second.request_code == "REQ-002"


def test_gm3_approve_request_changes_status(tmp_path: Path) -> None:
    """approve_request sets status to APPROVED."""
    db_path = _db(tmp_path)
    create_request("bp", "change", "eng@company.com", db_path)

    approved = approve_request("REQ-001", "jane@company.com", db_path)

    assert approved.status == "APPROVED"
    assert approved.decided_by == "jane@company.com"
    assert approved.decided_at is not None


def test_gm3_reject_request_stores_reason(tmp_path: Path) -> None:
    """reject_request sets status to REJECTED and stores the reason."""
    db_path = _db(tmp_path)
    create_request("bp", "change", "eng@company.com", db_path)

    rejected = reject_request(
        "REQ-001", "jane@company.com", "needs security review", db_path
    )

    assert rejected.status == "REJECTED"
    assert rejected.decision_reason == "needs security review"
    assert rejected.decided_at is not None


def test_gm3_get_pending_excludes_decided_requests(tmp_path: Path) -> None:
    """get_pending_requests excludes APPROVED and REJECTED requests."""
    db_path = _db(tmp_path)
    create_request("bp", "change one", "eng@company.com", db_path)
    create_request("bp", "change two", "eng@company.com", db_path)
    approve_request("REQ-001", "jane@company.com", db_path)

    pending = get_pending_requests(db_path)

    assert len(pending) == 1
    assert pending[0].request_code == "REQ-002"


def test_gm3_raises_pk_gm_005_for_unknown_request(tmp_path: Path) -> None:
    """GovernanceError PK-GM-005 raised for an unknown request_code."""
    db_path = _db(tmp_path)

    with pytest.raises(GovernanceError) as exc_info:
        approve_request("REQ-999", "jane@company.com", db_path)

    assert exc_info.value.code == "PK-GM-005"


def test_gm3_raises_pk_gm_006_for_already_decided_request(tmp_path: Path) -> None:
    """GovernanceError PK-GM-006 raised when the request is already decided."""
    db_path = _db(tmp_path)
    create_request("bp", "change", "eng@company.com", db_path)
    approve_request("REQ-001", "jane@company.com", db_path)

    with pytest.raises(GovernanceError) as exc_info:
        approve_request("REQ-001", "jane@company.com", db_path)

    assert exc_info.value.code == "PK-GM-006"


def test_gm3_get_all_requests_filters_by_blueprint(tmp_path: Path) -> None:
    """get_all_requests returns only requests for the specified blueprint."""
    db_path = _db(tmp_path)
    create_request("bp-a", "change a", "eng@company.com", db_path)
    create_request("bp-b", "change b", "eng@company.com", db_path)

    a_requests = get_all_requests("bp-a", db_path)

    assert len(a_requests) == 1
    assert a_requests[0].blueprint_name == "bp-a"
    assert a_requests[0].change_description == "change a"
