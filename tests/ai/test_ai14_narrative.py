"""Tests for AI-8 quality scorecard narrative (SPEC-033).

The AI provider is always mocked — no real API calls. CLI behavior is exercised
with Typer's ``CliRunner``.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pipelinekit.ai.cascade import estimate_prompt_tokens
from pipelinekit.ai.ems_context import EMSContext
from pipelinekit.ai.narrative import (
    build_narrative_prompt,
    generate_scorecard_narrative,
)
from pipelinekit.cli.quality import quality_app
from pipelinekit.quality.scorecard import BlueprintScore, ComponentScore
from typer.testing import CliRunner


def _score() -> BlueprintScore:
    return BlueprintScore(
        blueprint_name="stripe-to-snowflake",
        composite_score=88.0,
        rating="Good",
        components=[
            ComponentScore("coverage", 82.6, "82.6%", "✓"),
            ComponentScore("volume", 100.0, "OK", "✓"),
            ComponentScore("drift", 50.0, "NO_BASELINE", "—"),
            ComponentScore("ownership", 100.0, "Set", "✓"),
        ],
    )


def _ems_with_slo() -> EMSContext:
    return EMSContext(
        blueprint_name="stripe-to-snowflake",
        quality_score=88.0,
        quality_rating="Good",
        slo_violations=[
            {
                "table": "charges",
                "type": "freshness",
                "threshold": 6.0,
                "current": 8.0,
                "status": "VIOLATED",
            }
        ],
        has_data=True,
        summary="EMS signals: 1 SLO violation(s)",
    )


def _empty_ems() -> EMSContext:
    return EMSContext(
        blueprint_name="stripe-to-snowflake",
        quality_score=88.0,
        quality_rating="Good",
        has_data=False,
        summary="No EMS data available for this blueprint",
    )


def test_ai8_build_narrative_prompt_includes_score() -> None:
    """The prompt states the composite score and rating."""
    prompt = build_narrative_prompt(_score(), _empty_ems())

    assert "stripe-to-snowflake" in prompt
    assert "88/100" in prompt
    assert "Good" in prompt
    assert "coverage" in prompt


def test_ai8_build_narrative_prompt_includes_ems_signals() -> None:
    """The prompt includes EMS signals when present."""
    prompt = build_narrative_prompt(_score(), _ems_with_slo())

    assert "charges" in prompt
    assert "freshness" in prompt
    assert "SLO violation" in prompt


def test_ai8_generate_narrative_returns_empty_on_provider_failure() -> None:
    """A failing provider yields an empty narrative string."""
    provider = MagicMock()
    provider._complete.side_effect = RuntimeError("provider down")

    result = generate_scorecard_narrative(_score(), _ems_with_slo(), provider, "db")

    assert result == ""


def test_ai8_generate_narrative_never_raises() -> None:
    """generate_scorecard_narrative never raises, even for a bad provider."""
    # A provider missing _complete raises AttributeError internally.
    result = generate_scorecard_narrative(_score(), _ems_with_slo(), object(), "db")
    assert result == ""

    # A well-formed provider returns its text, stripped.
    provider = MagicMock()
    provider._complete.return_value = "  The score is 88 because coverage is high.  "
    text = generate_scorecard_narrative(_score(), _empty_ems(), provider, "db")
    assert text == "The score is 88 because coverage is high."


def test_ai8_scorecard_command_accepts_narrative_flag() -> None:
    """The scorecard command exposes a --narrative flag."""
    result = CliRunner().invoke(quality_app, ["scorecard", "--help"])

    assert result.exit_code == 0
    assert "--narrative" in result.output


def test_ai8_scorecard_without_narrative_makes_no_ai_call() -> None:
    """Running scorecard without --narrative never generates a narrative."""
    with patch(
        "pipelinekit.cli.quality.generate_scorecard_narrative"
    ) as mock_narrative:
        result = CliRunner().invoke(quality_app, ["scorecard"])

    assert result.exit_code == 0
    mock_narrative.assert_not_called()


def test_ai8_narrative_prompt_under_500_tokens() -> None:
    """The built prompt stays under 500 tokens."""
    prompt = build_narrative_prompt(_score(), _ems_with_slo())

    assert estimate_prompt_tokens(prompt) < 500


def test_ai8_narrative_includes_priority_recommendation() -> None:
    """The prompt asks for root cause, a priority fix, and expected impact."""
    prompt = build_narrative_prompt(_score(), _ems_with_slo()).lower()

    assert "root cause" in prompt
    assert "priority" in prompt
    assert "impact" in prompt
