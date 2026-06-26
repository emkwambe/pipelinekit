"""Tests for MigrationAnalyzer (SPEC-017, ADR-020). Provider mocked — no AI.

The trust boundary: analyze() writes no files; can_auto_apply is always False;
apply() refuses while blocking gaps exist (unless force); apply() writes
pipelinekit.proposed.yaml, never pipelinekit.yaml.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from pipelinekit.ai.migration_analyzer import MigrationAnalyzer
from pipelinekit.ai.migration_models import (
    MappingResult,
    MappingStatus,
    MigrationGap,
    MigrationProposal,
)
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import MigrationError

_AIRBYTE = {
    "source": {"sourceType": "postgres", "connectionConfiguration": {}},
    "destination": {"destinationType": "snowflake", "connectionConfiguration": {}},
    "syncCatalog": {
        "streams": [
            {"stream": {"name": "customers"}, "config": {"syncMode": "incremental"}}
        ]
    },
}


def _config() -> PipelineConfig:
    return PipelineConfig(
        **{
            "pipeline": {"name": "demo"},
            "runtime": {},
            "ingestion": {
                "source": {"type": "postgres"},
                "destination": {"type": "snowflake"},
            },
            "transformation": {},
            "contracts": {},
            "quality": {},
            "diagnostics": {"enabled": True, "provider": "anthropic"},
            "notifications": {},
        }
    )


def _canned(
    gaps: list[MigrationGap], can_auto_apply: bool = False
) -> MigrationProposal:
    """A proposal as a provider would return it (no identity stamped yet)."""
    return MigrationProposal(
        source_tool="",
        source_file="",
        draft_yaml="pipeline:\n  name: migrated\n",
        blueprint_recommendation="postgres-to-snowflake",
        mappings=[
            MappingResult(
                field="source.type",
                source_value="postgres",
                pipelinekit_equivalent="ingestion.source.type: postgres",
                status=MappingStatus.CLEAN,
            )
        ],
        gaps=gaps,
        confidence=0.84,
        can_auto_apply=can_auto_apply,
    )


def _analyzer(proposal: MigrationProposal) -> MigrationAnalyzer:
    provider = MagicMock()
    provider.name = "anthropic"
    provider.analyze_migration.return_value = proposal
    return MigrationAnalyzer(_config(), provider)


def _airbyte_file(tmp_path):
    path = tmp_path / "connection.json"
    path.write_text(json.dumps(_AIRBYTE), encoding="utf-8")
    return path


def test_analyze_returns_proposal_no_files_written(tmp_path):
    """analyze() returns a MigrationProposal and writes no files."""
    analyzer = _analyzer(_canned([]))
    proposal = analyzer.analyze(_airbyte_file(tmp_path), cwd=tmp_path)
    assert isinstance(proposal, MigrationProposal)
    assert proposal.source_tool == "airbyte"
    assert proposal.source_file.endswith("connection.json")
    assert not (tmp_path / "pipelinekit.proposed.yaml").exists()
    assert not (tmp_path / "pipelinekit.yaml").exists()


def test_can_auto_apply_always_false(tmp_path):
    """A provider returning can_auto_apply=True is corrected to False."""
    analyzer = _analyzer(_canned([], can_auto_apply=True))
    proposal = analyzer.analyze(_airbyte_file(tmp_path), cwd=tmp_path)
    assert proposal.can_auto_apply is False


def test_apply_raises_pk_migrate_003_when_blocking_gaps(tmp_path):
    """apply() raises PK-MIGRATE-003 when blocking gaps exist and force is off."""
    proposal = _canned([MigrationGap("credential", "creds", "set env", blocking=True)])
    analyzer = MigrationAnalyzer(_config(), MagicMock())
    with pytest.raises(MigrationError) as exc_info:
        analyzer.apply(proposal, cwd=tmp_path)
    assert exc_info.value.code == "PK-MIGRATE-003"
    assert not (tmp_path / "pipelinekit.proposed.yaml").exists()


def test_apply_writes_proposed_yaml_when_non_blocking(tmp_path):
    """apply() writes pipelinekit.proposed.yaml when no gap is blocking."""
    proposal = _canned([MigrationGap("feature", "optional", "later", blocking=False)])
    analyzer = MigrationAnalyzer(_config(), MagicMock())
    path = analyzer.apply(proposal, cwd=tmp_path)
    target = tmp_path / "pipelinekit.proposed.yaml"
    assert target.exists()
    assert path == str(target)
    assert "migrated" in target.read_text(encoding="utf-8")
    # Never the live config.
    assert not (tmp_path / "pipelinekit.yaml").exists()


def test_apply_force_overrides_blocking_gaps(tmp_path):
    """apply(force=True) writes even when blocking gaps remain."""
    proposal = _canned([MigrationGap("credential", "creds", "set env", blocking=True)])
    analyzer = MigrationAnalyzer(_config(), MagicMock())
    analyzer.apply(proposal, cwd=tmp_path, force=True)
    assert (tmp_path / "pipelinekit.proposed.yaml").exists()
