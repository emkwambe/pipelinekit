"""Release Management (RM) — scheduling.

RM-5 adds deterministic pipeline schedules stored in ``state.db``: an interval,
a timezone, and a computed next-run time, plus append-only run history. No AI.

PipelineKit records the schedule and emits the platform entry that would run it;
it does not run a daemon of its own. The OS scheduler (Windows Task Scheduler or
cron) remains the thing that actually fires — PipelineKit is not a workflow
scheduler replacement.
"""

from __future__ import annotations

from pipelinekit.scheduling.scheduler import (
    PipelineSchedule,
    ScheduleRun,
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

__all__ = [
    "PipelineSchedule",
    "ScheduleRun",
    "compute_next_run",
    "disable_schedule",
    "enable_schedule",
    "generate_platform_scheduler_entry",
    "get_all_schedules",
    "get_schedule",
    "get_schedule_history",
    "record_schedule_run",
    "remove_schedule",
    "set_schedule",
]
