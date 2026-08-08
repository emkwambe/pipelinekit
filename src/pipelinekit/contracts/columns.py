"""Canonical column extraction for data contracts — both contract shapes.

This repo carries two contract shapes, and every module that reads contract
columns must understand both:

* **shape A** — constraint blocks at the top level::

      required_columns: [order_id, amount]
      not_null: [order_id]
      uniqueness: [order_id]
      accepted_values: {status: [active, closed]}

* **shape B** — a ``columns:`` list of mappings, with constraints per column::

      columns:
        - name: order_id
          nullable: false
          unique: true
        - name: status
          accepted_values: [active, closed]

Reading only shape A silently yields *zero* columns for a shape-B contract.
That failure is quiet and severe: an empty column set makes a drift check report
a clean blueprint as fully drifted, and makes a removed column look like no
change at all — versioning a breaking change as a patch.

Every contract-column reader delegates here rather than re-deriving the rules,
so a third shape (or a fix) lands in one place. Shape A behavior is preserved
exactly: a shape-A contract produces the same sets it always did.
"""

from __future__ import annotations

# Top-level keys that hold a list of column names (shape A) or column mappings
# (shape B). Both are read and unioned, so a hybrid contract is understood.
_NAME_LIST_KEYS = ("columns", "required_columns")


def _entry_name(entry: object) -> str | None:
    """Return the column name from a list entry, whichever shape it is."""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        name = entry.get("name")
        if isinstance(name, str):
            return name
    return None


def _column_mappings(content: dict) -> list[dict]:
    """Return shape-B column mappings, or an empty list for shape A."""
    raw = content.get("columns")
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def column_names(content: dict) -> set[str]:
    """Return every column name a contract declares, in either shape."""
    if not isinstance(content, dict):
        return set()

    names: set[str] = set()
    for key in _NAME_LIST_KEYS:
        value = content.get(key)
        if not isinstance(value, list):
            continue
        for entry in value:
            name = _entry_name(entry)
            if name is not None:
                names.add(name)
    return names


def required_column_names(content: dict) -> set[str]:
    """Return the columns a contract requires to be present.

    Shape A states this explicitly via ``required_columns``. Shape B has no
    separate notion of "required" — declaring a column *is* requiring it — so
    every declared column counts.
    """
    if not isinstance(content, dict):
        return set()

    required = content.get("required_columns")
    if isinstance(required, list):
        names = {name for name in (_entry_name(e) for e in required) if name}
        if names:
            return names
    return {
        name
        for name in (col.get("name") for col in _column_mappings(content))
        if isinstance(name, str)
    }


def not_null_columns(content: dict) -> set[str]:
    """Return columns constrained to be non-null, in either shape."""
    if not isinstance(content, dict):
        return set()

    names = {
        name for name in (_entry_name(e) for e in content.get("not_null") or []) if name
    }
    for col in _column_mappings(content):
        if col.get("nullable") is False and isinstance(col.get("name"), str):
            names.add(col["name"])
    return names


def unique_columns(content: dict) -> set[str]:
    """Return columns constrained to be unique, in either shape."""
    if not isinstance(content, dict):
        return set()

    names = {
        name
        for name in (_entry_name(e) for e in content.get("uniqueness") or [])
        if name
    }
    for col in _column_mappings(content):
        if col.get("unique") is True and isinstance(col.get("name"), str):
            names.add(col["name"])
    return names


def accepted_values(content: dict) -> dict[str, list[str]]:
    """Return the column -> allowed-values map, in either shape."""
    if not isinstance(content, dict):
        return {}

    values: dict[str, list[str]] = {}
    top_level = content.get("accepted_values")
    if isinstance(top_level, dict):
        for column, allowed in top_level.items():
            if isinstance(allowed, list):
                values[str(column)] = [str(v) for v in allowed]

    for col in _column_mappings(content):
        name = col.get("name")
        allowed = col.get("accepted_values")
        if isinstance(name, str) and isinstance(allowed, list):
            values[name] = [str(v) for v in allowed]
    return values


def freshness_column(content: dict) -> str | None:
    """Return the column a contract measures freshness on, if any."""
    if not isinstance(content, dict):
        return None
    freshness = content.get("freshness")
    if isinstance(freshness, dict):
        column = freshness.get("column")
        if isinstance(column, str):
            return column
    return None


def all_referenced_columns(content: dict) -> set[str]:
    """Return every column a contract references — declared or constrained."""
    referenced = (
        column_names(content)
        | not_null_columns(content)
        | unique_columns(content)
        | set(accepted_values(content))
    )
    freshness = freshness_column(content)
    if freshness is not None:
        referenced.add(freshness)
    return referenced
