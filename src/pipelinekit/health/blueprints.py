"""Blueprint integrity check — reuses Phase 3 validation (SPEC-012).

Validates every installed blueprint with the existing ``BlueprintValidator``.
The ``blueprints/`` directory is scanned directly (the same way
``BlueprintRegistry`` scans it) so that a schema-invalid blueprint surfaces as
an ``error`` rather than being silently skipped — health must reveal failures,
not hide them (Smell 12). No blueprints installed is ``ok``, not an error.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.blueprints.validator import BlueprintValidator
from pipelinekit.core.errors import BlueprintError
from pipelinekit.health import ERROR, OK, HealthCheckResult

BLUEPRINTS_DIR = "blueprints"


class BlueprintHealthChecker:
    """Validate all installed blueprints against their schema."""

    name = "blueprints"

    def check(self, cwd: Path | None = None) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing blueprint integrity.

        Never raises — invalid blueprints resolve to an ``error`` result.
        """
        base = (cwd if cwd is not None else Path.cwd()) / BLUEPRINTS_DIR
        if not base.is_dir():
            return HealthCheckResult(self.name, OK, "No blueprints installed.")

        entries = [
            entry
            for entry in sorted(base.iterdir())
            if (entry / "blueprint.json").is_file()
        ]
        if not entries:
            return HealthCheckResult(self.name, OK, "No blueprints installed.")

        validator = BlueprintValidator()
        details: list[str] = []
        failed = 0
        for entry in entries:
            try:
                validator.validate(entry)
                details.append(f"{entry.name}: valid")
            except BlueprintError as exc:
                failed += 1
                details.append(f"{entry.name}: {exc.code} {exc.message}")

        if failed:
            return HealthCheckResult(
                self.name,
                ERROR,
                f"{failed} of {len(entries)} blueprint(s) failed validation.",
                details=details,
                fix_hint="Run 'pipelinekit blueprint validate <name>' for detail.",
            )

        return HealthCheckResult(
            self.name,
            OK,
            f"{len(entries)} blueprint(s) installed, all valid.",
            details=details,
        )
