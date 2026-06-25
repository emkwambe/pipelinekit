"""Tests for MistralProvider (ADR-016). The mistralai SDK is never called."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction
from pipelinekit.ai.providers.mistral import MistralProvider
from pipelinekit.core.errors import LLMError

_RESPONSE = json.dumps(
    {
        "status": "diagnosed",
        "finding_type": "configuration_error",
        "confidence": 0.79,
        "evidence": [{"type": "config", "detail": "missing source"}],
        "recommended_actions": [
            {"action": "set source", "risk_level": "low", "reversible": True}
        ],
        "can_auto_fix": False,
        "explanation": "Source not configured.",
    }
)


def _evidence() -> EvidencePackage:
    return EvidencePackage(
        run_id="run-ml", pipeline_name="demo", pipeline_result={"status": "failed"}
    )


def test_diagnose_returns_result():
    """diagnose() parses a mocked API response into a DiagnosticResult."""
    provider = MistralProvider()
    with patch.object(provider, "_complete", return_value=_RESPONSE):
        result = provider.diagnose(_evidence())
    assert isinstance(result, DiagnosticResult)
    assert result.finding_type == "configuration_error"
    assert result.run_id == "run-ml"


def test_diagnose_missing_key_raises_ai_001(monkeypatch):
    """diagnose() raises LLMError(PK-AI-001) when MISTRAL_API_KEY is missing."""
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(LLMError) as exc_info:
        MistralProvider().diagnose(_evidence())
    assert exc_info.value.code == "PK-AI-001"


def test_complete_calls_sdk(monkeypatch):
    """_complete imports the SDK, calls the API, and returns the text (mocked)."""
    monkeypatch.setenv("MISTRAL_API_KEY", "ml-test")
    fake_sdk = MagicMock()
    choice = SimpleNamespace(message=SimpleNamespace(content=_RESPONSE))
    completion = SimpleNamespace(choices=[choice])
    fake_sdk.Mistral.return_value.chat.complete.return_value = completion
    with patch.dict(sys.modules, {"mistralai": fake_sdk}):
        result = MistralProvider().diagnose(_evidence())
    assert result.finding_type == "configuration_error"
    fake_sdk.Mistral.assert_called_once()


def test_summarize_and_recommend():
    """summarize() returns text and recommend() echoes the diagnosis actions."""
    provider = MistralProvider()
    with patch.object(provider, "_complete", return_value="a summary"):
        assert provider.summarize(["line 1"]) == "a summary"
    result = DiagnosticResult(
        status="diagnosed",
        finding_type="configuration_error",
        confidence=0.8,
        recommended_actions=[RecommendedAction(action="set source")],
    )
    assert provider.recommend(result) == result.recommended_actions


def test_mistralai_imports_isolated():
    """No source file outside the mistral provider imports mistralai."""
    src_root = Path(__file__).resolve().parents[3] / "src" / "pipelinekit"
    allowed = src_root / "ai" / "providers" / "mistral.py"
    offenders = []
    for path in src_root.rglob("*.py"):
        if path == allowed:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("import mistralai", "from mistralai")):
                offenders.append(str(path))
                break
    assert offenders == [], f"mistralai imported outside provider: {offenders}"
