"""Tests for the Remote Blueprint Registry (SPEC-016). All network calls mocked."""

from __future__ import annotations

import io
import json
import zipfile
from unittest.mock import MagicMock, patch

import pytest
from pipelinekit.blueprints.remote import (
    CATALOG_URL,
    BlueprintCatalog,
    CatalogEntry,
    RemoteRegistry,
)
from pipelinekit.cli.main import app
from pipelinekit.core.errors import RegistryError
from typer.testing import CliRunner

runner = CliRunner()


def _entry(verified: bool = True) -> CatalogEntry:
    return CatalogEntry(
        name="stripe-to-snowflake",
        version="1.0.0",
        description="Stripe to Snowflake",
        source="stripe",
        destination="snowflake",
        verified=verified,
        verified_at=None,
        verified_by=None,
        downloads=0,
        tags=["stripe"],
        url="https://registry.pipelinekit.dev/v1/blueprints/stripe-to-snowflake-1.0.0.zip",
    )


_CATALOG = {
    "version": "1.0",
    "updated_at": "2026-06-26T00:00:00Z",
    "blueprints": [
        {
            "name": "stripe-to-snowflake",
            "version": "1.0.0",
            "description": "Stripe CRM to Snowflake",
            "source": "stripe",
            "destination": "snowflake",
            "verified": True,
            "verified_at": "2026-06-26",
            "verified_by": "mpingo-systems",
            "downloads": 0,
            "tags": ["stripe", "snowflake", "payments"],
            "url": "https://registry.pipelinekit.dev/v1/blueprints/stripe-to-snowflake-1.0.0.zip",
        },
        {
            "name": "postgres-to-snowflake",
            "version": "1.0.0",
            "description": "Postgres to Snowflake",
            "source": "postgres",
            "destination": "snowflake",
            "verified": True,
            "verified_at": "2026-06-26",
            "verified_by": "mpingo-systems",
            "downloads": 0,
            "tags": ["postgres", "sql"],
            "url": "https://registry.pipelinekit.dev/v1/blueprints/postgres-to-snowflake-1.0.0.zip",
        },
    ],
}

_VALID_BLUEPRINT_JSON = json.dumps(
    {
        "name": "stripe-to-snowflake",
        "version": "1.0.0",
        "source": {"type": "stripe", "dlt_source": "stripe_analytics"},
        "destination": {"type": "snowflake", "dlt_destination": "snowflake"},
        "contracts": ["contracts/charges.yaml"],
    }
)


def _make_zip(blueprint_json: str, all_assets: bool = True) -> bytes:
    """Build an in-memory blueprint zip with the (lenient) required assets."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("blueprint.json", blueprint_json)
        if all_assets:
            for path in (
                "ingestion/pipeline.py",
                "transform/dbt_project.yml",
                "contracts/charges.yaml",
                "quality/checks.yaml",
                "alerts/config.yaml",
                "docs/README.md",
                "docs/runbook.md",
            ):
                zf.writestr(path, "x\n")
    return buf.getvalue()


def _http_dispatcher(zip_bytes: bytes):
    """Return an _http_get side effect: catalog for CATALOG_URL, else the zip."""

    def _http(url: str) -> bytes:
        if url == CATALOG_URL:
            return json.dumps(_CATALOG).encode("utf-8")
        return zip_bytes

    return _http


def test_fetch_catalog_from_http(tmp_path):
    """fetch_catalog() returns a BlueprintCatalog from a mocked HTTP response."""
    registry = RemoteRegistry(cache_dir=tmp_path / "cache")
    with patch.object(
        registry, "_http_get", return_value=json.dumps(_CATALOG).encode("utf-8")
    ):
        catalog = registry.fetch_catalog()
    assert isinstance(catalog, BlueprintCatalog)
    assert len(catalog.blueprints) == 2


def test_fetch_catalog_uses_cache_within_ttl(tmp_path):
    """A fresh cache is returned without touching the network."""
    registry = RemoteRegistry(cache_dir=tmp_path)
    registry._write_cache(BlueprintCatalog.from_dict(_CATALOG))
    with patch.object(
        registry, "_http_get", side_effect=AssertionError("network must not be called")
    ):
        catalog = registry.fetch_catalog()
    assert catalog.version == "1.0"


def test_search_matches_name_source_destination_tag(tmp_path):
    """search() matches by name, source, destination, and tag."""
    registry = RemoteRegistry(cache_dir=tmp_path)
    registry._write_cache(BlueprintCatalog.from_dict(_CATALOG))
    assert any(r.name == "stripe-to-snowflake" for r in registry.search("stripe"))
    assert any(r.source == "postgres" for r in registry.search("postgres"))
    assert any(r.destination == "snowflake" for r in registry.search("snowflake"))
    assert any(r.name == "stripe-to-snowflake" for r in registry.search("payments"))


def test_install_writes_blueprint(tmp_path):
    """install() validates then writes the blueprint to blueprints/<name>/."""
    registry = RemoteRegistry(cache_dir=tmp_path / "cache")
    with patch.object(
        registry,
        "_http_get",
        side_effect=_http_dispatcher(_make_zip(_VALID_BLUEPRINT_JSON)),
    ):
        version = registry.install("stripe-to-snowflake", cwd=tmp_path)
    assert version == "1.0.0"
    bp = tmp_path / "blueprints" / "stripe-to-snowflake"
    assert (bp / "blueprint.json").is_file()
    assert (bp / "ingestion" / "pipeline.py").is_file()


def test_install_raises_pk_registry_002_on_invalid_schema(tmp_path):
    """A blueprint failing schema validation raises PK-REGISTRY-002, writes nothing."""
    bad = _make_zip(json.dumps({"name": "stripe-to-snowflake"}))  # missing fields
    registry = RemoteRegistry(cache_dir=tmp_path / "cache")
    with patch.object(registry, "_http_get", side_effect=_http_dispatcher(bad)):
        with pytest.raises(RegistryError) as exc_info:
            registry.install("stripe-to-snowflake", cwd=tmp_path)
    assert exc_info.value.code == "PK-REGISTRY-002"
    assert not (tmp_path / "blueprints" / "stripe-to-snowflake").exists()


def test_install_raises_pk_registry_003_when_already_installed(tmp_path):
    """install() raises PK-REGISTRY-003 when the blueprint dir already exists."""
    (tmp_path / "blueprints" / "stripe-to-snowflake").mkdir(parents=True)
    registry = RemoteRegistry(cache_dir=tmp_path / "cache")
    with patch.object(
        registry,
        "_http_get",
        side_effect=_http_dispatcher(_make_zip(_VALID_BLUEPRINT_JSON)),
    ):
        with pytest.raises(RegistryError) as exc_info:
            registry.install("stripe-to-snowflake", cwd=tmp_path)
    assert exc_info.value.code == "PK-REGISTRY-003"


# -- CLI: blueprint search / install (RemoteRegistry mocked) -----------------


def test_cli_search_lists_matches(tmp_path, monkeypatch):
    """blueprint search renders matching catalog entries."""
    monkeypatch.chdir(tmp_path)
    reg = MagicMock()
    reg.search.return_value = [_entry()]
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "search", "stripe"])
    assert result.exit_code == 0
    assert "stripe-to-snowflake" in result.stdout


def test_cli_search_no_results(tmp_path, monkeypatch):
    """blueprint search reports when nothing matches."""
    monkeypatch.chdir(tmp_path)
    reg = MagicMock()
    reg.search.return_value = []
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "search", "nope"])
    assert result.exit_code == 0
    assert "No blueprints found" in result.stdout


def test_cli_install_verified(tmp_path, monkeypatch):
    """blueprint install reports success and the verified badge."""
    monkeypatch.chdir(tmp_path)
    reg = MagicMock()
    reg.install.return_value = "1.0.0"
    reg.fetch_catalog.return_value = BlueprintCatalog(
        version="1.0", updated_at="", blueprints=[_entry(verified=True)]
    )
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "install", "stripe-to-snowflake"])
    assert result.exit_code == 0
    assert "installed" in result.stdout
    assert "Verified" in result.stdout


def test_cli_install_unverified_warns(tmp_path, monkeypatch):
    """blueprint install warns when the blueprint is unverified."""
    monkeypatch.chdir(tmp_path)
    reg = MagicMock()
    reg.install.return_value = "1.0.0"
    reg.fetch_catalog.return_value = BlueprintCatalog(
        version="1.0", updated_at="", blueprints=[_entry(verified=False)]
    )
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "install", "stripe-to-snowflake"])
    assert result.exit_code == 0
    assert "not been verified" in result.stdout


def test_cli_install_error_surfaces_pk_registry_code(tmp_path, monkeypatch):
    """A RegistryError from install surfaces its PK-REGISTRY code and exits 1."""
    monkeypatch.chdir(tmp_path)
    reg = MagicMock()
    reg.install.side_effect = RegistryError(
        "PK-REGISTRY-004", "Blueprint not found in catalog: nope", {}
    )
    with patch("pipelinekit.cli.blueprint.RemoteRegistry", return_value=reg):
        result = runner.invoke(app, ["blueprint", "install", "nope"])
    assert result.exit_code == 1
    assert "PK-REGISTRY-004" in result.stdout
