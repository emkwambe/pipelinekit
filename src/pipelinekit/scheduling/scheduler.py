"""RM-5 — pipeline schedule management.

Records *when* a pipeline should run and what the platform entry to run it looks
like. Purely deterministic — no AI, no daemon, no background thread. The OS
scheduler (Windows Task Scheduler or cron) is what actually fires the run;
PipelineKit stores the intent, computes the next run time, and prints the entry
to install. Scheduling state is operational state, so it lives in ``state.db``
rather than in ``pipelinekit.yaml``.

Times are stored as timezone-aware ISO 8601 UTC strings. The ``timezone`` field
records the zone the operator reasons in and is used only for display — the
stored instants stay unambiguous.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pipelinekit.core.errors import ReleaseError
from pipelinekit.state import db

ACTIVE = "active"
INACTIVE = "inactive"

# A schedule must fire at least once a year and no more than once a minute.
# Outside that band the entry is almost certainly a unit mistake (seconds passed
# as hours, or days passed as hours), not a real operational intent.
_MIN_INTERVAL_HOURS = 1.0 / 60.0
_MAX_INTERVAL_HOURS = 24.0 * 366.0


@dataclass
class PipelineSchedule:
    """A pipeline's recorded run schedule."""

    id: str
    pipeline_name: str
    interval_hours: float
    timezone: str
    status: str
    last_run_at: str | None
    next_run_at: str
    created_at: str
    updated_at: str

    def is_active(self) -> bool:
        """Return True when this schedule is enabled."""
        return self.status == ACTIVE


@dataclass
class ScheduleRun:
    """One recorded execution of a scheduled pipeline."""

    id: str
    pipeline_name: str
    triggered_by: str
    started_at: str
    completed_at: str | None
    status: str
    rows_loaded: int | None
    error: str | None


def _utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(dt_timezone.utc)


def _row_to_schedule(row: dict) -> PipelineSchedule:
    """Rebuild a ``PipelineSchedule`` from a stored ``rm_schedules`` row."""
    return PipelineSchedule(
        id=row["id"],
        pipeline_name=row["pipeline_name"],
        interval_hours=row["interval_hours"],
        timezone=row["timezone"],
        status=row["status"],
        last_run_at=row["last_run_at"],
        next_run_at=row["next_run_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_run(row: dict) -> ScheduleRun:
    """Rebuild a ``ScheduleRun`` from a stored ``rm_schedule_runs`` row."""
    return ScheduleRun(
        id=row["id"],
        pipeline_name=row["pipeline_name"],
        triggered_by=row["triggered_by"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        status=row["status"],
        rows_loaded=row["rows_loaded"],
        error=row["error"],
    )


def validate_interval(interval_hours: float) -> float:
    """Validate a schedule interval in hours and return it.

    Raises:
        ReleaseError: ``PK-RM-001`` if the interval is not a positive number
            inside the supported band.
    """
    if interval_hours != interval_hours or interval_hours in (
        float("inf"),
        float("-inf"),
    ):
        raise ReleaseError(
            "PK-RM-001",
            f"Interval must be a real number of hours, got {interval_hours!r}.",
            {"interval_hours": interval_hours},
        )
    if interval_hours < _MIN_INTERVAL_HOURS or interval_hours > _MAX_INTERVAL_HOURS:
        raise ReleaseError(
            "PK-RM-001",
            f"Interval must be between one minute and one year, "
            f"got {interval_hours} hour(s).",
            {"interval_hours": interval_hours},
        )
    return interval_hours


def validate_timezone(timezone_str: str) -> str:
    """Validate an IANA timezone name and return it.

    Raises:
        ReleaseError: ``PK-RM-002`` if the timezone is unknown on this system.
    """
    try:
        ZoneInfo(timezone_str)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ReleaseError(
            "PK-RM-002",
            f"Unknown timezone: {timezone_str!r}. Use an IANA name, e.g. "
            "'UTC' or 'America/New_York'.",
            {"timezone": timezone_str},
        ) from exc
    return timezone_str


def compute_next_run(interval_hours: float, from_time: datetime) -> datetime:
    """Compute the next run time by adding the interval to ``from_time``."""
    return from_time + timedelta(hours=interval_hours)


def set_schedule(
    pipeline_name: str,
    interval_hours: float,
    timezone_str: str,
    db_path: str,
) -> PipelineSchedule:
    """Create or update a pipeline's schedule.

    Re-setting a schedule preserves its ``id`` and ``created_at``. Re-setting an
    inactive schedule reactivates it — setting an interval expresses intent to
    run, so leaving it paused would be surprising.

    Raises:
        ReleaseError: ``PK-RM-001`` for an invalid interval, ``PK-RM-002`` for
            an unknown timezone.
    """
    validate_interval(interval_hours)
    validate_timezone(timezone_str)

    existing = db.get_schedule(pipeline_name, db_path)
    now = _utc_now()
    now_iso = now.isoformat()
    if existing is not None:
        schedule_id = existing["id"]
        created_at = existing["created_at"]
        last_run_at = existing["last_run_at"]
    else:
        schedule_id = str(uuid.uuid4())
        created_at = now_iso
        last_run_at = None

    schedule = PipelineSchedule(
        id=schedule_id,
        pipeline_name=pipeline_name,
        interval_hours=interval_hours,
        timezone=timezone_str,
        status=ACTIVE,
        last_run_at=last_run_at,
        next_run_at=compute_next_run(interval_hours, now).isoformat(),
        created_at=created_at,
        updated_at=now_iso,
    )
    db.upsert_schedule(schedule, db_path)
    return schedule


def get_schedule(pipeline_name: str, db_path: str) -> PipelineSchedule | None:
    """Return a pipeline's schedule, or None if none is set."""
    row = db.get_schedule(pipeline_name, db_path)
    return _row_to_schedule(row) if row is not None else None


def get_all_schedules(db_path: str) -> list[PipelineSchedule]:
    """Return every stored pipeline schedule."""
    return [_row_to_schedule(row) for row in db.get_all_schedules(db_path)]


def _set_status(pipeline_name: str, status: str, db_path: str) -> bool:
    """Set a schedule's status. Return False when no schedule exists."""
    row = db.get_schedule(pipeline_name, db_path)
    if row is None:
        return False

    schedule = _row_to_schedule(row)
    schedule.status = status
    schedule.updated_at = _utc_now().isoformat()
    db.upsert_schedule(schedule, db_path)
    return True


def disable_schedule(pipeline_name: str, db_path: str) -> bool:
    """Pause a schedule without deleting it. Return False if none exists."""
    return _set_status(pipeline_name, INACTIVE, db_path)


def enable_schedule(pipeline_name: str, db_path: str) -> bool:
    """Resume a paused schedule. Return False if none exists.

    Re-enabling recomputes ``next_run_at`` from now: a schedule paused for a week
    should not immediately fire on a next-run time that has long since passed.
    """
    row = db.get_schedule(pipeline_name, db_path)
    if row is None:
        return False

    schedule = _row_to_schedule(row)
    now = _utc_now()
    schedule.status = ACTIVE
    schedule.next_run_at = compute_next_run(schedule.interval_hours, now).isoformat()
    schedule.updated_at = now.isoformat()
    db.upsert_schedule(schedule, db_path)
    return True


def remove_schedule(pipeline_name: str, db_path: str) -> bool:
    """Delete a schedule entirely. Return True if one was removed."""
    return db.delete_schedule(pipeline_name, db_path)


def record_schedule_run(
    pipeline_name: str,
    status: str,
    started_at: str,
    completed_at: str | None,
    rows_loaded: int | None,
    error: str | None,
    db_path: str,
    triggered_by: str = "scheduler",
) -> ScheduleRun:
    """Append one scheduled run to history and advance the schedule.

    Recording a run updates the parent schedule's ``last_run_at`` and
    ``next_run_at`` when a schedule exists; history for a pipeline with no
    schedule is still recorded, so a manual run is never lost.
    """
    run = ScheduleRun(
        id=str(uuid.uuid4()),
        pipeline_name=pipeline_name,
        triggered_by=triggered_by,
        started_at=started_at,
        completed_at=completed_at,
        status=status,
        rows_loaded=rows_loaded,
        error=error,
    )
    db.insert_schedule_run(run, db_path)

    row = db.get_schedule(pipeline_name, db_path)
    if row is not None:
        schedule = _row_to_schedule(row)
        now = _utc_now()
        schedule.last_run_at = started_at
        schedule.next_run_at = compute_next_run(
            schedule.interval_hours, now
        ).isoformat()
        schedule.updated_at = now.isoformat()
        db.upsert_schedule(schedule, db_path)
    return run


def get_schedule_history(
    pipeline_name: str | None, limit: int, db_path: str
) -> list[ScheduleRun]:
    """Return the most recent scheduled runs, newest first."""
    rows = db.get_schedule_history(pipeline_name, limit, db_path)
    return [_row_to_run(row) for row in rows]


def format_next_run(schedule: PipelineSchedule) -> str:
    """Render ``next_run_at`` in the schedule's own timezone, for display."""
    moment = datetime.fromisoformat(schedule.next_run_at)
    try:
        local = moment.astimezone(ZoneInfo(schedule.timezone))
    except (ZoneInfoNotFoundError, ValueError):
        return moment.strftime("%Y-%m-%d %H:%M %Z")
    return local.strftime("%Y-%m-%d %H:%M %Z")


def _cron_expression(interval_hours: float) -> str:
    """Return a cron expression approximating an interval in hours.

    cron has no sub-hour-granularity 'every N hours' form beyond the step
    syntax, so intervals map as follows: under an hour becomes a minute step,
    whole hours up to a day become an hour step, and anything longer runs daily.
    The instruction text states the approximation so it is never silent.
    """
    if interval_hours < 1:
        minutes = max(1, round(interval_hours * 60))
        return f"*/{minutes} * * * *"
    if interval_hours < 24 and float(interval_hours).is_integer():
        return f"0 */{int(interval_hours)} * * *"
    if interval_hours < 24:
        return f"0 */{max(1, round(interval_hours))} * * *"
    return "0 0 * * *"


def _task_scheduler_xml(
    pipeline_name: str, interval_hours: float, command: str, cwd: str
) -> str:
    """Return a Windows Task Scheduler definition for a pipeline schedule.

    The trigger repeats on an ISO 8601 duration, which — unlike cron — expresses
    the interval exactly, so no approximation is needed on Windows.
    """
    total_minutes = max(1, round(interval_hours * 60))
    if total_minutes % 60 == 0:
        repetition = f"PT{total_minutes // 60}H"
    else:
        repetition = f"PT{total_minutes}M"

    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>PipelineKit scheduled run for {pipeline_name}</Description>
    <URI>\\PipelineKit-{pipeline_name}</URI>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>{repetition}</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2000-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{command}</Command>
      <Arguments>run</Arguments>
      <WorkingDirectory>{cwd}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""


def generate_platform_scheduler_entry(
    pipeline_name: str,
    interval_hours: float,
    pipelinekit_path: str,
    cwd: str,
    platform: str | None = None,
) -> dict:
    """Return the platform entry that would run this pipeline on schedule.

    PipelineKit generates the entry; it never installs it. Registering an OS
    task is a change to the machine, so it stays an explicit operator action.

    ``platform`` defaults to the current OS ('windows' or 'unix') and is
    overridable so the generated entry can be inspected for either platform.
    """
    import sys

    resolved = platform or ("windows" if sys.platform.startswith("win") else "unix")

    if resolved == "windows":
        task_name = f"PipelineKit-{pipeline_name}"
        return {
            "platform": "windows",
            "task_name": task_name,
            "instruction": (
                f"Register with Task Scheduler: schtasks /Create /TN "
                f"{task_name} /XML <saved-xml-path>"
            ),
            "command": f"{pipelinekit_path} run",
            "cron_expression": None,
            "task_xml": _task_scheduler_xml(
                pipeline_name, interval_hours, pipelinekit_path, cwd
            ),
        }

    cron = _cron_expression(interval_hours)
    approximate = interval_hours >= 24 or (
        interval_hours >= 1 and not float(interval_hours).is_integer()
    )
    note = " (cron approximates this interval)" if approximate else ""
    return {
        "platform": "unix",
        "task_name": f"pipelinekit-{pipeline_name}",
        "instruction": (
            f"Add to crontab{note}: {cron} cd {cwd} && {pipelinekit_path} run"
        ),
        "command": f"cd {cwd} && {pipelinekit_path} run",
        "cron_expression": cron,
        "task_xml": None,
    }
