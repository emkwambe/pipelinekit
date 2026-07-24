"""Tests for the provider cascade (AI-6 update, ADR-042).

Every provider is mocked — no real API calls. The cascade is exercised through a
mock ``provider_factory`` that returns ``MagicMock`` providers with a
``complete`` method and a ``MAX_CONTEXT_TOKENS`` attribute.
"""

from __future__ import annotations

import logging
from typing import Callable
from unittest.mock import MagicMock

import pytest
from pipelinekit.ai.cascade import (
    CascadeConfig,
    CascadeExhaustedError,
    estimate_prompt_tokens,
    execute_with_cascade,
)
from pipelinekit.core.errors import LLMError


def _provider(
    *,
    result: str | None = None,
    error: Exception | None = None,
    max_context: int = 200_000,
) -> MagicMock:
    """Build a mock provider with a ``complete`` method and a context limit."""
    provider = MagicMock()
    provider.MAX_CONTEXT_TOKENS = max_context
    if error is not None:
        provider.complete.side_effect = error
    else:
        provider.complete.return_value = result
    return provider


def _factory(providers: dict[str, MagicMock]) -> Callable[[str], MagicMock]:
    """Return a provider_factory over a name→mock mapping."""

    def factory(name: str) -> MagicMock:
        if name not in providers:
            raise LLMError("PK-AI-001", f"unknown provider {name}", {})
        return providers[name]

    return factory


def test_cascade_uses_primary_when_available() -> None:
    """The primary provider is used when it succeeds; fallbacks untouched."""
    cfg = CascadeConfig(primary="anthropic", fallbacks=["kimi"])
    providers = {
        "anthropic": _provider(result="primary-ok"),
        "kimi": _provider(result="kimi-ok"),
    }

    result, used = execute_with_cascade("hello", cfg, _factory(providers))

    assert result == "primary-ok"
    assert used == "anthropic"
    providers["kimi"].complete.assert_not_called()


def test_cascade_falls_back_on_provider_error() -> None:
    """Falls back to the next provider when the primary raises."""
    cfg = CascadeConfig(primary="anthropic", fallbacks=["kimi"])
    providers = {
        "anthropic": _provider(error=LLMError("PK-AI-001", "unavailable")),
        "kimi": _provider(result="kimi-ok"),
    }

    result, used = execute_with_cascade("hello", cfg, _factory(providers))

    assert result == "kimi-ok"
    assert used == "kimi"


def test_cascade_falls_back_on_rate_limit() -> None:
    """Falls back when the primary returns a rate-limit error."""
    cfg = CascadeConfig(primary="anthropic", fallbacks=["kimi"])
    providers = {
        "anthropic": _provider(error=LLMError("PK-AI-001", "429 rate limit exceeded")),
        "kimi": _provider(result="kimi-ok"),
    }

    result, used = execute_with_cascade("hello", cfg, _factory(providers))

    assert used == "kimi"
    assert result == "kimi-ok"


def test_cascade_skips_provider_when_context_exceeded() -> None:
    """A provider whose MAX_CONTEXT_TOKENS < prompt tokens is skipped uncalled."""
    cfg = CascadeConfig(primary="small", fallbacks=["big"])
    prompt = "word " * 100  # ~131 estimated tokens
    providers = {
        "small": _provider(result="small-ok", max_context=10),
        "big": _provider(result="big-ok", max_context=200_000),
    }

    result, used = execute_with_cascade(prompt, cfg, _factory(providers))

    assert used == "big"
    assert result == "big-ok"
    providers["small"].complete.assert_not_called()


def test_cascade_uses_large_context_provider_for_big_prompt() -> None:
    """A big prompt routes to the 128k provider when the 8k one can't hold it."""
    cfg = CascadeConfig(primary="anthropic", fallbacks=["kimi"])
    prompt = "token " * 10_000  # ~13001 estimated tokens
    providers = {
        "anthropic": _provider(result="a", max_context=8_192),
        "kimi": _provider(result="kimi-big", max_context=131_072),
    }

    result, used = execute_with_cascade(prompt, cfg, _factory(providers))

    assert used == "kimi"
    assert result == "kimi-big"
    providers["anthropic"].complete.assert_not_called()


def test_cascade_raises_pk_ai_001_when_all_fail() -> None:
    """CascadeExhaustedError (PK-AI-001) is raised when every provider fails."""
    cfg = CascadeConfig(primary="anthropic", fallbacks=["kimi"])
    providers = {
        "anthropic": _provider(error=LLMError("PK-AI-001", "boom-1")),
        "kimi": _provider(error=LLMError("PK-AI-001", "boom-2")),
    }

    with pytest.raises(CascadeExhaustedError) as exc_info:
        execute_with_cascade("hello", cfg, _factory(providers))

    assert exc_info.value.code == "PK-AI-001"


def test_cascade_single_provider_behavior_unchanged() -> None:
    """With no fallbacks, the cascade is single-provider: success or a raise."""
    cfg = CascadeConfig(primary="anthropic", fallbacks=[])
    ok = {"anthropic": _provider(result="only")}
    result, used = execute_with_cascade("hello", cfg, _factory(ok))
    assert (result, used) == ("only", "anthropic")

    failing = {"anthropic": _provider(error=LLMError("PK-AI-001", "boom"))}
    with pytest.raises(CascadeExhaustedError):
        execute_with_cascade("hello", cfg, _factory(failing))


def test_estimate_prompt_tokens_is_conservative() -> None:
    """estimate_prompt_tokens returns int(word_count * 1.3) + 1."""
    assert estimate_prompt_tokens("word " * 100) == int(100 * 1.3) + 1  # 131
    assert estimate_prompt_tokens("one two three") == int(3 * 1.3) + 1  # 4
    assert estimate_prompt_tokens("") == 1
    # Never underestimates the word count for a non-trivial prompt.
    assert estimate_prompt_tokens("a b c d e") >= 5


def test_cascade_respects_max_fallback_attempts() -> None:
    """Stops after max_fallback_attempts even when more fallbacks remain."""
    cfg = CascadeConfig(
        primary="p1", fallbacks=["p2", "p3", "p4"], max_fallback_attempts=2
    )
    providers = {
        name: _provider(error=LLMError("PK-AI-001", "boom"))
        for name in ("p1", "p2", "p3", "p4")
    }

    with pytest.raises(CascadeExhaustedError):
        execute_with_cascade("hello", cfg, _factory(providers))

    attempted = [name for name, p in providers.items() if p.complete.called]
    assert len(attempted) == 2
    assert not providers["p3"].complete.called
    assert not providers["p4"].complete.called


def test_cascade_logs_provider_used(caplog: pytest.LogCaptureFixture) -> None:
    """execute_with_cascade logs which provider was attempted and succeeded."""
    cfg = CascadeConfig(primary="anthropic", fallbacks=[])
    providers = {"anthropic": _provider(result="ok")}

    with caplog.at_level(logging.INFO, logger="pipelinekit.ai.cascade"):
        _, used = execute_with_cascade("hello", cfg, _factory(providers))

    assert used == "anthropic"
    messages = [record.getMessage() for record in caplog.records]
    assert any("Success with provider: anthropic" in m for m in messages)
    assert any("Attempting provider: anthropic" in m for m in messages)
