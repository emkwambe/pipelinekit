"""Tests for SecurityChecker (SPEC-012). subprocess/pip-audit is mocked."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from pipelinekit.health import INFO, OK, WARNING
from pipelinekit.health.security import SecurityChecker


def _completed(stdout: str = "{}", returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.stdout = stdout
    proc.returncode = returncode
    return proc


def test_info_when_pip_audit_missing():
    """pip-audit not installed → status info with install hint."""
    with patch(
        "pipelinekit.health.security.subprocess.run",
        side_effect=FileNotFoundError("pip-audit"),
    ):
        result = SecurityChecker().check()
    assert result.status == INFO
    assert "pip-audit" in (result.fix_hint or "")


def test_ok_when_no_vulnerabilities():
    """No vulns in pip-audit output → status ok."""
    output = json.dumps(
        {"dependencies": [{"name": "requests", "version": "2.0", "vulns": []}]}
    )
    with patch(
        "pipelinekit.health.security.subprocess.run",
        return_value=_completed(output),
    ):
        result = SecurityChecker().check()
    assert result.status == OK


def test_warning_when_vulnerabilities_found():
    """Vulnerabilities present → status warning with details."""
    output = json.dumps(
        {
            "dependencies": [
                {"name": "evil", "version": "1.0", "vulns": [{"id": "CVE-2026-1"}]}
            ]
        }
    )
    with patch(
        "pipelinekit.health.security.subprocess.run",
        return_value=_completed(output),
    ):
        result = SecurityChecker().check()
    assert result.status == WARNING
    assert any("evil" in d for d in result.details or [])


def test_info_when_output_unparseable():
    """Non-JSON pip-audit output → status info, never a crash."""
    with patch(
        "pipelinekit.health.security.subprocess.run",
        return_value=_completed("not json"),
    ):
        result = SecurityChecker().check()
    assert result.status == INFO
