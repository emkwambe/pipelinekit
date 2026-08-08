"""Tests for the data-mesh-contracts blueprint (Sprint E4).

Validates the blueprint's metadata, the Frame → Detail → Core → Utility
structure, and that it holds Grade A against QM-10. Structure only — no live
source, no dbt run. Follows the blueprint test pattern in test_blueprint_002.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pipelinekit.blueprints.models import BlueprintMetadata
from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.blueprints.validator import BlueprintValidator
from pipelinekit.quality.best_practices import check_blueprint_best_practices

_REPO = Path(__file__).resolve().parents[2]
_BLUEPRINTS = _REPO / "blueprints"
_MESH = _BLUEPRINTS / "data-mesh-contracts"
_MODELS = _MESH / "transform" / "models"

_DOMAINS = ("finance", "sales", "product")
_MODEL_NAMES = (
    "frame_contracts",
    "detail_finance_contracts",
    "detail_sales_contracts",
    "detail_product_contracts",
    "core_contracts",
)


def _schema_models(path: Path) -> list[dict]:
    """Return the model entries declared in a schema.yml."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [m for m in (data.get("models") or []) if isinstance(m, dict)]


def _all_models() -> dict[str, dict]:
    """Map model name -> its schema.yml entry, across every model directory."""
    models: dict[str, dict] = {}
    for schema_path in sorted(_MODELS.rglob("schema.yml")):
        for model in _schema_models(schema_path):
            if model.get("name"):
                models[model["name"]] = model
    return models


def test_e4_blueprint_json_is_valid() -> None:
    """blueprint.json validates against the schema and declares the mesh pattern."""
    BlueprintValidator().validate(_MESH)  # raises BlueprintError on invalid

    meta = BlueprintRegistry(_BLUEPRINTS).get("data-mesh-contracts")
    assert isinstance(meta, BlueprintMetadata)
    assert meta.name == "data-mesh-contracts"
    assert meta.source.type == "postgres"
    assert meta.destination.type == "duckdb"

    raw = json.loads((_MESH / "blueprint.json").read_text(encoding="utf-8"))
    # Never run end-to-end, so it must not claim a verified quality baseline.
    assert raw["status"] == "proposed"
    assert raw["data_mesh"]["pattern"] == "frame_detail_core_utility"
    assert raw["data_mesh"]["frame_table"] == "frame_contracts"
    assert set(raw["data_mesh"]["domains"]) == {
        "engineering",
        "finance",
        "sales",
        "product",
    }


def test_e4_frame_model_has_primary_key_tests() -> None:
    """frame_contracts declares unique + not_null on contract_id."""
    frame = _all_models()["frame_contracts"]
    contract_id = next(col for col in frame["columns"] if col["name"] == "contract_id")
    test_names = {
        t if isinstance(t, str) else next(iter(t)) for t in contract_id["tests"]
    }

    assert {"unique", "not_null"} <= test_names


def test_e4_detail_models_exist_for_all_domains() -> None:
    """Every domain has its own Detail directory, model, and schema."""
    models = _all_models()
    for domain in _DOMAINS:
        domain_dir = _MODELS / "detail" / domain
        assert domain_dir.is_dir(), f"missing detail directory for {domain}"
        assert (domain_dir / f"detail_{domain}_contracts.sql").is_file()
        assert (domain_dir / "schema.yml").is_file()

        model = models[f"detail_{domain}_contracts"]
        # Each Detail table is one row per contract — the grain the mesh depends on.
        contract_id = next(
            col for col in model["columns"] if col["name"] == "contract_id"
        )
        test_names = {
            t if isinstance(t, str) else next(iter(t)) for t in contract_id["tests"]
        }
        assert {"unique", "not_null"} <= test_names


def test_e4_core_model_references_all_detail_models() -> None:
    """core_contracts joins the Frame and every Detail model by contract_id."""
    sql = (_MODELS / "core" / "core_contracts.sql").read_text(encoding="utf-8")

    assert "ref('frame_contracts')" in sql
    for domain in _DOMAINS:
        assert f"ref('detail_{domain}_contracts')" in sql
    # All joins share the Frame key — that is what keeps them fan-out free.
    assert sql.count("using (contract_id)") == len(_DOMAINS)


def test_e4_best_practices_grade_a() -> None:
    """The blueprint scores Grade A against QM-10's seven best practices."""
    result = check_blueprint_best_practices(
        "data-mesh-contracts", str(_BLUEPRINTS), ":memory:"
    )

    assert result.grade == "A", f"violations: {[v.code for v in result.violations]}"
    assert result.score == 100.0
    assert result.violations == []


def test_e4_utility_readme_exists() -> None:
    """The utility directory documents how teams add downstream tables."""
    readme = _MODELS / "utility" / "README.md"
    assert readme.is_file()

    text = readme.read_text(encoding="utf-8")
    assert "core_contracts" in text
    assert "utility" in text.lower()


def test_e4_data_mesh_pattern_doc_exists() -> None:
    """DATA-MESH-PATTERN.md explains the pattern and per-domain ownership."""
    doc = _MESH / "docs" / "DATA-MESH-PATTERN.md"
    assert doc.is_file()

    text = doc.read_text(encoding="utf-8")
    assert "Frame" in text and "Detail" in text and "Core" in text
    for domain in ("Engineering", "Finance", "Sales", "Product"):
        assert domain in text
    assert "owner column" in text  # tells the reader how to declare ownership


def test_e4_all_models_have_descriptions() -> None:
    """Every model is documented and every declared column is tested."""
    models = _all_models()
    assert set(models) == set(_MODEL_NAMES)

    for name, model in models.items():
        assert model.get("description", "").strip(), f"{name} has no description"
        for col in model.get("columns") or []:
            assert col.get(
                "description", ""
            ).strip(), f"{name}.{col.get('name')} has no description"
            assert col.get("tests"), f"{name}.{col.get('name')} has no tests"


def test_e4_contracts_cover_every_model() -> None:
    """Each model has a contract, in the columns: list-of-mappings shape."""
    contracts_dir = _MESH / "contracts"
    contracts = {
        path.stem: yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted(contracts_dir.glob("*.yaml"))
    }

    assert set(contracts) == {
        "frame_contracts",
        "finance_contracts",
        "sales_contracts",
        "product_contracts",
        "core_contracts",
    }
    for name, contract in contracts.items():
        columns = contract["columns"]
        assert isinstance(columns, list) and columns, f"{name} declares no columns"
        for col in columns:
            assert isinstance(col, dict), f"{name} must use list-of-mappings columns"
            assert col.get("name")
            # Every column names the domain accountable for it (GM-4 intent).
            assert col.get("owner_domain"), f"{name}.{col['name']} has no owner_domain"
