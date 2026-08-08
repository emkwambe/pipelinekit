"""Tests for RM-5 pipeline scheduling.

Deterministic, no AI. Every test uses a ``tmp_path`` database — the real
``.pipelinekit/state.db`` is never touched. Follows the GM-1 test pattern.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pipelinekit.core.errors import ReleaseError
from pipelinekit.scheduling.scheduler import (
    ACTIVE,
    INACTIVE,
    compute_next_run,
    disable_schedule,
    enable_schedule,
    generate_platform_scheduler_entry,
    get_all_schedules,
    get_schedule,
    get_schedule_history,
    record_schedule_run,
    remove_schedule,
    set_schedule,
)

_PIPELINE = "pipelinekit-demo"


def _db(tmp_path: Path) -> str:
    """Return a throwaway state.db path inside the test's tmp dir."""
    return str(tmp_path / "state.db")


def test_rm5_set_schedule_creates_record(tmp_path: Path) -> None:
    """set_schedule creates a PipelineSchedule with the correct fields."""
    schedule = set_schedule(_PIPELINE, 8, "America/New_York", _db(tmp_path))

    assert schedule.pipeline_name == _PIPELINE
    assert schedule.interval_hours == 8
    assert schedule.timezone == "America/New_York"
    assert schedule.status == ACTIVE
    assert schedule.last_run_at is None
    assert schedule.id
    assert schedule.created_at == schedule.updated_at


def test_rm5_set_schedule_computes_next_run(tmp_path: Path) -> None:
    """next_run_at lands one interval ahead of now, as a UTC instant."""
    before = datetime.now(timezone.utc)
    schedule = set_schedule(_PIPELINE, 8, "UTC", _db(tmp_path))
    after = datetime.now(timezone.utc)

    next_run = datetime.fromisoformat(schedule.next_run_at)

    assert next_run.tzinfo is not None
    assert before + timedelta(hours=8) <= next_run <= after + timedelta(hours=8)


def test_rm5_get_schedule_returns_schedule(tmp_path: Path) -> None:
    """get_schedule returns the stored schedule; None when none is set."""
    db_path = _db(tmp_path)
    assert get_schedule(_PIPELINE, db_path) is None

    set_schedule(_PIPELINE, 12, "UTC", db_path)
    schedule = get_schedule(_PIPELINE, db_path)

    assert schedule is not None
    assert schedule.interval_hours == 12


def test_rm5_disable_sets_status_inactive(tmp_path: Path) -> None:
    """disable_schedule pauses without deleting the row."""
    db_path = _db(tmp_path)
    set_schedule(_PIPELINE, 8, "UTC", db_path)

    assert disable_schedule(_PIPELINE, db_path) is True

    schedule = get_schedule(_PIPELINE, db_path)
    assert schedule is not None
    assert schedule.status == INACTIVE
    assert schedule.is_active() is False
    # Disabling an absent schedule reports False rather than raising.
    assert disable_schedule("no-such-pipeline", db_path) is False


def test_rm5_enable_restores_active_status(tmp_path: Path) -> None:
    """enable_schedule reactivates and recomputes next_run_at from now."""
    db_path = _db(tmp_path)
    set_schedule(_PIPELINE, 8, "UTC", db_path)
    disable_schedule(_PIPELINE, db_path)

    assert enable_schedule(_PIPELINE, db_path) is True

    schedule = get_schedule(_PIPELINE, db_path)
    assert schedule is not None
    assert schedule.status == ACTIVE
    # A schedule resumed after a pause must not carry a stale past next-run.
    assert datetime.fromisoformat(schedule.next_run_at) > datetime.now(timezone.utc)


def test_rm5_remove_deletes_schedule(tmp_path: Path) -> None:
    """remove_schedule deletes the row and reports whether one existed."""
    db_path = _db(tmp_path)
    set_schedule(_PIPELINE, 8, "UTC", db_path)

    assert remove_schedule(_PIPELINE, db_path) is True
    assert get_schedule(_PIPELINE, db_path) is None
    assert remove_schedule(_PIPELINE, db_path) is False


def test_rm5_compute_next_run_adds_interval() -> None:
    """compute_next_run adds exactly the interval, including fractional hours."""
    start = datetime(2026, 7, 28, 6, 0, tzinfo=timezone.utc)

    assert compute_next_run(8, start) == datetime(
        2026, 7, 28, 14, 0, tzinfo=timezone.utc
    )
    assert compute_next_run(0.5, start) == datetime(
        2026, 7, 28, 6, 30, tzinfo=timezone.utc
    )


def test_rm5_schedule_history_returns_runs(tmp_path: Path) -> None:
    """History returns runs newest-first, honours limit, and advances the schedule."""
    db_path = _db(tmp_path)
    set_schedule(_PIPELINE, 8, "UTC", db_path)

    record_schedule_run(
        _PIPELINE, "success", "2026-07-28T00:00:00+00:00", None, 100, None, db_path
    )
    record_schedule_run(
        _PIPELINE, "failed", "2026-07-28T08:00:00+00:00", None, None, "boom", db_path
    )

    runs = get_schedule_history(_PIPELINE, 10, db_path)

    assert len(runs) == 2
    assert runs[0].status == "failed"  # newest first
    assert runs[0].error == "boom"
    assert runs[1].rows_loaded == 100
    assert get_schedule_history(_PIPELINE, 1, db_path) == runs[:1]

    # Recording a run advances the parent schedule's last_run_at.
    schedule = get_schedule(_PIPELINE, db_path)
    assert schedule is not None
    assert schedule.last_run_at == "2026-07-28T08:00:00+00:00"


def test_rm5_set_schedule_updates_existing(tmp_path: Path) -> None:
    """Re-setting preserves id and created_at, and reactivates a paused schedule."""
    db_path = _db(tmp_path)
    first = set_schedule(_PIPELINE, 8, "UTC", db_path)
    disable_schedule(_PIPELINE, db_path)

    second = set_schedule(_PIPELINE, 24, "America/New_York", db_path)

    assert second.id == first.id
    assert second.created_at == first.created_at
    assert second.interval_hours == 24
    assert second.status == ACTIVE  # setting an interval means intent to run
    assert len(get_all_schedules(db_path)) == 1


def test_rm5_set_schedule_rejects_invalid_interval_and_timezone(
    tmp_path: Path,
) -> None:
    """PK-RM-001 for an out-of-band interval, PK-RM-002 for an unknown timezone."""
    db_path = _db(tmp_path)

    with pytest.raises(ReleaseError) as interval_exc:
        set_schedule(_PIPELINE, 0, "UTC", db_path)
    assert interval_exc.value.code == "PK-RM-001"

    with pytest.raises(ReleaseError) as negative_exc:
        set_schedule(_PIPELINE, -8, "UTC", db_path)
    assert negative_exc.value.code == "PK-RM-001"

    with pytest.raises(ReleaseError) as tz_exc:
        set_schedule(_PIPELINE, 8, "Mars/Olympus_Mons", db_path)
    assert tz_exc.value.code == "PK-RM-002"

    # Nothing was persisted by any rejected call.
    assert get_schedule(_PIPELINE, db_path) is None


def test_rm5_platform_entry_windows_emits_task_xml() -> None:
    """The Windows entry carries Task Scheduler XML with an exact interval."""
    entry = generate_platform_scheduler_entry(
        _PIPELINE, 8, "C:\\bin\\pipelinekit.exe", "C:\\proj", platform="windows"
    )

    assert entry["platform"] == "windows"
    assert entry["task_name"] == f"PipelineKit-{_PIPELINE}"
    assert entry["cron_expression"] is None
    assert "<Interval>PT8H</Interval>" in entry["task_xml"]
    assert "C:\\proj" in entry["task_xml"]


def test_rm5_platform_entry_unix_emits_cron() -> None:
    """The unix entry carries a cron expression and flags approximation."""
    every_8h = generate_platform_scheduler_entry(
        _PIPELINE, 8, "/usr/bin/pipelinekit", "/proj", platform="unix"
    )
    assert every_8h["platform"] == "unix"
    assert every_8h["cron_expression"] == "0 */8 * * *"
    assert every_8h["task_xml"] is None
    assert "approximates" not in every_8h["instruction"]

    # cron cannot express "every 36 hours" — that must be stated, not hidden.
    every_36h = generate_platform_scheduler_entry(
        _PIPELINE, 36, "/usr/bin/pipelinekit", "/proj", platform="unix"
    )
    assert every_36h["cron_expression"] == "0 0 * * *"
    assert "approximates" in every_36h["instruction"]
