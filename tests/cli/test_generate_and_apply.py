"""Tests for the generate/apply CLI (SPEC-015). No AI calls."""

from __future__ import annotations

from pipelinekit.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()

_CONFIG = """\
pipeline:
  name: demo
runtime:
  environment: local
ingestion:
  source:
    type: stripe
  destination:
    type: snowflake
transformation:
  enabled: false
contracts:
  enabled: true
quality:
  enabled: false
diagnostics:
  enabled: true
  provider: anthropic
notifications:
  enabled: false
"""


def test_generate_blueprint_help_exits_zero():
    result = runner.invoke(app, ["generate", "blueprint", "--help"])
    assert result.exit_code == 0


def test_generate_show_help_exits_zero():
    result = runner.invoke(app, ["generate", "show", "--help"])
    assert result.exit_code == 0


def test_apply_plan_help_exits_zero():
    result = runner.invoke(app, ["apply", "plan", "--help"])
    assert result.exit_code == 0


def _seed_proposal(cwd, approved: bool = False):
    """Insert a minimal proposal into state.db at ``cwd`` and return its plan_id."""
    from pipelinekit.ai.proposal_models import BlueprintProposal, ProposedAsset
    from pipelinekit.state import db

    asset = ProposedAsset("readme", "docs/README.md", "# x")
    if approved:
        asset.approve()
    proposal = BlueprintProposal(
        plan_id="plan-stripe-snowflake-test",
        blueprint_name="stripe-to-snowflake",
        source_type="stripe",
        destination_type="snowflake",
        tables=["charges"],
        assets=[asset],
        confidence=0.88,
    )
    db.insert_blueprint_proposal(proposal.to_dict(), cwd=cwd)
    return proposal.plan_id


def test_generate_show_displays_stored_plan(tmp_path, monkeypatch):
    """generate show <plan_id> renders a stored proposal."""
    plan_id = _seed_proposal(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["generate", "show", plan_id])
    assert result.exit_code == 0
    assert plan_id in result.stdout


def test_apply_plan_no_approved_reports_pk_gen_003(tmp_path, monkeypatch):
    """apply plan on a proposal with no approved assets reports PK-GEN-003."""
    plan_id = _seed_proposal(tmp_path, approved=False)
    (tmp_path / "pipelinekit.yaml").write_text(_CONFIG, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    # No --interactive and no prior approval → must not write (no auto-apply).
    result = runner.invoke(app, ["apply", "plan", plan_id])
    assert result.exit_code == 1
    assert "PK-GEN-003" in result.stdout


def test_show_unknown_plan_exits_one(tmp_path, monkeypatch):
    """generate show on an unknown plan id exits 1."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["generate", "show", "plan-does-not-exist"])
    assert result.exit_code == 1


def test_generate_blueprint_plan_writes_no_files(tmp_path, monkeypatch):
    """generate blueprint --plan prints a plan ID and writes no blueprint files."""
    from unittest.mock import MagicMock, patch

    from pipelinekit.ai.proposal_models import BlueprintProposal, ProposedAsset

    canned = BlueprintProposal(
        plan_id="",
        blueprint_name="stripe-to-snowflake",
        source_type="stripe",
        destination_type="snowflake",
        tables=["charges"],
        assets=[ProposedAsset("readme", "docs/README.md", "# x")],
        confidence=0.9,
        provider="anthropic",
    )
    provider = MagicMock()
    provider.name = "anthropic"
    provider.propose_blueprint.return_value = canned

    (tmp_path / "pipelinekit.yaml").write_text(_CONFIG, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    with patch("pipelinekit.cli.generate.create_provider", return_value=provider):
        result = runner.invoke(
            app,
            [
                "generate",
                "blueprint",
                "-s",
                "stripe",
                "-d",
                "snowflake",
                "-t",
                "charges",
                "--plan",
            ],
        )
    assert result.exit_code == 0
    assert "Plan ID:" in result.stdout
    assert "No files written." in result.stdout
    assert not (tmp_path / "blueprints").exists()


def test_unsupported_source_reports_pk_gen_006(tmp_path, monkeypatch):
    """An unsupported source fails with PK-GEN-006 (before any AI call)."""
    (tmp_path / "pipelinekit.yaml").write_text(_CONFIG, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "generate",
            "blueprint",
            "--source",
            "oracle",
            "--destination",
            "snowflake",
            "--tables",
            "things",
        ],
    )
    assert result.exit_code == 1
    assert "PK-GEN-006" in result.stdout
