"""Integration tests for ``pipelinekit governance`` — real SQLite state via CLI."""

from __future__ import annotations

from pipelinekit.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_governance_owner_set_exits_zero(project: str) -> None:
    """`governance owner set` runs and echoes the blueprint."""
    result = runner.invoke(
        app,
        [
            "governance",
            "owner",
            "set",
            "stripe-to-snowflake",
            "--name",
            "Jane Smith",
            "--email",
            "jane@company.com",
        ],
    )
    assert result.exit_code == 0
    assert "stripe-to-snowflake" in result.output


def test_governance_owner_list_shows_set_owner(project: str) -> None:
    """`governance owner list` shows an owner set earlier."""
    runner.invoke(
        app,
        [
            "governance",
            "owner",
            "set",
            "stripe-to-snowflake",
            "--name",
            "Jane Smith",
            "--email",
            "jane@company.com",
        ],
    )
    result = runner.invoke(app, ["governance", "owner", "list"])
    assert result.exit_code == 0
    assert "jane@company.com" in result.output


def test_governance_owner_get_returns_owner(project: str) -> None:
    """`governance owner get` returns the set owner's name."""
    runner.invoke(
        app,
        [
            "governance",
            "owner",
            "set",
            "stripe-to-snowflake",
            "--name",
            "Jane Smith",
            "--email",
            "jane@company.com",
        ],
    )
    result = runner.invoke(app, ["governance", "owner", "get", "stripe-to-snowflake"])
    assert result.exit_code == 0
    assert "Jane Smith" in result.output


def test_governance_owner_remove_exits_zero(project: str) -> None:
    """`governance owner remove` removes a previously-set owner."""
    runner.invoke(
        app,
        [
            "governance",
            "owner",
            "set",
            "stripe-to-snowflake",
            "--name",
            "Jane Smith",
            "--email",
            "jane@company.com",
        ],
    )
    result = runner.invoke(
        app, ["governance", "owner", "remove", "stripe-to-snowflake"]
    )
    assert result.exit_code == 0


def test_governance_convention_add_and_list(project: str) -> None:
    """`governance convention add` then `list` shows the convention scope."""
    result = runner.invoke(
        app,
        [
            "governance",
            "convention",
            "add",
            "--scope",
            "table",
            "--pattern",
            r"^(stg|fct|dim|raw)_[a-z_]+",
            "--description",
            "Table prefix convention",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(app, ["governance", "convention", "list"])
    assert result.exit_code == 0
    assert "table" in result.output


def test_governance_approval_full_lifecycle(project: str) -> None:
    """Full approval lifecycle: request -> list -> approve, all via the CLI."""
    runner.invoke(
        app,
        [
            "governance",
            "approver",
            "set",
            "stripe-to-snowflake",
            "--name",
            "Jane Smith",
            "--email",
            "jane@company.com",
        ],
    )
    result = runner.invoke(
        app,
        [
            "governance",
            "approval",
            "request",
            "--blueprint",
            "stripe-to-snowflake",
            "--change",
            "Upgrade to v1.1.0",
            "--requested-by",
            "engineer@company.com",
        ],
    )
    assert result.exit_code == 0
    assert "REQ-001" in result.output

    result = runner.invoke(app, ["governance", "approval", "list"])
    assert result.exit_code == 0
    assert "REQ-001" in result.output

    result = runner.invoke(app, ["governance", "approval", "approve", "REQ-001"])
    assert result.exit_code == 0
    assert "REQ-001" in result.output
