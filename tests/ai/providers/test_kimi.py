"""Tests for KimiProvider (ADR-041). The OpenAI-compatible SDK is never called.

Kimi (Moonshot AI) drives the ``openai`` SDK pointed at Moonshot's base URL, so
these mirror ``test_openai.py``: HTTP is always mocked via ``sys.modules``.
"""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.providers import create_provider, get_provider, list_providers
from pipelinekit.ai.providers.kimi import KIMI_MODELS, KimiProvider
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import LLMError

_RESPONSE = json.dumps(
    {
        "status": "diagnosed",
        "finding_type": "configuration_error",
        "confidence": 0.82,
        "evidence": [{"type": "config", "detail": "missing destination"}],
        "recommended_actions": [
            {"action": "set destination", "risk_level": "low", "reversible": True}
        ],
        "can_auto_fix": False,
        "explanation": "Destination not configured.",
    }
)


def _evidence() -> EvidencePackage:
    return EvidencePackage(
        run_id="run-k", pipeline_name="demo", pipeline_result={"status": "failed"}
    )


def _fake_sdk() -> MagicMock:
    """Return a mock OpenAI SDK whose completion yields ``_RESPONSE``."""
    fake_sdk = MagicMock()
    choice = SimpleNamespace(message=SimpleNamespace(content=_RESPONSE))
    completion = SimpleNamespace(choices=[choice])
    fake_sdk.OpenAI.return_value.chat.completions.create.return_value = completion
    return fake_sdk


def _config(provider: str) -> PipelineConfig:
    return PipelineConfig(
        **{
            "pipeline": {"name": "demo"},
            "runtime": {},
            "ingestion": {
                "source": {"type": "postgres"},
                "destination": {"type": "duckdb"},
            },
            "transformation": {},
            "contracts": {},
            "quality": {},
            "diagnostics": {"enabled": True, "provider": provider},
            "notifications": {},
        }
    )


def test_kimi_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """KimiProvider raises LLMError(PK-AI-001) when MOONSHOT_API_KEY is not set."""
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    with pytest.raises(LLMError) as exc_info:
        KimiProvider().diagnose(_evidence())
    assert exc_info.value.code == "PK-AI-001"


def test_kimi_provider_uses_correct_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """KimiProvider points the SDK at https://api.moonshot.cn/v1."""
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-test")
    fake_sdk = _fake_sdk()
    with patch.dict(sys.modules, {"openai": fake_sdk}):
        KimiProvider().diagnose(_evidence())
    fake_sdk.OpenAI.assert_called_once_with(
        api_key="sk-test", base_url="https://api.moonshot.cn/v1"
    )


def test_kimi_provider_default_model_is_32k() -> None:
    """KimiProvider defaults to moonshot-v1-32k."""
    assert KimiProvider().model == "moonshot-v1-32k"


def test_kimi_provider_accepts_128k_model() -> None:
    """KimiProvider accepts the moonshot-v1-128k model."""
    provider = KimiProvider("moonshot-v1-128k")
    assert provider.model == "moonshot-v1-128k"
    assert "moonshot-v1-128k" in KIMI_MODELS


def test_kimi_provider_complete_returns_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_complete returns the string response from the mocked SDK."""
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-test")
    fake_sdk = _fake_sdk()
    with patch.dict(sys.modules, {"openai": fake_sdk}):
        result = KimiProvider()._complete("system", "user")
    assert isinstance(result, str)
    assert result == _RESPONSE


def test_kimi_provider_registered_in_factory() -> None:
    """'kimi' is a valid provider name resolvable via the factory."""
    assert "kimi" in list_providers()
    assert isinstance(get_provider("kimi"), KimiProvider)
    assert isinstance(create_provider(_config("kimi")), KimiProvider)


def test_kimi_provider_message_format_is_openai_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KimiProvider sends system+user messages in OpenAI-compatible format."""
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-test")
    fake_sdk = _fake_sdk()
    with patch.dict(sys.modules, {"openai": fake_sdk}):
        KimiProvider().diagnose(_evidence())
    create_call = fake_sdk.OpenAI.return_value.chat.completions.create
    messages = create_call.call_args.kwargs["messages"]
    assert [m["role"] for m in messages] == ["system", "user"]
    assert all(set(m.keys()) == {"role", "content"} for m in messages)
    assert create_call.call_args.kwargs["model"] == "moonshot-v1-32k"
