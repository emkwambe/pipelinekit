"""Tests for canonical contract-column extraction across both contract shapes.

This repo carries two contract shapes. A reader that understands only shape A
returns an empty column set for a shape-B contract — silently, which is how the
same defect reached three separate modules. These tests pin both shapes at the
one place every reader now delegates to.

  shape A  required_columns + top-level constraint blocks (stripe-to-snowflake)
  shape B  columns: list-of-mappings with per-column constraints
           (postgres-to-duckdb, data-mesh-contracts)
"""

from __future__ import annotations

from pipelinekit.contracts import columns as contract_columns

_SHAPE_A = {
    "table": "charges",
    "version": 1,
    "required_columns": ["charge_id", "amount", "status"],
    "not_null": ["charge_id", "amount"],
    "uniqueness": ["charge_id"],
    "accepted_values": {"status": ["succeeded", "failed"]},
    "freshness": {"max_age_hours": 6, "column": "created_at"},
}

_SHAPE_B = {
    "table": "frame_contracts",
    "version": "1.0.0",
    "columns": [
        {"name": "contract_id", "type": "varchar", "nullable": False, "unique": True},
        {
            "name": "status",
            "type": "varchar",
            "nullable": False,
            "accepted_values": ["active", "expired"],
        },
        {"name": "note", "type": "varchar"},
    ],
}


def test_column_names_reads_both_shapes() -> None:
    """Column names are found whether they are strings or {name: ...} mappings."""
    assert contract_columns.column_names(_SHAPE_A) == {
        "charge_id",
        "amount",
        "status",
    }
    assert contract_columns.column_names(_SHAPE_B) == {
        "contract_id",
        "status",
        "note",
    }


def test_shape_b_never_yields_an_empty_column_set() -> None:
    """The core regression: a populated shape-B contract must not read as empty.

    An empty set is what made drift report a clean blueprint as fully drifted
    and made a removed column look like no change at all.
    """
    assert contract_columns.column_names(_SHAPE_B) != set()
    assert contract_columns.all_referenced_columns(_SHAPE_B) != set()
    assert contract_columns.required_column_names(_SHAPE_B) != set()


def test_not_null_and_unique_read_per_column_constraints() -> None:
    """Shape B expresses constraints per column; shape A in top-level blocks."""
    assert contract_columns.not_null_columns(_SHAPE_A) == {"charge_id", "amount"}
    assert contract_columns.unique_columns(_SHAPE_A) == {"charge_id"}

    assert contract_columns.not_null_columns(_SHAPE_B) == {"contract_id", "status"}
    assert contract_columns.unique_columns(_SHAPE_B) == {"contract_id"}


def test_accepted_values_read_from_both_shapes() -> None:
    """accepted_values is a top-level map in shape A, per-column in shape B."""
    assert contract_columns.accepted_values(_SHAPE_A) == {
        "status": ["succeeded", "failed"]
    }
    assert contract_columns.accepted_values(_SHAPE_B) == {
        "status": ["active", "expired"]
    }


def test_all_referenced_columns_includes_freshness_column() -> None:
    """Shape A's freshness column counts toward the column universe."""
    assert "created_at" in contract_columns.all_referenced_columns(_SHAPE_A)


def test_required_columns_falls_back_to_declared_columns() -> None:
    """Shape B has no separate 'required' notion — declaring a column requires it."""
    assert contract_columns.required_column_names(_SHAPE_A) == {
        "charge_id",
        "amount",
        "status",
    }
    assert contract_columns.required_column_names(_SHAPE_B) == {
        "contract_id",
        "status",
        "note",
    }


def test_malformed_content_returns_empty_never_raises() -> None:
    """Unexpected structures degrade to empty results rather than raising."""
    for bad in ({}, {"columns": "not-a-list"}, {"columns": [1, None]}, "not-a-dict"):
        assert contract_columns.column_names(bad) == set()  # type: ignore[arg-type]
        assert contract_columns.not_null_columns(bad) == set()  # type: ignore[arg-type]
        assert contract_columns.accepted_values(bad) == {}  # type: ignore[arg-type]
