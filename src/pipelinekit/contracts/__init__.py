"""Data contracts: the deterministic mechanism that defines and enforces truth.

Contracts are first-class YAML artifacts. Validation is purely deterministic —
no AI. Violations carry PK error codes and structured evidence for Phase 4 AI
diagnosis (SPEC-004, Principle 4 — Contracts Define Truth).

DC-8 (SPEC-020) adds deterministic schema versioning on top of validation.
"""

from __future__ import annotations

from pipelinekit.contracts.versioning import (
    ContractDiff,
    ContractVersion,
    diff_contract_versions,
    get_contract_history,
    get_contract_version,
    snapshot_contract,
)

__all__ = [
    "ContractVersion",
    "ContractDiff",
    "snapshot_contract",
    "get_contract_version",
    "get_contract_history",
    "diff_contract_versions",
]
