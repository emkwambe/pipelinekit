"""Tests for TestsChecker (SPEC-012). Coverage data is read, never generated."""

from __future__ import annotations

from pipelinekit.health import INFO, OK
from pipelinekit.health.tests import TestsChecker


def test_info_when_no_coverage_file(tmp_path):
    """No .coverage file → status info (tests not yet run)."""
    result = TestsChecker().check(cwd=tmp_path)
    assert result.status == INFO


def test_info_when_coverage_unreadable(tmp_path):
    """A corrupt .coverage file → status info, never a crash."""
    (tmp_path / ".coverage").write_text("not a coverage database", encoding="utf-8")
    result = TestsChecker().check(cwd=tmp_path)
    assert result.status == INFO


def test_ok_reports_percentage_from_coverage(tmp_path, monkeypatch):
    """A readable coverage file reports a percentage as status ok."""
    (tmp_path / ".coverage").write_text("placeholder", encoding="utf-8")

    class _FakeCov:
        def __init__(self, data_file=None):
            self._data_file = data_file

        def load(self):
            return None

        def report(self, file=None):
            return 81.27

    monkeypatch.setattr("coverage.Coverage", lambda data_file=None: _FakeCov(data_file))
    result = TestsChecker().check(cwd=tmp_path)
    assert result.status == OK
    assert "81.27" in result.message
