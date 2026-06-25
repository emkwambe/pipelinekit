"""Tests for the configuration loader (SPEC-002)."""

from __future__ import annotations

import pytest
from pipelinekit.config.loader import (
    config_exists,
    load_config,
    write_default_config,
)
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import ConfigurationError


def test_load_config_valid(tmp_path):
    """load_config returns a PipelineConfig on a valid file."""
    write_default_config(tmp_path)
    config = load_config(tmp_path)
    assert isinstance(config, PipelineConfig)
    assert config.pipeline.name == "my-project"


def test_load_config_not_found(tmp_path):
    """load_config raises PK-CONFIG-003 when the file is absent."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_config(tmp_path)
    assert exc_info.value.code == "PK-CONFIG-003"


def test_load_config_invalid_yaml(tmp_path):
    """load_config raises PK-CONFIG-004 on malformed YAML."""
    (tmp_path / "pipelinekit.yaml").write_text(
        "pipeline: [unclosed\n", encoding="utf-8"
    )
    with pytest.raises(ConfigurationError) as exc_info:
        load_config(tmp_path)
    assert exc_info.value.code == "PK-CONFIG-004"


def test_load_config_schema_violation(tmp_path):
    """load_config raises PK-CONFIG-001 when a required section is missing."""
    (tmp_path / "pipelinekit.yaml").write_text(
        "pipeline:\n  name: demo\n", encoding="utf-8"
    )
    with pytest.raises(ConfigurationError) as exc_info:
        load_config(tmp_path)
    assert exc_info.value.code == "PK-CONFIG-001"
    assert exc_info.value.context["errors"]


def test_write_default_config(tmp_path):
    """write_default_config creates a file that passes load_config."""
    write_default_config(tmp_path)
    assert (tmp_path / "pipelinekit.yaml").is_file()
    config = load_config(tmp_path)
    assert isinstance(config, PipelineConfig)


def test_config_exists_true(tmp_path):
    """config_exists returns True when the file is present."""
    write_default_config(tmp_path)
    assert config_exists(tmp_path) is True


def test_config_exists_false(tmp_path):
    """config_exists returns False when the file is absent."""
    assert config_exists(tmp_path) is False
