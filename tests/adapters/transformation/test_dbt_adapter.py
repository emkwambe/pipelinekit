"""Tests for DbtTransformationAdapter (SPEC-009). subprocess is mocked."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from pipelinekit.adapters.transformation.dbt.adapter import DbtTransformationAdapter
from pipelinekit.config.schema import TransformationSection

_MODULE = "pipelinekit.adapters.transformation.dbt.adapter"


def _config(tmp_path) -> TransformationSection:
    return TransformationSection(enabled=True, project_dir=str(tmp_path))


def test_execute_success_on_exit_zero(tmp_path):
    """execute() returns success when dbt build exits 0."""
    completed = MagicMock(returncode=0, stdout="", stderr="")
    adapter = DbtTransformationAdapter(_config(tmp_path))
    with patch(f"{_MODULE}.subprocess.run", return_value=completed):
        result = adapter.execute()

    assert result.status.value == "success"
    assert result.step == "transformation"


def test_execute_maps_exit_one_to_adapter_002(tmp_path):
    """execute() maps a non-zero dbt exit code to PK-ADAPTER-002."""
    completed = MagicMock(returncode=1, stdout="", stderr="error")
    adapter = DbtTransformationAdapter(_config(tmp_path))
    with patch(f"{_MODULE}.subprocess.run", return_value=completed):
        result = adapter.execute()

    assert result.status.value == "failed"
    assert result.error_code == "PK-ADAPTER-002"


def test_validate_runs_dbt_parse(tmp_path):
    """validate() runs `dbt parse` and returns a valid StepResult on exit 0."""
    completed = MagicMock(returncode=0, stdout="", stderr="")
    adapter = DbtTransformationAdapter(_config(tmp_path))
    with patch(f"{_MODULE}.subprocess.run", return_value=completed) as mock_run:
        result = adapter.validate()

    assert result.status.value == "valid"
    assert "parse" in mock_run.call_args.args[0]


def test_initialize_missing_dir_is_safe(tmp_path):
    """initialize() does not raise when the project dir is absent."""
    adapter = DbtTransformationAdapter(
        TransformationSection(enabled=True, project_dir=str(tmp_path / "nope"))
    )
    adapter.initialize()


def test_execute_launch_failure_maps_to_adapter_002(tmp_path):
    """A subprocess launch failure on build maps to PK-ADAPTER-002."""
    adapter = DbtTransformationAdapter(_config(tmp_path))
    with patch(f"{_MODULE}.subprocess.run", side_effect=OSError("dbt missing")):
        result = adapter.execute()
    assert result.error_code == "PK-ADAPTER-002"


def test_validate_launch_failure_maps_to_adapter_001(tmp_path):
    """A subprocess launch failure on parse maps to PK-ADAPTER-001."""
    adapter = DbtTransformationAdapter(_config(tmp_path))
    with patch(f"{_MODULE}.subprocess.run", side_effect=OSError("dbt missing")):
        result = adapter.validate()
    assert result.status.value == "invalid"
    assert result.error_code == "PK-ADAPTER-001"


def test_execute_parses_run_results(tmp_path):
    """execute() parses run_results.json for pass counts."""
    target = tmp_path / "target"
    target.mkdir()
    (target / "run_results.json").write_text(
        json.dumps({"results": [{"status": "pass"}, {"status": "success"}]}),
        encoding="utf-8",
    )
    completed = MagicMock(returncode=0, stdout="", stderr="")
    adapter = DbtTransformationAdapter(_config(tmp_path))
    with patch(f"{_MODULE}.subprocess.run", return_value=completed):
        result = adapter.execute()

    assert result.status.value == "success"
    assert result.rows_processed == 2


def test_status_returns_structured_dict(tmp_path):
    """status() returns a structured dict describing the adapter."""
    adapter = DbtTransformationAdapter(_config(tmp_path))
    status = adapter.status()
    assert status["adapter"] == "dbt"
    assert status["step"] == "transformation"
