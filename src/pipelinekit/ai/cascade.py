"""Provider cascade with ordered fallbacks (AI-6 update, ADR-042).

Tries a primary provider first, then ordered fallbacks, so the AI layer survives
a rate-limited, unavailable, or too-small provider. Fallback is **opt-in**: with
no fallbacks configured the cascade behaves exactly like a single provider, so
existing configurations are unchanged.

Fallback triggers:

1. Provider cannot be loaded or its call fails (missing key, network, rate limit).
2. The estimated prompt size exceeds a provider's ``MAX_CONTEXT_TOKENS``.
3. All candidates exhausted → ``CascadeExhaustedError`` (``PK-AI-001``).

Reality notes (this codebase, not the generic ADR template):

* The only AI exception is ``LLMError`` (``PK-AI-001`` unavailable /
  ``PK-AI-002`` bad output). There is no ``RateLimitError``/``NetworkError``
  hierarchy, so the cascade catches ``LLMError`` (and, defensively, any
  ``Exception``) from a provider call and falls back. Rate limits are detected
  heuristically from the error text.
* ``provider_factory`` is normally ``pipelinekit.ai.providers.get_provider``.
* Providers are invoked through a ``complete(prompt)`` callable — this is the
  generic cascade primitive; wiring it into the existing ``diagnose``/
  ``architect`` call sites is deferred to the AI-7+ work that consumes it.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from pipelinekit.core.errors import LLMError

logger = logging.getLogger(__name__)

# Fallback context limit when a provider does not declare MAX_CONTEXT_TOKENS.
_DEFAULT_MAX_CONTEXT_TOKENS = 8192


@dataclass
class CascadeConfig:
    """Primary provider plus ordered fallbacks and fallback policy."""

    primary: str  # provider name, e.g. "anthropic"
    fallbacks: list[str] = field(default_factory=list)  # ordered, e.g. ["kimi"]
    fallback_on_rate_limit: bool = True
    fallback_on_context_exceeded: bool = True
    max_fallback_attempts: int = 3


class CascadeExhaustedError(LLMError):
    """Raised when every provider in the cascade failed or was skipped.

    Carries ``PK-AI-001`` (AI provider unavailable — extended here to "all
    providers exhausted"), so callers that already handle ``LLMError`` work
    unchanged.
    """

    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__("PK-AI-001", message, context or {})


def estimate_prompt_tokens(prompt: str) -> int:
    """Return a conservative token estimate for ``prompt``.

    Formula: ``word_count * 1.3`` rounded down, plus 1 (never underestimates a
    non-empty prompt). Deliberately provider-agnostic — used only to skip
    obviously-too-large providers before making a call.
    """
    words = len(prompt.split())
    return int(words * 1.3) + 1


def _is_rate_limit(exc: Exception) -> bool:
    """Heuristically detect a rate-limit error from its text (429 / "rate")."""
    text = str(exc).lower()
    return "429" in text or "rate limit" in text or "ratelimit" in text


def execute_with_cascade(
    prompt: str,
    cascade_config: CascadeConfig,
    provider_factory: Callable[[str], Any],
    **provider_kwargs: Any,
) -> tuple[str, str]:
    """Execute ``prompt`` against the cascade, returning ``(response, provider)``.

    Tries ``primary`` then each fallback in order. A provider is skipped (without
    consuming an attempt) if it cannot be loaded or if ``prompt`` is estimated to
    exceed its ``MAX_CONTEXT_TOKENS`` (when ``fallback_on_context_exceeded``).
    Each provider actually called consumes one attempt; the cascade stops after
    ``max_fallback_attempts``.

    Raises:
        CascadeExhaustedError: ``PK-AI-001`` when no provider succeeds.
    """
    providers_to_try = [cascade_config.primary, *cascade_config.fallbacks]
    prompt_tokens = estimate_prompt_tokens(prompt)
    attempts = 0
    last_error: Exception | None = None
    skipped_for_context = False

    for provider_name in providers_to_try:
        if attempts >= cascade_config.max_fallback_attempts:
            break

        try:
            provider = provider_factory(provider_name)
        except Exception as exc:  # noqa: BLE001 — any load failure → next provider
            last_error = exc
            logger.info("[AI Cascade] Cannot load provider %s: %s", provider_name, exc)
            continue

        max_context = getattr(
            provider, "MAX_CONTEXT_TOKENS", _DEFAULT_MAX_CONTEXT_TOKENS
        )
        if cascade_config.fallback_on_context_exceeded and prompt_tokens > max_context:
            skipped_for_context = True
            logger.info(
                "[AI Cascade] Skipping %s: prompt ~%d tokens exceeds %d limit",
                provider_name,
                prompt_tokens,
                max_context,
            )
            continue

        attempts += 1
        try:
            logger.info(
                "[AI Cascade] Attempting provider: %s (attempt %d)",
                provider_name,
                attempts,
            )
            result = provider.complete(prompt, **provider_kwargs)
            logger.info("[AI Cascade] Success with provider: %s", provider_name)
            return result, provider_name
        except Exception as exc:  # noqa: BLE001 — provider failure → next provider
            last_error = exc
            if _is_rate_limit(exc) and not cascade_config.fallback_on_rate_limit:
                raise
            logger.info(
                "[AI Cascade] %s failed: %s, trying fallback",
                provider_name,
                type(exc).__name__,
            )
            continue

    if attempts == 0 and skipped_for_context:
        raise CascadeExhaustedError(
            f"Prompt (~{prompt_tokens} tokens) exceeds the context window of "
            "every configured provider. Add a larger-context provider "
            "(e.g. kimi / moonshot-v1-128k).",
            {"prompt_tokens": prompt_tokens},
        )
    raise CascadeExhaustedError(
        f"All providers exhausted after {attempts} attempt(s). "
        f"Last error: {last_error}",
        {"attempts": attempts, "last_error": str(last_error)},
    )


def _extract_ai_config(config: Any) -> dict:
    """Return the ``ai`` cascade section from a config object, or ``{}``.

    The strict Pydantic ``PipelineConfig`` has no ``ai`` section, so cascade
    config is env-var-driven in practice; this helper keeps the door open for a
    dict-shaped config (or a future model) that carries one.
    """
    if config is None:
        return {}
    if isinstance(config, dict):
        section = config.get("ai", {})
        return section if isinstance(section, dict) else {}
    section = getattr(config, "ai", None)
    if section is None:
        return {}
    if isinstance(section, dict):
        return section
    model_dump = getattr(section, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        return dumped if isinstance(dumped, dict) else {}
    return {}


def _as_bool(value: Any, default: bool = True) -> bool:
    """Coerce a config/env value to bool (accepts true/1/yes/on)."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_cascade_config(config: Any = None) -> CascadeConfig:
    """Build a ``CascadeConfig`` from environment variables (and optional config).

    Environment variables take precedence:

    * ``PIPELINEKIT_AI_PRIMARY`` — primary provider name.
    * ``PIPELINEKIT_AI_FALLBACKS`` — comma-separated ordered fallbacks.

    With nothing configured, returns single-provider behavior (primary
    ``anthropic``, no fallbacks) — unchanged from before.
    """
    ai_cfg = _extract_ai_config(config)

    primary = (
        os.getenv("PIPELINEKIT_AI_PRIMARY") or ai_cfg.get("primary") or "anthropic"
    )

    fallbacks_env = os.getenv("PIPELINEKIT_AI_FALLBACKS", "").strip()
    if fallbacks_env:
        fallbacks = [name.strip() for name in fallbacks_env.split(",") if name.strip()]
    else:
        fallbacks = list(ai_cfg.get("fallbacks", []) or [])

    return CascadeConfig(
        primary=primary,
        fallbacks=fallbacks,
        fallback_on_rate_limit=_as_bool(ai_cfg.get("fallback_on_rate_limit", True)),
        fallback_on_context_exceeded=_as_bool(
            ai_cfg.get("fallback_on_context_exceeded", True)
        ),
        max_fallback_attempts=int(ai_cfg.get("max_fallback_attempts", 3)),
    )
