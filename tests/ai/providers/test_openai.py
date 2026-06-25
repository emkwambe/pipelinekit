"""Tests for OpenAIProvider (SPEC-005). OpenAI SDK is never called."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction
from pipelinekit.ai.providers.openai import OpenAIProvider
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
        run_id="run-2", pipeline_name="demo", pipeline_result={"status": "failed"}
    )


def test_diagnose_returns_result():
    """diagnose() parses a mocked API response into a DiagnosticResult."""
    provider = OpenAIProvider()
    with patch.object(provider, "_complete", return_value=_RESPONSE):
        result = provider.diagnose(_evidence())
    assert isinstance(result, DiagnosticResult)
    assert result.finding_type == "configuration_error"


def test_diagnose_missing_key_raises_ai_001(monkeypatch):
    """diagnose() raises LLMError(PK-AI-001) when the API key is missing."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LLMError) as exc_info:
        OpenAIProvider().diagnose(_evidence())
    assert exc_info.value.code == "PK-AI-001"


def test_complete_calls_sdk(monkeypatch):
    """_complete imports the SDK, calls the API, and returns the text (mocked)."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    fake_sdk = MagicMock()
    choice = SimpleNamespace(message=SimpleNamespace(content=_RESPONSE))
    completion = SimpleNamespace(choices=[choice])
    fake_sdk.OpenAI.return_value.chat.completions.create.return_value = completion
    with patch.dict(sys.modules, {"openai": fake_sdk}):
        result = OpenAIProvider().diagnose(_evidence())
    assert result.finding_type == "configuration_error"
    fake_sdk.OpenAI.assert_called_once()


def test_summarize_and_recommend():
    """summarize() returns text and recommend() echoes the diagnosis actions."""
    provider = OpenAIProvider()
    with patch.object(provider, "_complete", return_value="ok"):
        assert provider.summarize(["x"]) == "ok"
    result = DiagnosticResult(
        status="diagnosed",
        finding_type="configuration_error",
        confidence=0.8,
        recommended_actions=[RecommendedAction(action="set destination")],
    )
    assert provider.recommend(result) == result.recommended_actions


def test_openai_imports_isolated():
    """No source file outside the openai provider imports openai."""
    src_root = Path(__file__).resolve().parents[3] / "src" / "pipelinekit"
    allowed = src_root / "ai" / "providers" / "openai.py"
    offenders = []
    for path in src_root.rglob("*.py"):
        if path == allowed:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("import openai", "from openai")):
                offenders.append(str(path))
                break
    assert offenders == [], f"openai imported outside provider: {offenders}"
