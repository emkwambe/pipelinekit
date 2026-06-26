"""Tests for the migrate CLI (SPEC-017). Provider mocked — no AI calls."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from pipelinekit.ai.migration_models import (
    MappingResult,
    MappingStatus,
    MigrationGap,
    MigrationProposal,
)
from pipelinekit.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()

_AIRBYTE = {
    "source": {"sourceType": "postgres", "connectionConfiguration": {}},
    "destination": {"destinationType": "snowflake", "connectionConfiguration": {}},
    "syncCatalog": {
        "streams": [
            {"stream": {"name": "customers"}, "config": {"syncMode": "incremental"}}
        ]
    },
}


def _proposal(blocking: bool) -> MigrationProposal:
    return MigrationProposal(
        source_tool="",
        source_file="",
        draft_yaml="pipeline:\n  name: migrated\n",
        blueprint_recommendation="postgres-to-snowflake",
        mappings=[
            MappingResult(
                "source.type", "postgres", "ingestion.source.type", MappingStatus.CLEAN
            )
        ],
        gaps=[MigrationGap("credential", "creds", "set env vars", blocking=blocking)],
        confidence=0.84,
    )


def test_migrate_analyze_help_exits_zero():
    result = runner.invoke(app, ["migrate", "analyze", "--help"])
    assert result.exit_code == 0


def _airbyte_file(tmp_path):
    path = tmp_path / "connection.json"
    path.write_text(json.dumps(_AIRBYTE), encoding="utf-8")
    return path


def test_migrate_analyze_writes_no_files_by_default(tmp_path, monkeypatch):
    """analyze (no --apply) shows the analysis and writes nothing."""
    provider = MagicMock()
    provider.analyze_migration.return_value = _proposal(blocking=True)
    monkeypatch.chdir(tmp_path)
    path = _airbyte_file(tmp_path)
    with patch("pipelinekit.cli.migrate.create_provider", return_value=provider):
        result = runner.invoke(
            app, ["migrate", "analyze", str(path), "-p", "anthropic"]
        )
    assert result.exit_code == 0
    assert "Migration Analysis" in result.stdout
    assert "postgres-to-snowflake" in result.stdout
    assert not (tmp_path / "pipelinekit.proposed.yaml").exists()


def test_migrate_analyze_apply_blocking_gap_reports_pk_migrate_003(
    tmp_path, monkeypatch
):
    """--apply with a blocking gap and no --write-draft reports PK-MIGRATE-003."""
    provider = MagicMock()
    provider.analyze_migration.return_value = _proposal(blocking=True)
    monkeypatch.chdir(tmp_path)
    path = _airbyte_file(tmp_path)
    with patch("pipelinekit.cli.migrate.create_provider", return_value=provider):
        result = runner.invoke(
            app, ["migrate", "analyze", str(path), "-p", "anthropic", "--apply"]
        )
    assert result.exit_code == 1
    assert "PK-MIGRATE-003" in result.stdout
    assert not (tmp_path / "pipelinekit.proposed.yaml").exists()


def test_migrate_analyze_apply_non_blocking_writes_proposed_yaml(tmp_path, monkeypatch):
    """--apply with no blocking gap writes pipelinekit.proposed.yaml
    (never pipelinekit.yaml) — no override flag needed."""
    provider = MagicMock()
    provider.analyze_migration.return_value = _proposal(blocking=False)
    monkeypatch.chdir(tmp_path)
    path = _airbyte_file(tmp_path)
    with patch("pipelinekit.cli.migrate.create_provider", return_value=provider):
        result = runner.invoke(
            app, ["migrate", "analyze", str(path), "-p", "anthropic", "--apply"]
        )
    assert result.exit_code == 0
    assert (tmp_path / "pipelinekit.proposed.yaml").exists()
    assert not (tmp_path / "pipelinekit.yaml").exists()
