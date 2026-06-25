"""Tests for ${VAR} env interpolation in the config loader (ADR-017)."""

from __future__ import annotations

from pipelinekit.config.loader import _interpolate_env_vars, load_config


def test_interpolate_env_vars_string(monkeypatch):
    """A ${VAR} reference is replaced with the environment value."""
    monkeypatch.setenv("PK_TEST_HOST", "db.internal")
    assert _interpolate_env_vars("${PK_TEST_HOST}") == "db.internal"
    assert _interpolate_env_vars("host=${PK_TEST_HOST}:5432") == "host=db.internal:5432"


def test_interpolate_env_vars_unset(monkeypatch):
    """An unset variable resolves to an empty string and never raises."""
    monkeypatch.delenv("PK_TEST_MISSING", raising=False)
    assert _interpolate_env_vars("${PK_TEST_MISSING}") == ""
    assert _interpolate_env_vars({"k": "${PK_TEST_MISSING}"}) == {"k": ""}


def test_interpolate_env_vars_recurses_dict_and_list(monkeypatch):
    """Interpolation recurses through nested dicts and lists."""
    monkeypatch.setenv("PK_TEST_DB", "analytics")
    obj = {
        "ingestion": {
            "source": {"database": "${PK_TEST_DB}", "tables": ["${PK_TEST_DB}"]}
        }
    }
    result = _interpolate_env_vars(obj)
    assert result["ingestion"]["source"]["database"] == "analytics"
    assert result["ingestion"]["source"]["tables"] == ["analytics"]


def test_interpolate_env_vars_passthrough_non_strings():
    """Non-string scalars pass through unchanged."""
    assert _interpolate_env_vars(5432) == 5432
    assert _interpolate_env_vars(True) is True
    assert _interpolate_env_vars(None) is None


def test_load_config_interpolates_before_validation(tmp_path, monkeypatch):
    """load_config() expands ${VAR} so config carries resolved values."""
    monkeypatch.setenv("PK_TEST_PGHOST", "postgres.prod")
    monkeypatch.setenv("PK_TEST_SFACCOUNT", "acme-xy123")
    (tmp_path / "pipelinekit.yaml").write_text(
        """
pipeline:
  name: demo
runtime:
  environment: local
ingestion:
  source:
    type: postgres
    host: "${PK_TEST_PGHOST}"
    port: 5432
  destination:
    type: snowflake
    account: "${PK_TEST_SFACCOUNT}"
transformation:
  enabled: false
contracts:
  enabled: true
quality:
  enabled: false
diagnostics:
  enabled: false
  provider: none
notifications:
  enabled: false
""",
        encoding="utf-8",
    )
    config = load_config(cwd=tmp_path)
    assert config.ingestion.source.host == "postgres.prod"
    assert config.ingestion.destination.account == "acme-xy123"
