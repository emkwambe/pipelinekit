"""Intelligence layer: AI-assisted diagnostics.

Deterministic first, AI second. The AI layer *interprets* evidence produced by
the deterministic systems (contracts, quality, state); it never defines truth,
never executes actions, and never modifies production. Every output validates
against ``schemas/diagnostic.schema.json`` before reaching the user.

See: SPEC-005, ADR-007, ADR-014, docs/ai/PIPELINEKIT-AI & Model Strategy Standard.

AI-7 (SPEC-032) adds EMS context injection: the diagnostics engine enriches its
evidence with quality, SLO, volume, drift, and contract signals from ``state.db``
so the AI can correlate them with a failure.
"""

from __future__ import annotations

from pipelinekit.ai.ems_context import (
    EMSContext,
    assemble_ems_context,
    format_ems_context_for_prompt,
)
from pipelinekit.ai.narrative import (
    build_narrative_prompt,
    generate_scorecard_narrative,
)

__all__ = [
    "EMSContext",
    "assemble_ems_context",
    "format_ems_context_for_prompt",
    # AI-8 — quality scorecard narrative (SPEC-033)
    "build_narrative_prompt",
    "generate_scorecard_narrative",
]
