"""Tests for SodaQualityAdapter (SPEC-009). Soda is mocked — no real database."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pipelinekit.adapters.quality.soda.adapter import SodaQualityAdapter
from pipelinekit.config.schema import QualitySection


def _config(checks_dir: str) -> QualitySection:
    return QualitySection(enabled=True, checks_dir=checks_dir)


def _scan(pass_count: int, fail_count: int, warn_count: int = 0) -> MagicMock:
    """Mock a Soda Scan using the real get_scan_results() API.

    soda-core exposes results as a dict whose ``checks`` entries each carry an
    ``outcome`` of ``pass`` | ``fail`` | ``warn`` (CheckOutcome). The adapter
    counts these outcomes — the removed get_checks_*_count() methods are gone.
    """
    checks = (
        [{"outcome": "pass"}] * pass_count
        + [{"outcome": "fail"}] * fail_count
        + [{"outcome": "warn"}] * warn_count
    )
    scan = MagicMock()
    scan.execute.return_value = 0
    scan.get_scan_results.return_value = {"checks": checks}
    return scan


def test_execute_returns_pass_fail_counts(tmp_path):
    """execute() returns success with the reported pass count (mocked Soda)."""
    adapter = SodaQualityAdapter(_config(str(tmp_path)))
    with patch("soda.scan.Scan", return_value=_scan(pass_count=5, fail_count=0)):
        result = adapter.execute()

    assert result.status.value == "success"
    assert result.rows_processed == 5


def test_execute_maps_failure_to_adapter_002(tmp_path):
    """execute() maps failing Soda checks to PK-ADAPTER-002."""
    adapter = SodaQualityAdapter(_config(str(tmp_path)))
    with patch("soda.scan.Scan", return_value=_scan(pass_count=3, fail_count=2)):
        result = adapter.execute()

    assert result.status.value == "failed"
    assert result.error_code == "PK-ADAPTER-002"


def test_validate_checks_directory_exists(tmp_path):
    """validate() returns valid when the checks directory exists."""
    adapter = SodaQualityAdapter(_config(str(tmp_path)))
    result = adapter.validate()

    assert result.status.value == "valid"
    assert result.step == "quality"


def test_validate_missing_directory_is_invalid(tmp_path):
    """validate() returns invalid with PK-ADAPTER-001 when the dir is absent."""
    adapter = SodaQualityAdapter(_config(str(tmp_path / "nope")))
    result = adapter.validate()
    assert result.status.value == "invalid"
    assert result.error_code == "PK-ADAPTER-001"


def test_initialize_and_status(tmp_path):
    """initialize() is safe and status() returns a structured dict."""
    adapter = SodaQualityAdapter(_config(str(tmp_path)))
    adapter.initialize()
    status = adapter.status()
    assert status["adapter"] == "soda"
    assert status["step"] == "quality"
