"""Tests for DepsChecker (SPEC-012). subprocess is mocked — no real poetry call."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from pipelinekit.health import INFO, OK, WARNING
from pipelinekit.health.deps import DepsChecker


def _completed(stdout: str = "", returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.stdout = stdout
    proc.stderr = ""
    proc.returncode = returncode
    return proc


def test_ok_when_no_outdated_packages():
    """All current → status ok."""
    with patch("pipelinekit.health.deps.subprocess.run", return_value=_completed("")):
        result = DepsChecker().check()
    assert result.status == OK


def test_warning_when_patch_update_available():
    """A patch update available → status warning."""
    output = "dlt 1.28.0 1.28.3 Data load tool for Python"
    with patch(
        "pipelinekit.health.deps.subprocess.run", return_value=_completed(output)
    ):
        result = DepsChecker().check()
    assert result.status == WARNING
    assert any("dlt" in d for d in result.details or [])


def test_info_when_poetry_unavailable():
    """Poetry not installed → status info (never an error)."""
    with patch(
        "pipelinekit.health.deps.subprocess.run",
        side_effect=FileNotFoundError("poetry"),
    ):
        result = DepsChecker().check()
    assert result.status == INFO


def test_error_when_major_update_available():
    """A major update available → status error (ADR required to upgrade)."""
    output = "anthropic 0.25.1 1.0.0 Anthropic SDK"
    with patch(
        "pipelinekit.health.deps.subprocess.run", return_value=_completed(output)
    ):
        result = DepsChecker().check()
    assert result.status == "error"


def test_info_when_poetry_returns_nonzero():
    """A non-zero poetry exit resolves to info, not a crash."""
    proc = _completed("", returncode=1)
    proc.stderr = "not a poetry project"
    with patch("pipelinekit.health.deps.subprocess.run", return_value=proc):
        result = DepsChecker().check()
    assert result.status == INFO


def test_info_when_poetry_times_out():
    """A subprocess timeout resolves to info, not a crash."""
    with patch(
        "pipelinekit.health.deps.subprocess.run",
        side_effect=subprocess.TimeoutExpired("poetry", 120),
    ):
        result = DepsChecker().check()
    assert result.status == INFO
