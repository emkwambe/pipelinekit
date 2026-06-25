"""Tests for SourceConfig credential fields (ADR-017)."""

from __future__ import annotations

from pipelinekit.config.schema import SourceConfig


def test_source_config_accepts_credential_fields():
    """SourceConfig accepts the full ADR-017 credential surface."""
    source = SourceConfig(
        type="postgres",
        host="localhost",
        port=5432,
        database="analytics",
        user="admin",
        password="secret",
        tables=["orders", "customers"],
    )
    assert source.user == "admin"
    assert source.password == "secret"
    assert source.tables == ["orders", "customers"]


def test_source_config_snowflake_fields():
    """Snowflake-specific fields load, including the `schema` alias."""
    dest = SourceConfig(
        type="snowflake",
        account="acct",
        warehouse="wh",
        database="db",
        **{"schema": "raw"},
    )
    assert dest.account == "acct"
    assert dest.warehouse == "wh"
    assert dest.schema_name == "raw"


def test_source_config_schema_populate_by_name():
    """The schema field is settable by its Python name too (populate_by_name)."""
    dest = SourceConfig(type="snowflake", schema_name="staging")
    assert dest.schema_name == "staging"


def test_source_config_bigquery_and_duckdb_fields():
    """BigQuery and DuckDB descriptor fields load."""
    bq = SourceConfig(type="bigquery", project="my-proj", location="EU")
    duck = SourceConfig(type="duckdb", path="./local.duckdb")
    assert bq.project == "my-proj"
    assert bq.location == "EU"
    assert duck.path == "./local.duckdb"


def test_source_config_backward_compatible():
    """A minimal source without credentials still loads (no breaking change)."""
    source = SourceConfig(type="postgres", host="localhost", port=5432)
    assert source.type == "postgres"
    assert source.user is None
    assert source.password is None
    assert source.tables is None
