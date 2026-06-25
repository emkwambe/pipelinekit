"""Tests for ArchitectureContextCollector (SPEC-011). Reads real state.db."""

from __future__ import annotations

import json

import pytest
from pipelinekit.ai.arch_evidence import (
    ArchitectureContext,
    ArchitectureContextCollector,
)
from pipelinekit.core.errors import ArchitectureError
from pipelinekit.state import db


def _seed_runs(tmp_path, count: int) -> None:
    for i in range(count):
        run_id = f"run-arch{i:04d}"
        db.insert_run(run_id, "demo", cwd=tmp_path)
        status = "failed" if i % 3 == 0 else "success"
        db.update_run(run_id, status, 1.0 + i, cwd=tmp_path)


def test_collect_returns_context(tmp_path):
    """collect() assembles an ArchitectureContext from a valid state.db."""
    _seed_runs(tmp_path, 6)
    ctx = ArchitectureContextCollector().collect(cwd=tmp_path)
    assert isinstance(ctx, ArchitectureContext)
    assert len(ctx.run_history) == 6
    assert isinstance(ctx.adr_summaries, list)
    assert isinstance(ctx.blueprint_metadata, list)


def test_collect_insufficient_history_raises_arch_004(tmp_path):
    """collect() raises ArchitectureError(PK-ARCH-004) with fewer than 5 runs."""
    _seed_runs(tmp_path, 4)
    with pytest.raises(ArchitectureError) as exc_info:
        ArchitectureContextCollector().collect(cwd=tmp_path)
    assert exc_info.value.code == "PK-ARCH-004"


def test_context_is_json_serializable(tmp_path):
    """ArchitectureContext.to_dict() round-trips through JSON without error."""
    _seed_runs(tmp_path, 5)
    ctx = ArchitectureContextCollector().collect(cwd=tmp_path)
    encoded = json.dumps(ctx.to_dict())
    assert json.loads(encoded)["volume_profile"]["runs_observed"] == 5


def test_volume_profile_from_run_history(tmp_path):
    """Volume profile is derived from run history."""
    _seed_runs(tmp_path, 6)
    ctx = ArchitectureContextCollector().collect(cwd=tmp_path)
    profile = ctx.volume_profile
    assert profile["runs_observed"] == 6
    assert "runs_per_day" in profile
    assert profile["failed_runs"] >= 1
