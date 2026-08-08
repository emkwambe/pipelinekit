"""Release Management (RM) — staging → production promotion.

RM-4 builds transformations into a staging schema and promotes them into
production only once the whole build succeeds. A failed run leaves production
untouched, so production is never left holding half a run's output.

Opt-in: with ``transformation.staging.enabled`` false (the default), pipeline
behavior is unchanged.
"""

from __future__ import annotations

from pipelinekit.staging.promoter import (
    BUILDING,
    FAILED,
    PROMOTED,
    PROMOTING,
    ROLLED_BACK,
    TESTS_PASSING,
    StagingPromoter,
    StagingRun,
)

__all__ = [
    "BUILDING",
    "FAILED",
    "PROMOTED",
    "PROMOTING",
    "ROLLED_BACK",
    "TESTS_PASSING",
    "StagingPromoter",
    "StagingRun",
]
