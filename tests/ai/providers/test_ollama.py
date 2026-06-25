"""Tests for OllamaProvider (SPEC-005). Ollama server is never contacted."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pipelinekit.ai.evidence import EvidencePackage
from pipelinekit.ai.models import DiagnosticResult, RecommendedAction
from pipelinekit.ai.providers.ollama import OllamaProvider
from pipelinekit.core.errors import LLMError

_RESPONSE = json.dumps(
    {
        "status": "diagnosed",
        "finding_type": "freshness_violation",
        "confidence": 0.77,
        "evidence": [{"type": "contract", "detail": "PK-CONTRACT-002"}],
        "recommended_actions": [
            {"action": "increase run frequency", "risk_level": "low"}
        ],
        "can_auto_fix": False,
        "explanation": "Data is stale.",
    }
)


def _evidence() -> EvidencePackage:
    return EvidencePackage(
        run_id="run-3", pipeline_name="demo", pipeline_result={"status": "failed"}
    )


def test_diagnose_returns_result():
    """diagnose() parses a mocked local response into a DiagnosticResult."""
    provider = OllamaProvider()
    with patch.object(provider, "_complete", return_value=_RESPONSE):
        result = provider.diagnose(_evidence())
    assert isinstance(result, DiagnosticResult)
    assert result.finding_type == "freshness_violation"


def test_default_host_when_env_missing(monkeypatch):
    """OllamaProvider falls back to the default host when OLLAMA_HOST is unset."""
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    provider = OllamaProvider()
    assert provider.host == "http://localhost:11434"


def test_complete_calls_client(monkeypatch):
    """_complete imports the SDK, calls the local server, returns text (mocked)."""
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
    fake_sdk = MagicMock()
    fake_sdk.Client.return_value.chat.return_value = {"message": {"content": _RESPONSE}}
    with patch.dict(sys.modules, {"ollama": fake_sdk}):
        result = OllamaProvider().diagnose(_evidence())
    assert result.finding_type == "freshness_violation"
    fake_sdk.Client.assert_called_once()


def test_complete_unreachable_raises_ai_001():
    """A transport failure maps to LLMError(PK-AI-001)."""
    fake_sdk = MagicMock()
    fake_sdk.Client.return_value.chat.side_effect = Exception("connection refused")
    with patch.dict(sys.modules, {"ollama": fake_sdk}):
        with pytest.raises(LLMError) as exc_info:
            OllamaProvider().diagnose(_evidence())
    assert exc_info.value.code == "PK-AI-001"


def test_summarize_and_recommend():
    """summarize() returns text and recommend() echoes the diagnosis actions."""
    provider = OllamaProvider()
    with patch.object(provider, "_complete", return_value="done"):
        assert provider.summarize(["y"]) == "done"
    result = DiagnosticResult(
        status="diagnosed",
        finding_type="freshness_violation",
        confidence=0.77,
        recommended_actions=[RecommendedAction(action="increase frequency")],
    )
    assert provider.recommend(result) == result.recommended_actions


def test_ollama_imports_isolated():
    """No source file outside the ollama provider imports ollama."""
    src_root = Path(__file__).resolve().parents[3] / "src" / "pipelinekit"
    allowed = src_root / "ai" / "providers" / "ollama.py"
    offenders = []
    for path in src_root.rglob("*.py"):
        if path == allowed:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ollama", "from ollama")):
                offenders.append(str(path))
                break
    assert offenders == [], f"ollama imported outside provider: {offenders}"
