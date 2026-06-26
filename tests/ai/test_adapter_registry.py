"""Tests for AdapterCapabilityRegistry (SPEC-015)."""

from __future__ import annotations

from pipelinekit.ai.adapter_registry import AdapterCapabilityRegistry


def test_supported_sources_return_true():
    """postgres, salesforce, stripe are supported sources."""
    reg = AdapterCapabilityRegistry()
    assert reg.is_source_supported("postgres")
    assert reg.is_source_supported("salesforce")
    assert reg.is_source_supported("stripe")


def test_unsupported_sources_return_false():
    """oracle and mysql are not supported."""
    reg = AdapterCapabilityRegistry()
    assert not reg.is_source_supported("oracle")
    assert not reg.is_source_supported("mysql")


def test_source_verified_flag():
    """postgres is PipelineKit-verified; salesforce and stripe are not (SPEC-016)."""
    reg = AdapterCapabilityRegistry()
    assert reg.is_source_verified("postgres") is True
    assert reg.is_source_verified("salesforce") is False
    assert reg.is_source_verified("stripe") is False
    # Unknown sources are treated as unverified.
    assert reg.is_source_verified("oracle") is False


def test_get_supported_tables_for_salesforce():
    """Salesforce returns its fixed object list."""
    reg = AdapterCapabilityRegistry()
    tables = reg.get_supported_tables("salesforce")
    assert "opportunities" in tables
    assert "accounts" in tables
    # Postgres accepts any table.
    assert reg.get_supported_tables("postgres") == "configurable"
