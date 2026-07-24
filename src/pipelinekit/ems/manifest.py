"""EMS Manifest — maps the twelve Engineering Management Systems.

Maps each EMS to its shipped capabilities, CLI command groups, and ``state.db``
tables. This is the canonical, declarative source used by ``pipelinekit ems
list`` and ``pipelinekit ems status`` — it is data, not computed from the
codebase at runtime, and must be kept in sync with what is actually built
(``docs/reference/EMS-STATUS.md``).

Capability codes reflect ADR-043 (AI code reconciliation): AI-7/8/9 are reserved
for their taxonomy meanings (Prompt Governance, Agent Registry, Evaluation
Pipeline) and the three built capabilities are AI-13/14/15.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EMSCapability:
    """One capability within an EMS, keyed by its taxonomy code."""

    code: str  # e.g. "DC-8" or a range "DC-1..7"
    name: str  # e.g. "Schema versioning"
    status: str  # "built" | "partial" | "planned" | "not_started"
    phase: str | None  # "Phase 1".."Phase 6" | None


@dataclass
class EMSDefinition:
    """One Engineering Management System and its capability inventory."""

    code: str  # e.g. "DC"
    ems_id: str  # e.g. "EMS-008"
    name: str  # e.g. "Data Contract Management"
    description: str  # one sentence
    capabilities: list[EMSCapability]
    cli_commands: list[str]  # top-level command groups
    state_tables: list[str]  # state.db tables this EMS owns
    total_planned: int  # from the taxonomy


EMS_MANIFEST: list[EMSDefinition] = [
    EMSDefinition(
        code="DC",
        ems_id="EMS-008",
        name="Data Contract Management",
        description="Version, validate, and govern data contracts across pipelines.",
        capabilities=[
            EMSCapability(
                "DC-1..7", "Contract definition and validation", "built", "Phase 1"
            ),
            EMSCapability("DC-8", "Schema versioning", "built", "Phase 2"),
            EMSCapability("DC-9", "Breaking change detection", "built", "Phase 2"),
            EMSCapability("DC-10", "Consumer notification", "built", "Phase 2"),
            EMSCapability("DC-11", "Contract lifecycle management", "built", "Phase 3"),
            EMSCapability("DC-12", "Producer/consumer registry", "partial", "Phase 3"),
        ],
        cli_commands=["contract"],
        state_tables=[
            "dc_contract_versions",
            "dc_consumers",
            "dc_notifications",
            "dc_contract_lifecycle",
        ],
        total_planned=12,
    ),
    EMSDefinition(
        code="QM",
        ems_id="EMS-002",
        name="Quality Management",
        description="Measure, monitor, and enforce data quality across all pipelines.",
        capabilities=[
            EMSCapability(
                "QM-1..3", "Source/transform quality checks", "built", "Phase 1"
            ),
            EMSCapability("QM-4", "Coverage monitoring", "built", "Phase 2"),
            EMSCapability("QM-5", "Freshness SLA enforcement", "built", "Phase 3"),
            EMSCapability("QM-6", "Volume anomaly detection", "built", "Phase 2"),
            EMSCapability("QM-7", "Schema drift detection", "built", "Phase 2"),
            EMSCapability("QM-8", "Quality scorecard", "built", "Phase 2"),
            EMSCapability("QM-9", "Regression testing", "built", "Phase 3"),
        ],
        cli_commands=["quality"],
        state_tables=[
            "qm_row_counts",
            "qm_freshness_requirements",
            "qm_scorecard_snapshots",
        ],
        total_planned=9,
    ),
    EMSDefinition(
        code="GM",
        ems_id="EMS-001",
        name="Governance Management",
        description=(
            "Assign ownership, enforce naming conventions, and manage change "
            "approvals."
        ),
        capabilities=[
            EMSCapability("GM-1", "Ownership assignment", "built", "Phase 2"),
            EMSCapability("GM-2", "Naming convention enforcement", "built", "Phase 2"),
            EMSCapability("GM-3", "Approval workflow", "built", "Phase 2"),
            EMSCapability("GM-4", "Repository standards", "planned", "Phase 4"),
            EMSCapability("GM-5", "Architecture review gate", "planned", "Phase 4"),
            EMSCapability("GM-6", "Data lineage governance", "planned", "Phase 4"),
            EMSCapability("GM-7", "Governance dashboard", "planned", "Phase 4"),
            EMSCapability("GM-8", "Policy enforcement engine", "planned", "Phase 5"),
            EMSCapability("GM-9", "Governance reporting", "planned", "Phase 5"),
        ],
        cli_commands=["governance"],
        state_tables=[
            "gm_owners",
            "gm_conventions",
            "gm_approvers",
            "gm_approval_requests",
        ],
        total_planned=9,
    ),
    EMSDefinition(
        code="OM",
        ems_id="EMS-006",
        name="Observability Management",
        description=(
            "Monitor pipeline health, define SLOs, and track compliance over time."
        ),
        capabilities=[
            EMSCapability("OM-1..3", "Health check + alerting", "built", "Phase 1"),
            EMSCapability("OM-4", "SLO definition and evaluation", "built", "Phase 2"),
            EMSCapability("OM-5", "SLO compliance dashboard", "built", "Phase 3"),
            EMSCapability("OM-6", "Incident timeline", "planned", "Phase 4"),
            EMSCapability("OM-7", "Cost observability", "planned", "Phase 5"),
            EMSCapability("OM-8", "PagerDuty integration", "planned", "Phase 4"),
            EMSCapability("OM-9", "Pipeline health score", "planned", "Phase 4"),
        ],
        cli_commands=["observability", "health"],
        state_tables=[
            "om_slos",
            "om_slo_runs",
            "health_runs",
        ],
        total_planned=9,
    ),
    EMSDefinition(
        code="AM",
        ems_id="EMS-004",
        name="Architecture Management",
        description="Map blueprint dependencies and detect architectural drift.",
        capabilities=[
            EMSCapability(
                "AM-1..3",
                "ADR templates + blueprint validation",
                "built",
                "Phase 1",
            ),
            EMSCapability("AM-4", "Dependency analysis", "built", "Phase 2"),
            EMSCapability("AM-5", "Architecture drift detection", "built", "Phase 3"),
            EMSCapability(
                "AM-6", "Reference architecture library", "planned", "Phase 4"
            ),
            EMSCapability(
                "AM-7", "Architecture compliance score", "planned", "Phase 4"
            ),
            EMSCapability("AM-8", "Architecture reporting", "planned", "Phase 5"),
        ],
        cli_commands=["architect"],
        state_tables=[
            "am_dependencies",
        ],
        total_planned=8,
    ),
    EMSDefinition(
        code="AI",
        ems_id="EMS-010",
        name="AI Management",
        description=(
            "Govern AI providers, trust boundaries, and intelligence across "
            "pipelines."
        ),
        capabilities=[
            EMSCapability(
                "AI-1", "Provider abstraction (6 providers)", "built", "Phase 1"
            ),
            EMSCapability("AI-2", "Blueprint generation", "built", "Phase 1"),
            EMSCapability("AI-3", "Diagnostics engine", "built", "Phase 1"),
            EMSCapability("AI-4", "Confidence scoring", "built", "Phase 1"),
            EMSCapability("AI-5", "AI trust model", "built", "Phase 1"),
            EMSCapability(
                "AI-6", "Multi-provider routing + cascade", "built", "Phase 1"
            ),
            EMSCapability("AI-7", "Prompt governance", "planned", "Phase 4"),
            EMSCapability("AI-8", "Agent registry", "planned", "Phase 4"),
            EMSCapability("AI-9", "Evaluation pipeline", "planned", "Phase 4"),
            EMSCapability("AI-10", "Hallucination monitoring", "planned", "Phase 4"),
            EMSCapability("AI-11", "AI acceptance tracking", "planned", "Phase 4"),
            EMSCapability("AI-12", "Fine-tuned model management", "planned", "Phase 5"),
            EMSCapability("AI-13", "EMS context injection", "built", "Phase 3"),
            EMSCapability("AI-14", "Quality scorecard narrative", "built", "Phase 3"),
            EMSCapability(
                "AI-15", "EMS-aware confidence recalibration", "built", "Phase 3"
            ),
        ],
        cli_commands=["generate", "diagnose"],
        state_tables=[],
        total_planned=15,
    ),
    EMSDefinition(
        code="RM",
        ems_id="EMS-012",
        name="Release Management",
        description=(
            "Coordinate blueprint versioning, upgrades, and release approval."
        ),
        capabilities=[
            EMSCapability(
                "RM-1..3", "Blueprint versioning + lifecycle", "built", "Phase 1"
            ),
            EMSCapability("RM-4", "Release approval workflow", "planned", "Phase 4"),
            EMSCapability("RM-5", "Rollback coordination", "planned", "Phase 4"),
            EMSCapability("RM-6", "Release notes generation", "planned", "Phase 5"),
            EMSCapability("RM-7", "Multi-environment promotion", "planned", "Phase 5"),
            EMSCapability("RM-8", "Release reporting", "planned", "Phase 5"),
        ],
        cli_commands=["blueprint"],
        state_tables=[],
        total_planned=8,
    ),
    EMSDefinition(
        code="KM",
        ems_id="EMS-003",
        name="Knowledge Management",
        description=(
            "Capture, version, and serve institutional pipeline knowledge via MCP."
        ),
        capabilities=[
            EMSCapability("KM-1", "Knowledge capture", "not_started", "Phase 3"),
            EMSCapability("KM-2", "Knowledge versioning", "not_started", "Phase 3"),
            EMSCapability("KM-3", "Knowledge search", "not_started", "Phase 3"),
            EMSCapability(
                "KM-4", "Knowledge recommendations", "not_started", "Phase 4"
            ),
            EMSCapability("KM-5", "Knowledge validation", "not_started", "Phase 4"),
            EMSCapability("KM-6", "Knowledge analytics", "not_started", "Phase 4"),
            EMSCapability("KM-7", "MCP knowledge endpoint", "not_started", "Phase 3"),
            EMSCapability("KM-8", "Knowledge export", "not_started", "Phase 5"),
            EMSCapability("KM-9", "Knowledge reporting", "not_started", "Phase 5"),
        ],
        cli_commands=[],
        state_tables=[],
        total_planned=9,
    ),
    EMSDefinition(
        code="CM",
        ems_id="EMS-007",
        name="Compliance Management",
        description=(
            "Map, track, and evidence SOC 2, GDPR, and regulatory compliance."
        ),
        capabilities=[
            EMSCapability("CM-1", "SOC 2 control mapping", "not_started", "Phase 4"),
            EMSCapability("CM-2", "Evidence collection", "not_started", "Phase 4"),
            EMSCapability("CM-3", "Compliance scoring", "not_started", "Phase 4"),
            EMSCapability("CM-4", "Audit trail", "not_started", "Phase 4"),
            EMSCapability("CM-5", "GDPR mapping", "not_started", "Phase 5"),
            EMSCapability("CM-6", "Compliance reporting", "not_started", "Phase 4"),
            EMSCapability("CM-7", "Control testing", "not_started", "Phase 5"),
            EMSCapability("CM-8", "Remediation tracking", "not_started", "Phase 5"),
            EMSCapability("CM-9", "Compliance dashboard", "not_started", "Phase 5"),
            EMSCapability(
                "CM-10", "Certification management", "not_started", "Phase 6"
            ),
        ],
        cli_commands=[],
        state_tables=[],
        total_planned=10,
    ),
    EMSDefinition(
        code="SM",
        ems_id="EMS-009",
        name="Security Management",
        description=(
            "Scan dependencies, enforce access controls, and manage security "
            "posture."
        ),
        capabilities=[
            EMSCapability("SM-1", "Access control framework", "not_started", "Phase 4"),
            EMSCapability(
                "SM-2", "Dependency vulnerability scanning", "partial", "Phase 1"
            ),
            EMSCapability("SM-3", "Secret detection", "not_started", "Phase 4"),
            EMSCapability(
                "SM-4", "Security policy enforcement", "not_started", "Phase 4"
            ),
            EMSCapability("SM-5", "Security scoring", "not_started", "Phase 5"),
            EMSCapability(
                "SM-6", "Penetration test integration", "not_started", "Phase 5"
            ),
            EMSCapability("SM-7", "Security reporting", "not_started", "Phase 5"),
        ],
        cli_commands=[],
        state_tables=[],
        total_planned=7,
    ),
    EMSDefinition(
        code="CO",
        ems_id="EMS-011",
        name="Cost Management",
        description="Track, allocate, and optimize data infrastructure costs.",
        capabilities=[
            EMSCapability("CO-1", "Cost tracking", "not_started", "Phase 5"),
            EMSCapability("CO-2", "Cost allocation", "not_started", "Phase 5"),
            EMSCapability(
                "CO-3", "Cost optimization recommendations", "not_started", "Phase 5"
            ),
            EMSCapability("CO-4", "Budget alerting", "not_started", "Phase 5"),
            EMSCapability("CO-5", "Cost forecasting", "not_started", "Phase 6"),
            EMSCapability(
                "CO-6", "Cross-cloud cost comparison", "not_started", "Phase 6"
            ),
            EMSCapability("CO-7", "Cost reporting", "not_started", "Phase 5"),
            EMSCapability("CO-8", "ROI measurement", "not_started", "Phase 6"),
        ],
        cli_commands=[],
        state_tables=[],
        total_planned=8,
    ),
    EMSDefinition(
        code="DM",
        ems_id="EMS-005",
        name="Documentation Management",
        description=(
            "Generate, version, and maintain pipeline documentation automatically."
        ),
        capabilities=[
            EMSCapability("DM-1", "Documentation generation", "not_started", "Phase 5"),
            EMSCapability("DM-2", "Documentation versioning", "not_started", "Phase 5"),
            EMSCapability("DM-3", "Documentation search", "not_started", "Phase 5"),
            EMSCapability("DM-4", "Documentation freshness", "not_started", "Phase 5"),
            EMSCapability("DM-5", "Documentation templates", "not_started", "Phase 5"),
            EMSCapability("DM-6", "Documentation export", "not_started", "Phase 6"),
            EMSCapability("DM-7", "Documentation analytics", "not_started", "Phase 6"),
            EMSCapability("DM-8", "Documentation reporting", "not_started", "Phase 6"),
        ],
        cli_commands=[],
        state_tables=[],
        total_planned=8,
    ),
]


def get_ems(code: str) -> EMSDefinition | None:
    """Get an EMS definition by its code (e.g. 'DC', 'QM'). Case-insensitive."""
    return next((e for e in EMS_MANIFEST if e.code.upper() == code.upper()), None)


def get_all_ems() -> list[EMSDefinition]:
    """Return all twelve EMS definitions."""
    return EMS_MANIFEST


def _codes_in(code: str) -> int:
    """Number of individual capabilities a code entry represents.

    A range like ``"DC-1..7"`` counts as 7; a single code like ``"DC-8"`` as 1.
    This lets a grouped entry contribute its true weight to coverage so a
    near-complete domain reads as (e.g.) 11/12 rather than 6/12.
    """
    prefix, _, tail = code.rpartition("-")
    if ".." in tail:
        start_s, _, end_s = tail.partition("..")
        try:
            return int(end_s) - int(start_s) + 1
        except ValueError:
            return 1
    return 1


def compute_coverage(ems: EMSDefinition) -> tuple[float, int]:
    """Return ``(built, total_planned)`` counting individual capability codes.

    A ``built`` capability contributes its full code count; a ``partial`` one
    contributes half. ``built`` is a float because a partial capability (e.g.
    SM-2) yields a half — displayed trimmed (``0.5``, ``11.5``, ``9``).
    """
    built = 0.0
    for c in ems.capabilities:
        weight = _codes_in(c.code)
        if c.status == "built":
            built += weight
        elif c.status == "partial":
            built += weight * 0.5
    return built, ems.total_planned
