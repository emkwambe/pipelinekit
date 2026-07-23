"""Data contracts: the deterministic mechanism that defines and enforces truth.

Contracts are first-class YAML artifacts. Validation is purely deterministic —
no AI. Violations carry PK error codes and structured evidence for Phase 4 AI
diagnosis (SPEC-004, Principle 4 — Contracts Define Truth).

DC-8 (SPEC-020) adds deterministic schema versioning on top of validation.
DC-9 (SPEC-021) adds deterministic breaking-change detection with dbt impact.
DC-10 (SPEC-027) adds consumer registration and contract change notifications.
"""

from __future__ import annotations

from pipelinekit.contracts.notification import (
    ContractConsumer,
    ContractNotification,
    create_notifications,
    get_consumers,
    get_pending_notifications,
    mark_all_read,
    register_consumer,
    remove_consumer,
)
from pipelinekit.contracts.versioning import (
    BreakingChange,
    ContractDiff,
    ContractVersion,
    DbtImpact,
    detect_breaking_changes,
    diff_contract_versions,
    get_contract_history,
    get_contract_version,
    scan_dbt_impact,
    snapshot_contract,
)

__all__ = [
    "ContractVersion",
    "ContractDiff",
    "DbtImpact",
    "BreakingChange",
    "snapshot_contract",
    "get_contract_version",
    "get_contract_history",
    "diff_contract_versions",
    "detect_breaking_changes",
    "scan_dbt_impact",
    # DC-10 — consumer notification (SPEC-027)
    "ContractConsumer",
    "ContractNotification",
    "register_consumer",
    "get_consumers",
    "remove_consumer",
    "create_notifications",
    "get_pending_notifications",
    "mark_all_read",
]
