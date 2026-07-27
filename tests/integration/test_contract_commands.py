"""Integration tests for ``pipelinekit contract`` — real SQLite state via CLI."""

from __future__ import annotations

from pipelinekit.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def _add_consumer() -> list[str]:
    return [
        "contract",
        "consumer",
        "add",
        "stripe-to-snowflake",
        "--email",
        "analyst@company.com",
        "--table",
        "charges",
    ]


def _set_active() -> list[str]:
    return [
        "contract",
        "lifecycle",
        "set",
        "stripe-to-snowflake",
        "--contract",
        "charges.yaml",
        "--state",
        "active",
    ]


def test_contract_consumer_add_exits_zero(project: str) -> None:
    """`contract consumer add` runs without error."""
    result = runner.invoke(app, _add_consumer())
    assert result.exit_code == 0


def test_contract_consumer_list_shows_registered(project: str) -> None:
    """`contract consumer list` shows a registered consumer."""
    runner.invoke(app, _add_consumer())
    result = runner.invoke(app, ["contract", "consumer", "list"])
    assert result.exit_code == 0
    assert "analyst@company.com" in result.output


def test_contract_notifications_empty_initially(project: str) -> None:
    """`contract notifications` reports none on fresh state."""
    result = runner.invoke(app, ["contract", "notifications"])
    assert result.exit_code == 0
    assert "No pending" in result.output


def test_contract_lifecycle_set_and_get(project: str) -> None:
    """`contract lifecycle set` (lowercase state) then `get` shows ACTIVE."""
    result = runner.invoke(app, _set_active())
    assert result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "contract",
            "lifecycle",
            "get",
            "stripe-to-snowflake",
            "--contract",
            "charges.yaml",
        ],
    )
    assert result.exit_code == 0
    assert "ACTIVE" in result.output.upper()


def test_contract_lifecycle_list_shows_state(project: str) -> None:
    """`contract lifecycle list` shows a state after one is set."""
    runner.invoke(app, _set_active())
    result = runner.invoke(app, ["contract", "lifecycle", "list"])
    assert result.exit_code == 0
    assert "ACTIVE" in result.output.upper()
    assert "charges.yaml" in result.output


def test_contract_lifecycle_invalid_transition_exits_one(project: str) -> None:
    """An invalid transition (ACTIVE -> DRAFT) exits 1 with PK-DC-013."""
    runner.invoke(app, _set_active())
    result = runner.invoke(
        app,
        [
            "contract",
            "lifecycle",
            "set",
            "stripe-to-snowflake",
            "--contract",
            "charges.yaml",
            "--state",
            "draft",
        ],
    )
    assert result.exit_code == 1
    assert "PK-DC-013" in result.output
