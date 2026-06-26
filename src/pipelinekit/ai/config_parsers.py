"""Deterministic parsers for existing pipeline configs (SPEC-017, ADR-020).

Parsing is deterministic; the AI only interprets the parsed dict afterwards
(ADR-008, deterministic before AI). The Python parser uses ``ast.parse()`` only
— it never ``exec()``s, ``eval()``s, or shells out — so reading an untrusted
pipeline file can never run it.

Routing (``MigrationConfigParser``):
    .json  → Airbyte, then Fivetran
    .py    → Python (AST inspection)
    .yaml  → existing pipelinekit.yaml upgrade path
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from pipelinekit.core.errors import MigrationError

# Connection-string schemes we recognise → PipelineKit source/destination type.
_SCHEME_TO_TYPE: dict[str, str] = {
    "postgresql": "postgres",
    "postgres": "postgres",
    "mysql": "mysql",
    "snowflake": "snowflake",
    "bigquery": "bigquery",
    "duckdb": "duckdb",
}


def _first_word_lower(value: str) -> str:
    """Normalise a tool's display name to a type token (``Postgres`` → postgres)."""
    return value.strip().lower().split()[0] if value.strip() else ""


class AirbyteParser:
    """Parse an Airbyte ``connection.json`` export."""

    @staticmethod
    def can_parse(data: dict) -> bool:
        """Return True if ``data`` looks like an Airbyte connection export."""
        if not isinstance(data, dict):
            return False
        return "syncCatalog" in data or ("source" in data and "destination" in data)

    def parse(self, path: Path) -> dict:
        """Extract source_type, destination_type, streams, sync_mode, namespace."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return self.parse_data(data)

    def parse_data(self, data: dict) -> dict:
        """Parse an already-loaded Airbyte export dict."""
        source = data.get("source") or {}
        destination = data.get("destination") or {}
        catalog = data.get("syncCatalog") or {}

        streams: list[dict] = []
        for entry in catalog.get("streams", []) or []:
            stream = entry.get("stream", {}) if isinstance(entry, dict) else {}
            config = entry.get("config", {}) if isinstance(entry, dict) else {}
            streams.append(
                {
                    "name": stream.get("name", ""),
                    "namespace": stream.get("namespace", ""),
                    "sync_mode": config.get("syncMode", ""),
                }
            )

        sync_mode = streams[0]["sync_mode"] if streams else ""
        namespace = streams[0]["namespace"] if streams else ""
        return {
            "source_type": self._type_of(source, "sourceType", "sourceName"),
            "destination_type": self._type_of(
                destination, "destinationType", "destinationName"
            ),
            "streams": streams,
            "sync_mode": sync_mode,
            "namespace": namespace,
            "source_config": source.get("connectionConfiguration", {}),
            "destination_config": destination.get("connectionConfiguration", {}),
            "schedule": data.get("scheduleData") or data.get("scheduleType"),
        }

    @staticmethod
    def _type_of(node: dict, type_key: str, name_key: str) -> str:
        """Resolve a connector type from an explicit type or its display name."""
        explicit = node.get(type_key)
        if explicit:
            return _first_word_lower(str(explicit))
        return _first_word_lower(str(node.get(name_key, "")))


class FivetranParser:
    """Parse a Fivetran ``connector.json`` export."""

    @staticmethod
    def can_parse(data: dict) -> bool:
        """Return True if ``data`` looks like a Fivetran connector export."""
        if not isinstance(data, dict):
            return False
        return "service" in data and ("sync_frequency" in data or "schema" in data)

    def parse(self, path: Path) -> dict:
        """Extract connector_type, schema, tables, sync_frequency."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return self.parse_data(data)

    def parse_data(self, data: dict) -> dict:
        """Parse an already-loaded Fivetran connector dict."""
        destination = data.get("destination") or {}
        return {
            "connector_type": _first_word_lower(str(data.get("service", ""))),
            "destination_type": _first_word_lower(str(destination.get("service", ""))),
            "schema": data.get("schema", ""),
            "tables": self._tables(data),
            "sync_frequency": data.get("sync_frequency"),
            "source_config": data.get("config", {}),
        }

    @staticmethod
    def _tables(data: dict) -> list[str]:
        """Collect enabled table names from the connector's schema map."""
        tables: list[str] = []
        schemas = data.get("schemas") or {}
        for schema in schemas.values():
            if not isinstance(schema, dict):
                continue
            for name, table in (schema.get("tables") or {}).items():
                enabled = (
                    table.get("enabled", True) if isinstance(table, dict) else True
                )
                if enabled:
                    tables.append(name)
        return tables


class PythonParser:
    """Best-effort, execution-free parse of a custom Python pipeline file.

    Uses ``ast.parse()`` only — never ``exec()``, ``eval()``, or ``subprocess``.
    Looks for dlt / SQLAlchemy / psycopg2 patterns: connection strings (and the
    source type implied by their scheme), a dlt ``destination=`` hint, and
    list-of-string table declarations. Results carry ``confidence: "low"`` because
    static inspection of arbitrary Python is inherently ambiguous.
    """

    def parse(self, path: Path) -> dict:
        """Extract connection hints from a Python file without executing it.

        Raises:
            MigrationError: ``PK-MIGRATE-005`` if the file is not valid Python.
        """
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            raise MigrationError(
                "PK-MIGRATE-005",
                f"Could not parse Python file (syntax error): {exc}",
                {"path": str(path), "detail": str(exc)},
            ) from exc

        conn_strings = self._connection_strings(tree)
        return {
            "connection_strings": conn_strings,
            "source_type": self._source_type(conn_strings),
            "destination_type": self._destination_hint(tree),
            "tables": self._tables(tree),
            "confidence": "low",
        }

    @staticmethod
    def _connection_strings(tree: ast.AST) -> list[str]:
        """Return every string literal that looks like a connection URL."""
        found: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "://" in node.value:
                    found.append(node.value)
        return found

    @staticmethod
    def _source_type(conn_strings: list[str]) -> str:
        """Infer a source type from the scheme of the first connection string."""
        for conn in conn_strings:
            scheme = conn.split("://", 1)[0].split("+", 1)[0].lower()
            if scheme in _SCHEME_TO_TYPE:
                return _SCHEME_TO_TYPE[scheme]
        return ""

    @staticmethod
    def _destination_hint(tree: ast.AST) -> str:
        """Find a dlt ``destination="..."`` keyword argument, if present."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "destination" and isinstance(kw.value, ast.Constant):
                        if isinstance(kw.value.value, str):
                            return _first_word_lower(kw.value.value)
        return ""

    @staticmethod
    def _tables(tree: ast.AST) -> list[str]:
        """Collect a list-of-strings assigned to a name containing 'table'.

        Falls back to the first list-of-strings literal found, since custom
        pipelines often name it ``TABLES``/``tables`` but not always.
        """
        fallback: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if not isinstance(node.value, ast.List):
                continue
            items = [
                el.value
                for el in node.value.elts
                if isinstance(el, ast.Constant) and isinstance(el.value, str)
            ]
            if not items:
                continue
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any("table" in n.lower() for n in names):
                return items
            if not fallback:
                fallback = items
        return fallback


class MigrationConfigParser:
    """Router — detect the source format and delegate to the right parser."""

    def __init__(self) -> None:
        self.airbyte = AirbyteParser()
        self.fivetran = FivetranParser()
        self.python = PythonParser()

    def parse(self, path: Path) -> tuple[str, dict]:
        """Return ``(tool_name, parsed_config)`` for an existing config file.

        Raises:
            MigrationError: ``PK-MIGRATE-001`` if the file is missing,
                ``PK-MIGRATE-002`` if the format is not recognised,
                ``PK-MIGRATE-005`` if a ``.py`` file has a syntax error.
        """
        if not path.is_file():
            raise MigrationError(
                "PK-MIGRATE-001",
                f"Config file not found: {path}",
                {"path": str(path)},
            )

        suffix = path.suffix.lower()
        if suffix == ".py":
            return ("python", self.python.parse(path))
        if suffix in (".yaml", ".yml"):
            return ("pipelinekit", self._parse_pipelinekit(path))
        if suffix == ".json":
            return self._parse_json(path)

        raise MigrationError(
            "PK-MIGRATE-002",
            f"Unrecognised config format: {path.suffix or '(no extension)'}",
            {"path": str(path)},
        )

    def _parse_json(self, path: Path) -> tuple[str, dict]:
        """Route a JSON file to Airbyte, then Fivetran."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise MigrationError(
                "PK-MIGRATE-002",
                f"Config file is not valid JSON: {path}",
                {"path": str(path), "detail": str(exc)},
            ) from exc

        if self.airbyte.can_parse(data):
            return ("airbyte", self.airbyte.parse_data(data))
        if self.fivetran.can_parse(data):
            return ("fivetran", self.fivetran.parse_data(data))
        raise MigrationError(
            "PK-MIGRATE-002",
            f"JSON config matched neither Airbyte nor Fivetran: {path}",
            {"path": str(path)},
        )

    def _parse_pipelinekit(self, path: Path) -> dict:
        """Read an existing pipelinekit.yaml for an upgrade-path analysis."""
        text = path.read_text(encoding="utf-8")
        if "pipeline:" not in text or "ingestion:" not in text:
            raise MigrationError(
                "PK-MIGRATE-002",
                f"YAML file is not a pipelinekit.yaml: {path}",
                {"path": str(path)},
            )
        return {"raw_yaml": text}
