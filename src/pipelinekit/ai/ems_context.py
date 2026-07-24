"""AI-7 — EMS operational context for AI diagnosis (SPEC-032, ADR-033).

Assembles the current Engineering Management System (EMS) state for a blueprint
from ``state.db`` and formats it for inclusion in the diagnosis prompt, so the AI
can correlate a pipeline failure with quality scores, SLO violations, volume
anomalies, schema drift, and pending contract changes.

Read-only and defensive: every signal source is wrapped in ``try/except`` and a
missing/failing source is simply skipped. ``assemble_ems_context`` never raises
and returns ``has_data=False`` when there is no EMS signal to report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EMSContext:
    """Structured EMS operational state for one blueprint."""

    blueprint_name: str
    quality_score: float | None  # QM-8 composite score
    quality_rating: str | None  # Excellent / Good / Fair / Poor
    slo_violations: list[dict] = field(default_factory=list)  # OM-4
    volume_anomalies: list[dict] = field(default_factory=list)  # QM-6
    schema_drift: list[dict] = field(default_factory=list)  # QM-7
    pending_notifications: list[dict] = field(default_factory=list)  # DC-10
    has_data: bool = False
    summary: str = ""


def assemble_ems_context(blueprint_name: str, db_path: str) -> EMSContext:
    """Assemble current EMS state for ``blueprint_name`` from ``state.db``.

    Every signal source is isolated in ``try/except`` so one failing source never
    stops the others. Returns ``has_data=False`` when nothing is available. Never
    raises.
    """
    quality_score: float | None = None
    quality_rating: str | None = None
    slo_violations: list[dict] = []
    volume_anomalies: list[dict] = []
    schema_drift: list[dict] = []
    pending_notifications: list[dict] = []

    blueprint_dir = str(Path("blueprints") / blueprint_name)

    # Quality scorecard (QM-8) — only for an actually-installed blueprint, since
    # compute_blueprint_score always returns a score (it would otherwise make
    # every unknown blueprint look like it "has data").
    try:
        if Path(blueprint_dir).is_dir():
            from pipelinekit.quality.scorecard import compute_blueprint_score

            bp_score = compute_blueprint_score(blueprint_name, blueprint_dir, db_path)
            quality_score = bp_score.composite_score
            quality_rating = bp_score.rating
    except Exception:
        pass

    # SLO violations (OM-4)
    try:
        from pipelinekit.observability.slo import check_slos

        for slo_result in check_slos(blueprint_name, db_path):
            if slo_result.status == "VIOLATED":
                slo_violations.append(
                    {
                        "table": slo_result.slo.table_name,
                        "type": slo_result.slo.slo_type,
                        "threshold": slo_result.slo.threshold,
                        "current": slo_result.current_value,
                        "status": slo_result.status,
                    }
                )
    except Exception:
        pass

    # Volume anomalies (QM-6)
    try:
        from pipelinekit.quality.anomaly import check_volume_anomalies
        from pipelinekit.state.db import (
            get_all_tables_for_blueprint,
            get_row_count_history,
        )

        for table in get_all_tables_for_blueprint(blueprint_name, db_path):
            history = get_row_count_history(blueprint_name, table, 1, db_path)
            if not history:
                continue
            current = {table: history[0]["row_count"]}
            for anomaly in check_volume_anomalies(blueprint_name, current, db_path):
                if anomaly.is_anomaly:
                    volume_anomalies.append(
                        {
                            "table": anomaly.table_name,
                            "current": anomaly.current_count,
                            "baseline": anomaly.baseline_avg,
                            "deviation_pct": anomaly.deviation_pct,
                        }
                    )
    except Exception:
        pass

    # Schema drift (QM-7)
    try:
        from pipelinekit.quality.drift import check_blueprint_drift

        for drift_result in check_blueprint_drift(
            blueprint_name, blueprint_dir, db_path
        ):
            if drift_result.status == "DRIFTED":
                schema_drift.append(
                    {
                        "table": drift_result.table_name,
                        "drift_items": [
                            {"type": d.drift_type.value, "column": d.name}
                            for d in drift_result.drift_items
                        ],
                    }
                )
    except Exception:
        pass

    # Pending contract changes (DC-10)
    try:
        from pipelinekit.contracts.notification import get_pending_notifications

        pending_notifications = [
            {
                "blueprint": n.blueprint_name,
                "table": n.table_name,
                "change": f"{n.old_version} -> {n.new_version}",
                "type": n.change_type,
            }
            for n in get_pending_notifications(db_path)
            if n.blueprint_name == blueprint_name
        ]
    except Exception:
        pass

    has_data = any(
        [
            quality_score is not None,
            bool(slo_violations),
            bool(volume_anomalies),
            bool(schema_drift),
            bool(pending_notifications),
        ]
    )

    issues: list[str] = []
    if slo_violations:
        issues.append(f"{len(slo_violations)} SLO violation(s)")
    if volume_anomalies:
        issues.append(f"{len(volume_anomalies)} volume anomaly(ies)")
    if schema_drift:
        issues.append(f"{len(schema_drift)} drifted table(s)")
    if pending_notifications:
        issues.append(f"{len(pending_notifications)} contract change(s)")

    if issues:
        summary = f"EMS signals: {', '.join(issues)}"
    elif quality_score is not None:
        summary = f"EMS healthy (score: {quality_score:.0f} {quality_rating})"
    else:
        summary = "No EMS data available for this blueprint"

    return EMSContext(
        blueprint_name=blueprint_name,
        quality_score=quality_score,
        quality_rating=quality_rating,
        slo_violations=slo_violations,
        volume_anomalies=volume_anomalies,
        schema_drift=schema_drift,
        pending_notifications=pending_notifications,
        has_data=has_data,
        summary=summary,
    )


def format_ems_context_for_prompt(ctx: EMSContext) -> str:
    """Format an ``EMSContext`` as a prompt section, or ``""`` if no data."""
    if not ctx.has_data:
        return ""

    lines: list[str] = [f"## EMS Operational Context for {ctx.blueprint_name}"]
    if ctx.quality_score is not None:
        lines.append(
            f"Quality Score: {ctx.quality_score:.0f}/100 ({ctx.quality_rating})"
        )
    lines.append("")

    if ctx.slo_violations:
        lines.append("### SLO Violations (OM-4)")
        for v in ctx.slo_violations:
            lines.append(
                f"- {v['table']} {v['type']}: current={v['current']}, "
                f"threshold={v['threshold']} -> VIOLATED"
            )
        lines.append("")

    if ctx.volume_anomalies:
        lines.append("### Volume Anomalies (QM-6)")
        for a in ctx.volume_anomalies:
            lines.append(
                f"- {a['table']}: {a['current']:,} rows vs baseline "
                f"{a['baseline']:,.0f} ({a['deviation_pct']:+.1f}%)"
            )
        lines.append("")

    if ctx.schema_drift:
        lines.append("### Schema Drift (QM-7)")
        for d in ctx.schema_drift:
            for item in d["drift_items"]:
                lines.append(f"- {d['table']}: {item['type']} -> {item['column']}")
        lines.append("")

    if ctx.pending_notifications:
        lines.append("### Pending Contract Changes (DC-10)")
        for n in ctx.pending_notifications:
            lines.append(
                f"- {n['table']}: contract changed {n['change']} ({n['type']})"
            )
        lines.append("")

    lines.append("Use these EMS signals to correlate with the pipeline failure.")
    lines.append(
        "Multiple signals pointing to the same table suggest a common root cause."
    )
    return "\n".join(lines)
