"""Tests for Migration Intelligence models (SPEC-017, ADR-020)."""

from __future__ import annotations

from pipelinekit.ai.migration_models import (
    MappingResult,
    MappingStatus,
    MigrationGap,
    MigrationProposal,
)


def _proposal(gaps: list[MigrationGap]) -> MigrationProposal:
    return MigrationProposal(
        source_tool="airbyte",
        source_file="connection.json",
        draft_yaml="pipeline:\n  name: demo\n",
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
    )


def test_migration_proposal_serializes_round_trip():
    """MigrationProposal survives to_dict → from_dict."""
    proposal = _proposal([MigrationGap("credential", "set env vars", "set PG_USER")])
    restored = MigrationProposal.from_dict(proposal.to_dict())
    assert restored.source_tool == "airbyte"
    assert restored.draft_yaml == proposal.draft_yaml
    assert restored.blueprint_recommendation == "postgres-to-snowflake"
    assert len(restored.mappings) == 1
    assert restored.mappings[0].status is MappingStatus.CLEAN
    assert restored.confidence == 0.84
    assert restored.can_auto_apply is False


def test_blocking_gaps_count_matches_blocking_gaps():
    """blocking_gaps counts exactly the gaps with blocking=True."""
    gaps = [
        MigrationGap("credential", "creds", "set env vars", blocking=True),
        MigrationGap("schedule", "sched", "configure cron", blocking=True),
        MigrationGap("feature", "nice-to-have", "optional", blocking=False),
    ]
    proposal = _proposal(gaps)
    assert proposal.blocking_gaps == 2
    # Recomputed in __post_init__ even after from_dict.
    assert MigrationProposal.from_dict(proposal.to_dict()).blocking_gaps == 2
