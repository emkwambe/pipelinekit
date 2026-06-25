"""Dependency currency check — ``poetry show --outdated`` (SPEC-012).

Reports only; never updates anything. Outdated packages are categorized by
semver distance: patch (safe), minor (test first), major (ADR required). If
Poetry is unavailable the check resolves to ``info`` — a missing tool is never
treated as a project failure.
"""

from __future__ import annotations

import subprocess

from pipelinekit.health import ERROR, INFO, OK, WARNING, HealthCheckResult

_TIMEOUT_S = 120


class DepsChecker:
    """Check for outdated dependencies using ``poetry show --outdated``."""

    name = "deps"

    def check(self) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing dependency currency.

        Never raises — Poetry failures resolve to an ``info`` result.
        """
        try:
            proc = subprocess.run(
                ["poetry", "show", "--outdated", "--no-ansi"],
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_S,
            )
        except (FileNotFoundError, OSError, subprocess.SubprocessError):
            return HealthCheckResult(
                self.name,
                INFO,
                "Poetry is not available — dependency check skipped.",
                fix_hint="Install Poetry to enable dependency currency checks.",
            )

        if proc.returncode != 0:
            detail = (proc.stderr or "").strip()
            return HealthCheckResult(
                self.name,
                INFO,
                "Could not read dependency status from Poetry.",
                details=[detail] if detail else None,
                fix_hint="Run 'poetry show --outdated' to inspect the failure.",
            )

        return self._categorize(proc.stdout)

    def _categorize(self, stdout: str) -> HealthCheckResult:
        """Parse ``poetry show --outdated`` output into a verdict."""
        patch: list[str] = []
        minor: list[str] = []
        major: list[str] = []

        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            package, current, latest = parts[0], parts[1], parts[2]
            bucket = self._bump(current, latest)
            entry = f"{package} {current} -> {latest} ({bucket})"
            if bucket == "major":
                major.append(entry)
            elif bucket == "minor":
                minor.append(entry)
            elif bucket == "patch":
                patch.append(entry)

        outdated = major + minor + patch
        if not outdated:
            return HealthCheckResult(self.name, OK, "All dependencies current.")

        if major:
            return HealthCheckResult(
                self.name,
                ERROR,
                f"{len(major)} major update(s) available — review before upgrading.",
                details=outdated,
                fix_hint="Major upgrades require an ADR (Sustainability Policy).",
            )

        return HealthCheckResult(
            self.name,
            WARNING,
            f"{len(outdated)} update(s) available "
            f"({len(patch)} patch, {len(minor)} minor).",
            details=outdated,
            fix_hint="Patch updates are safe; test minor updates before applying.",
        )

    @staticmethod
    def _bump(current: str, latest: str) -> str:
        """Classify the semver distance from ``current`` to ``latest``."""
        cur = DepsChecker._version(current)
        lat = DepsChecker._version(latest)
        if lat[0] > cur[0]:
            return "major"
        if lat[0] == cur[0] and lat[1] > cur[1]:
            return "minor"
        if lat[0] == cur[0] and lat[1] == cur[1] and lat[2] > cur[2]:
            return "patch"
        return "current"

    @staticmethod
    def _version(value: str) -> tuple[int, int, int]:
        """Parse a version string into a (major, minor, patch) tuple."""
        parts: list[int] = []
        for segment in value.split("."):
            digits = ""
            for char in segment:
                if char.isdigit():
                    digits += char
                else:
                    break
            parts.append(int(digits) if digits else 0)
        while len(parts) < 3:
            parts.append(0)
        return parts[0], parts[1], parts[2]
