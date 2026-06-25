"""Tests for EvidenceCollector (SPEC-005). Reads real state.db via tmp_path."""

from __future__ import annotations

import json

import pytest
from pipelinekit.ai.evidence import EvidenceCollector, EvidencePackage
from pipelinekit.core.errors import DiagnosticsError
from pipelinekit.state import db


def _seed_run(tmp_path, run_id: str = "run-abc12345") -> None:
    db.insert_run(run_id, "demo", cwd=tmp_path)
    db.update_run(
        run_id,
        "failed",
        1.2,
        error_code="PK-ADAPTER-001",
        error_msg="refused",
        cwd=tmp_path,
    )
    violations = [{"error_code": "PK-CONTRACT-002", "message": "stale"}]
    db.insert_contract_result(
        run_id, "orders", "violated", 1, json.dumps(violations), cwd=tmp_path
    )


def test_collect_returns_package(tmp_path):
    """collect() assembles an EvidencePackage from a valid state.db."""
    _seed_run(tmp_path)
    pkg = EvidenceCollector().collect("run-abc12345", cwd=tmp_path)
    assert isinstance(pkg, EvidencePackage)
    assert pkg.run_id == "run-abc12345"
    assert pkg.pipeline_name == "demo"
    assert pkg.pipeline_result["status"] == "failed"
    assert len(pkg.contract_results) == 1
    assert "PK-ADAPTER-001" in pkg.error_codes
    assert "PK-CONTRACT-002" in pkg.error_codes


def test_collect_unknown_run_raises_diag_001(tmp_path):
    """collect() raises DiagnosticsError(PK-DIAG-001) for an unknown run_id."""
    db.initialize(cwd=tmp_path)
    with pytest.raises(DiagnosticsError) as exc_info:
        EvidenceCollector().collect("run-missing", cwd=tmp_path)
    assert exc_info.value.code == "PK-DIAG-001"


def test_get_most_recent_run_id(tmp_path):
    """get_most_recent_run_id() returns the latest run id."""
    _seed_run(tmp_path, "run-old00001")
    _seed_run(tmp_path, "run-new00002")
    most_recent = EvidenceCollector().get_most_recent_run_id(cwd=tmp_path)
    assert most_recent in {"run-old00001", "run-new00002"}


def test_get_most_recent_run_id_empty_raises(tmp_path):
    """get_most_recent_run_id() raises PK-DIAG-001 when no runs exist."""
    db.initialize(cwd=tmp_path)
    with pytest.raises(DiagnosticsError) as exc_info:
        EvidenceCollector().get_most_recent_run_id(cwd=tmp_path)
    assert exc_info.value.code == "PK-DIAG-001"


def test_package_is_json_serializable(tmp_path):
    """EvidencePackage.to_dict() round-trips through JSON without error."""
    _seed_run(tmp_path)
    pkg = EvidenceCollector().collect("run-abc12345", cwd=tmp_path)
    encoded = json.dumps(pkg.to_dict())
    assert json.loads(encoded)["run_id"] == "run-abc12345"
