"""Security advisory check — ``pip-audit`` (SPEC-012).

If ``pip-audit`` is not installed the check resolves to ``info`` with install
instructions — a missing tool never fails the check. When present, known
vulnerabilities resolve to ``warning`` (advisory; the user decides how to act).
"""

from __future__ import annotations

import json
import subprocess

from pipelinekit.health import INFO, OK, WARNING, HealthCheckResult

_TIMEOUT_S = 300
_INSTALL_HINT = "poetry add --group dev pip-audit"


class SecurityChecker:
    """Check for known vulnerabilities using ``pip-audit``."""

    name = "security"

    def check(self) -> HealthCheckResult:
        """Return a ``HealthCheckResult`` describing vulnerability status.

        Never raises — a missing or failing ``pip-audit`` resolves to ``info``.
        """
        try:
            proc = subprocess.run(
                ["pip-audit", "--format=json"],
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_S,
            )
        except (FileNotFoundError, OSError):
            return HealthCheckResult(
                self.name,
                INFO,
                "pip-audit is not installed — security check skipped.",
                fix_hint=_INSTALL_HINT,
            )
        except subprocess.SubprocessError:
            return HealthCheckResult(
                self.name,
                INFO,
                "pip-audit could not run — security check skipped.",
                fix_hint=_INSTALL_HINT,
            )

        try:
            data = json.loads(proc.stdout or "{}")
        except ValueError:
            return HealthCheckResult(
                self.name,
                INFO,
                "pip-audit output could not be parsed — security check skipped.",
                fix_hint=_INSTALL_HINT,
            )

        vulnerable = self._vulnerable_packages(data)
        if not vulnerable:
            return HealthCheckResult(self.name, OK, "No known vulnerabilities found.")

        return HealthCheckResult(
            self.name,
            WARNING,
            f"{len(vulnerable)} package(s) with known vulnerabilities.",
            details=vulnerable,
            fix_hint="Review pip-audit output and upgrade affected packages.",
        )

    @staticmethod
    def _vulnerable_packages(data: object) -> list[str]:
        """Extract a summary line per vulnerable package from pip-audit JSON."""
        if isinstance(data, dict):
            dependencies = data.get("dependencies", [])
        elif isinstance(data, list):
            dependencies = data
        else:
            dependencies = []

        summaries: list[str] = []
        for dep in dependencies:
            if not isinstance(dep, dict):
                continue
            vulns = dep.get("vulns") or []
            if vulns:
                name = dep.get("name", "unknown")
                version = dep.get("version", "?")
                ids = ", ".join(
                    str(v.get("id", "?")) for v in vulns if isinstance(v, dict)
                )
                summaries.append(f"{name} {version}: {ids}")
        return summaries
