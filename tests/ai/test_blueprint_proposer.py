"""Tests for BlueprintProposer (SPEC-015, ADR-018). Provider mocked — no AI calls.

The trust boundary: propose() writes no blueprint files; only apply() writes, and
only APPROVED assets; can_auto_apply is always False; unsupported sources fail
before any AI call.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from pipelinekit.ai.blueprint_proposer import BlueprintProposer
from pipelinekit.ai.proposal_models import (
    AssetState,
    BlueprintProposal,
    ProposedAsset,
)
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import ProposalError

_VALID_BLUEPRINT_JSON = json.dumps(
    {
        "name": "stripe-to-snowflake",
        "version": "1.0.0",
        "source": {"type": "stripe", "dlt_source": "stripe_analytics"},
        "destination": {"type": "snowflake", "dlt_destination": "snowflake"},
        "contracts": ["contracts/charges.yaml"],
    }
)


def _config() -> PipelineConfig:
    return PipelineConfig(
        **{
            "pipeline": {"name": "demo"},
            "runtime": {},
            "ingestion": {
                "source": {"type": "stripe"},
                "destination": {"type": "snowflake"},
            },
            "transformation": {},
            "contracts": {},
            "quality": {},
            "diagnostics": {"enabled": True, "provider": "anthropic"},
            "notifications": {},
        }
    )


def _canned(can_auto_apply: bool = False) -> BlueprintProposal:
    """A fresh proposal as a provider would return it (assets PROPOSED)."""
    return BlueprintProposal(
        plan_id="",
        blueprint_name="stripe-to-snowflake",
        source_type="stripe",
        destination_type="snowflake",
        tables=["charges"],
        assets=[
            ProposedAsset(
                asset_type="blueprint_json",
                filename="blueprint.json",
                content=_VALID_BLUEPRINT_JSON,
            ),
            ProposedAsset(
                asset_type="readme",
                filename="docs/README.md",
                content="# Stripe → Snowflake\n",
            ),
        ],
        confidence=0.9,
        assumptions=["charges has id, amount, currency"],
        provider="anthropic",
        can_auto_apply=can_auto_apply,
    )


def _proposer(proposal: BlueprintProposal) -> BlueprintProposer:
    provider = MagicMock()
    provider.name = "anthropic"
    provider.propose_blueprint.return_value = proposal
    return BlueprintProposer(_config(), provider)


def test_propose_returns_plan_no_files_written(tmp_path):
    """propose() returns a BlueprintProposal and writes no blueprint files."""
    proposer = _proposer(_canned())
    proposal = proposer.propose("stripe", "snowflake", ["charges"], cwd=tmp_path)
    assert isinstance(proposal, BlueprintProposal)
    assert proposal.plan_id.startswith("plan-stripe-snowflake-")
    assert not (tmp_path / "blueprints").exists()  # nothing written


def test_can_auto_apply_always_false(tmp_path):
    """A provider returning can_auto_apply=True is corrected to False."""
    proposer = _proposer(_canned(can_auto_apply=True))
    proposal = proposer.propose("stripe", "snowflake", ["charges"], cwd=tmp_path)
    assert proposal.can_auto_apply is False


def test_apply_writes_only_approved(tmp_path):
    """apply() writes only APPROVED assets."""
    proposal = _canned()
    proposal.plan_id = "plan-test-1"
    proposal.assets[0].approve()  # blueprint.json approved; README stays proposed
    proposer = BlueprintProposer(_config(), MagicMock())
    written = proposer.apply(proposal, cwd=tmp_path)
    bp = tmp_path / "blueprints" / "stripe-to-snowflake"
    assert len(written) == 1
    assert (bp / "blueprint.json").exists()
    assert not (bp / "docs" / "README.md").exists()


def test_apply_strips_blueprint_name_prefix(tmp_path):
    """apply() strips a leading <blueprint_name>/ prefix (no doubled directory)."""
    proposal = _canned()
    proposal.plan_id = "plan-prefix-1"
    # AI rooted the filename at the blueprint dir — would double without stripping.
    proposal.assets[0].filename = "stripe-to-snowflake/blueprint.json"
    proposal.assets[0].approve()
    proposer = BlueprintProposer(_config(), MagicMock())
    proposer.apply(proposal, cwd=tmp_path)
    bp = tmp_path / "blueprints" / "stripe-to-snowflake"
    assert (bp / "blueprint.json").exists()
    assert not (bp / "stripe-to-snowflake").exists()  # not doubled


def test_apply_raises_on_no_approved(tmp_path):
    """apply() raises ProposalError(PK-GEN-003) when no assets are approved."""
    proposal = _canned()
    proposal.plan_id = "plan-test-2"
    proposer = BlueprintProposer(_config(), MagicMock())
    with pytest.raises(ProposalError) as exc_info:
        proposer.apply(proposal, cwd=tmp_path)
    assert exc_info.value.code == "PK-GEN-003"


def test_apply_raises_on_existing_directory(tmp_path):
    """apply() raises ProposalError(PK-GEN-004) when the blueprint dir exists."""
    proposal = _canned()
    proposal.plan_id = "plan-test-3"
    proposal.assets[0].approve()
    (tmp_path / "blueprints" / "stripe-to-snowflake").mkdir(parents=True)
    proposer = BlueprintProposer(_config(), MagicMock())
    with pytest.raises(ProposalError) as exc_info:
        proposer.apply(proposal, cwd=tmp_path)
    assert exc_info.value.code == "PK-GEN-004"


def test_unsupported_source_raises_before_ai_call(tmp_path):
    """An unsupported source raises PK-GEN-006 without calling the provider."""
    proposer = _proposer(_canned())
    with pytest.raises(ProposalError) as exc_info:
        proposer.propose("oracle", "snowflake", ["things"], cwd=tmp_path)
    assert exc_info.value.code == "PK-GEN-006"
    proposer.provider.propose_blueprint.assert_not_called()


def test_asset_state_machine_valid_path():
    """proposed → approved → written → validated is allowed."""
    asset = ProposedAsset("readme", "docs/README.md", "# x")
    asset.approve()
    assert asset.state is AssetState.APPROVED
    asset.mark_written()
    assert asset.state is AssetState.WRITTEN
    asset.mark_validated()
    assert asset.state is AssetState.VALIDATED


def test_asset_invalid_transition_raises_pk_gen_007():
    """proposed → written (skipping approval) raises PK-GEN-007."""
    asset = ProposedAsset("readme", "docs/README.md", "# x")
    with pytest.raises(ProposalError) as exc_info:
        asset.mark_written()  # PROPOSED → WRITTEN is forbidden
    assert exc_info.value.code == "PK-GEN-007"
    assert asset.state is AssetState.PROPOSED


def test_asset_edit_records_history_and_reproposes():
    """edit moves proposed → edited (recording history); repropose returns it."""
    asset = ProposedAsset("readme", "docs/README.md", "old")
    asset.edit("new")
    assert asset.state is AssetState.EDITED
    assert asset.content == "new"
    assert asset.edit_history == ["old"]
    asset.repropose()
    assert asset.state is AssetState.PROPOSED


def test_proposal_roundtrips_through_dict():
    """BlueprintProposal survives to_dict → from_dict."""
    proposal = _canned()
    proposal.plan_id = "plan-rt-1"
    proposal.assets[0].approve()
    restored = BlueprintProposal.from_dict(proposal.to_dict())
    assert restored.plan_id == "plan-rt-1"
    assert restored.blueprint_name == proposal.blueprint_name
    assert len(restored.assets) == 2
    assert restored.assets[0].state.value == "approved"
    assert restored.can_auto_apply is False


def test_proposal_persists_and_reloads_from_db(tmp_path):
    """A proposal stored by propose() reloads with get_blueprint_proposal."""
    from pipelinekit.state import db

    proposer = _proposer(_canned())
    proposal = proposer.propose("stripe", "snowflake", ["charges"], cwd=tmp_path)
    loaded = db.get_blueprint_proposal(proposal.plan_id, cwd=tmp_path)
    assert loaded is not None
    assert loaded["blueprint_name"] == "stripe-to-snowflake"
    assert loaded["can_auto_apply"] is False
    assert len(loaded["assets"]) == 2
