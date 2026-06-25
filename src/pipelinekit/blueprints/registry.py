"""Local blueprint registry — scans the ``blueprints/`` directory.

Phase 3 is local only; a remote, versioned catalog arrives in Phase 4. The
registry never raises on a missing directory or an unparseable blueprint — it
returns what it can and skips the rest (SPEC-006).
"""

from __future__ import annotations

import json
from pathlib import Path

from pipelinekit.blueprints.models import BlueprintMetadata

BLUEPRINTS_DIR = Path("blueprints")


class BlueprintRegistry:
    """Scans a local directory of installed blueprints."""

    def __init__(self, blueprints_dir: Path = BLUEPRINTS_DIR) -> None:
        self.blueprints_dir = blueprints_dir

    def list(self) -> list[BlueprintMetadata]:
        """Return metadata for every valid blueprint, sorted by name.

        Returns an empty list when ``blueprints/`` is absent or empty. A single
        malformed blueprint is skipped, never fatal.
        """
        if not self.blueprints_dir.is_dir():
            return []
        blueprints: list[BlueprintMetadata] = []
        for entry in sorted(self.blueprints_dir.iterdir()):
            metadata = self._load(entry / "blueprint.json")
            if metadata is not None:
                blueprints.append(metadata)
        return blueprints

    def get(self, name: str) -> BlueprintMetadata | None:
        """Return metadata for a named blueprint, or None if not installed."""
        metadata = self._load(self.blueprints_dir / name / "blueprint.json")
        if metadata is not None and metadata.name == name:
            return metadata
        # Fall back to a directory whose blueprint.json declares this name.
        for candidate in self.list():
            if candidate.name == name:
                return candidate
        return None

    def exists(self, name: str) -> bool:
        """Return True if a blueprint with this name is installed."""
        return self.get(name) is not None

    def _load(self, path: Path) -> BlueprintMetadata | None:
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return BlueprintMetadata(**data)
        except Exception:
            return None
