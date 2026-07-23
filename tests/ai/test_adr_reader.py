"""Tests for ADRReader (SPEC-011).

Reads a committed fixture directory (``tests/fixtures/decisions/``) rather than
the real ``docs/decisions/``, which is gitignored and absent from CI checkouts.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.ai.adr_reader import ADRReader

_FIXTURE_DECISIONS = Path(__file__).resolve().parents[1] / "fixtures" / "decisions"


def test_read_all_returns_summaries():
    """read_all() returns structured ADR summaries from the fixture directory."""
    reader = ADRReader(_FIXTURE_DECISIONS)
    adrs = reader.read_all()
    assert len(adrs) > 0
    assert all(a["adr_id"].startswith("ADR-") for a in adrs)
    summaries = reader.get_adr_summaries()
    assert all({"adr_id", "title", "status", "summary"} <= set(s) for s in summaries)


def test_malformed_adr_is_skipped(tmp_path):
    """A malformed ADR file is skipped — read_all does not raise."""
    (tmp_path / "ADR-001-Valid.md").write_text(
        "# ADR-001: Valid\n\nStatus: Accepted\n\n## Decision\n\nAdopt the thing.\n",
        encoding="utf-8",
    )
    (tmp_path / "not-an-adr.md").write_text(
        "just some random notes with no adr heading at all\n", encoding="utf-8"
    )
    reader = ADRReader(tmp_path)
    adrs = reader.read_all()
    assert len(adrs) == 1
    assert adrs[0]["adr_id"] == "ADR-001"
    assert reader.warnings  # the malformed file was recorded, not raised


def test_missing_decisions_dir_returns_empty(tmp_path):
    """A missing decisions directory returns [] — does not raise."""
    reader = ADRReader(tmp_path / "does-not-exist")
    assert reader.read_all() == []
