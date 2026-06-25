"""Validate ``blueprint.json`` against ``schemas/blueprint.schema.json``.

Uses the ``jsonschema`` library, imported only in this file. The schema is
located relative to the repository root (derived from this module's path) so
validation is independent of the current working directory.

See: SPEC-006.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from pipelinekit.core.errors import BlueprintError

# repo_root/src/pipelinekit/blueprints/validator.py -> parents[3] == repo root
_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "blueprint.schema.json"


class BlueprintValidator:
    """Validates a blueprint's ``blueprint.json`` against the JSON schema."""

    def __init__(self, schema_path: Path | None = None) -> None:
        self.schema_path = schema_path if schema_path is not None else _SCHEMA_PATH

    def validate(self, blueprint_path: Path) -> None:
        """Validate the ``blueprint.json`` at ``blueprint_path``.

        Args:
            blueprint_path: Path to a ``blueprint.json`` file (or its directory).

        Raises:
            BlueprintError: ``PK-BLUEPRINT-002`` if the file is not found,
                ``PK-BLUEPRINT-001`` if it fails schema validation or is not
                valid JSON.
        """
        path = blueprint_path
        if path.is_dir():
            path = path / "blueprint.json"
        if not path.is_file():
            raise BlueprintError(
                "PK-BLUEPRINT-002",
                f"blueprint.json not found at {path}",
                {"path": str(path)},
            )

        try:
            instance = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise BlueprintError(
                "PK-BLUEPRINT-001",
                f"blueprint.json is not valid JSON: {path.name}",
                {"path": str(path), "detail": str(exc)},
            ) from exc

        schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(instance=instance, schema=schema)
        except jsonschema.ValidationError as exc:
            raise BlueprintError(
                "PK-BLUEPRINT-001",
                f"blueprint.json failed schema validation: {exc.message}",
                {"path": str(path), "detail": exc.message},
            ) from exc
