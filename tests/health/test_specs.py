"""Tests for SpecDriftChecker (SPEC-012). Operates on tmp_path SPEC files."""

from __future__ import annotations

from pathlib import Path

from pipelinekit.health import OK, WARNING
from pipelinekit.health.specs import SpecDriftChecker


def _write_spec(base: Path, filename: str, status: str) -> Path:
    path = base / filename
    path.write_text(
        f"# {filename[:-3]}\n\n**Status:** {status}\n\n## Purpose\n\nx\n",
        encoding="utf-8",
    )
    return path


def test_detects_drift_when_implemented_spec_is_approved(tmp_path):
    """An implemented SPEC still marked Approved is reported as drift."""
    _write_spec(tmp_path, "SPEC-001-CLI-Framework.md", "Approved")
    result = SpecDriftChecker().check(specs_dir=tmp_path)
    assert result.status == WARNING
    assert any("SPEC-001" in d for d in result.details or [])


def test_ok_when_all_specs_correct(tmp_path):
    """Implemented SPECs marked Implemented show no drift."""
    _write_spec(tmp_path, "SPEC-001-CLI-Framework.md", "Implemented")
    _write_spec(tmp_path, "SPEC-002-Configuration.md", "Implemented")
    result = SpecDriftChecker().check(specs_dir=tmp_path)
    assert result.status == OK


def test_fix_updates_status_headers(tmp_path):
    """fix() rewrites a drifted Approved header to Implemented."""
    path = _write_spec(tmp_path, "SPEC-001-CLI-Framework.md", "Approved")
    fixed = SpecDriftChecker().fix(specs_dir=tmp_path)
    assert fixed == 1
    assert "**Status:** Implemented" in path.read_text(encoding="utf-8")
    # Drift is resolved after the fix.
    assert SpecDriftChecker().check(specs_dir=tmp_path).status == OK


def test_fix_leaves_non_implemented_specs_untouched(tmp_path):
    """A SPEC not in the implemented set is left as-is (e.g. the active sprint)."""
    path = _write_spec(tmp_path, "SPEC-012-Health-Command-System.md", "Approved")
    fixed = SpecDriftChecker().fix(specs_dir=tmp_path)
    assert fixed == 0
    assert "**Status:** Approved" in path.read_text(encoding="utf-8")
