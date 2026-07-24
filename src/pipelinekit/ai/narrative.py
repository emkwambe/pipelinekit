"""AI-8 — AI-assisted quality scorecard narrative (SPEC-033, ADR-034).

Turns a QM-8 ``BlueprintScore`` plus AI-7 ``EMSContext`` into a one-paragraph,
actionable narrative: root cause of the score, the single highest-priority fix,
and the expected score impact. Opt-in via ``pipelinekit quality scorecard
--narrative`` — the default scorecard makes no AI call.

The narrative is **informational**, not prescriptive (the trust model is
unchanged — nothing is executed). Generation is fully defensive: any provider
failure yields an empty string; ``generate_scorecard_narrative`` never raises.

Provider call: all concrete providers share a ``_complete(system, user) -> str``
text primitive. AI-8 uses it directly because the narrative is free prose — the
JSON-returning ``diagnose``/``architect`` methods would reject a prose response.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pipelinekit.ai.ems_context import EMSContext
    from pipelinekit.quality.scorecard import BlueprintScore

NARRATIVE_SYSTEM_PROMPT = (
    "You are a data pipeline quality advisor. Given a blueprint's quality "
    "scorecard and its EMS operational signals, write ONE concise, actionable "
    "paragraph. Use only the data provided — never invent signals. The narrative "
    "is informational, not a command to execute."
)


def build_narrative_prompt(
    blueprint_score: BlueprintScore,
    ems_context: EMSContext,
) -> str:
    """Build the structured user prompt for narrative generation.

    Includes the composite score, each component score, and any EMS signals, and
    asks for (1) root cause, (2) the single highest-priority fix, and (3) the
    expected score impact. Kept well under 500 tokens.
    """
    lines: list[str] = [
        f"Blueprint: {blueprint_score.blueprint_name}",
        f"Composite quality score: {blueprint_score.composite_score:.0f}/100 "
        f"({blueprint_score.rating})",
        "Component scores (weighted: coverage 40%, volume 30%, drift 20%, "
        "ownership 10%):",
    ]
    for component in blueprint_score.components:
        lines.append(
            f"- {component.name}: {component.score:.0f}/100 ({component.status})"
        )

    if ems_context.has_data:
        lines.append("")
        lines.append(f"EMS operational signals: {ems_context.summary}")
        for v in ems_context.slo_violations:
            lines.append(
                f"- SLO violation: {v['table']} {v['type']} "
                f"current={v['current']} threshold={v['threshold']}"
            )
        for a in ems_context.volume_anomalies:
            lines.append(
                f"- Volume anomaly: {a['table']} current={a['current']} "
                f"baseline={a['baseline']:.0f} ({a['deviation_pct']:+.1f}%)"
            )
        for d in ems_context.schema_drift:
            for item in d["drift_items"]:
                lines.append(
                    f"- Schema drift: {d['table']} {item['type']} {item['column']}"
                )
        for n in ems_context.pending_notifications:
            lines.append(f"- Contract change: {n['table']} {n['change']} ({n['type']})")

    lines.append("")
    lines.append(
        "In one short paragraph, explain: (1) the root cause of this score, "
        "(2) the single highest-priority fix to make first, and (3) the expected "
        "score impact if that fix is applied. Be specific and concise."
    )
    return "\n".join(lines)


def generate_scorecard_narrative(
    blueprint_score: BlueprintScore,
    ems_context: EMSContext,
    provider: Any,
    db_path: str,
) -> str:
    """Generate an AI narrative for a blueprint's quality score.

    Returns the narrative text, or an empty string if the provider call fails.
    Never raises — the confidence threshold does not apply (informational).
    ``db_path`` is accepted for signature stability (EMS context is already
    supplied by the caller).
    """
    try:
        prompt = build_narrative_prompt(blueprint_score, ems_context)
        text = provider._complete(NARRATIVE_SYSTEM_PROMPT, prompt)
        return (text or "").strip()
    except Exception:
        return ""
