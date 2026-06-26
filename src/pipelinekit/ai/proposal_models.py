"""Data models for the AI Blueprint Proposal subsystem (SPEC-015, ADR-018).

This is a *proposal* system, not a generation system: AI proposes artifacts and
humans approve what becomes part of the repository. Every ``ProposedAsset`` moves
through an explicit state machine and only ``apply()`` writes to disk — and only
assets a human has APPROVED.

State machine (code-enforced; invalid transitions raise ``PK-GEN-007``):

    proposed → approved → written → validated
    proposed → rejected
    proposed → edited → proposed   (re-proposed after edit)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from pipelinekit.core.errors import ProposalError


class AssetState(Enum):
    """The six states a proposed asset may occupy (ADR-018)."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    WRITTEN = "written"
    VALIDATED = "validated"


# The only valid transitions. Anything else raises ProposalError(PK-GEN-007).
_VALID_TRANSITIONS: dict[AssetState, set[AssetState]] = {
    AssetState.PROPOSED: {AssetState.APPROVED, AssetState.REJECTED, AssetState.EDITED},
    AssetState.EDITED: {AssetState.PROPOSED},
    AssetState.APPROVED: {AssetState.WRITTEN},
    AssetState.WRITTEN: {AssetState.VALIDATED},
    AssetState.REJECTED: set(),
    AssetState.VALIDATED: set(),
}


@dataclass
class AssetProvenance:
    """Provenance metadata for one proposed asset (9 fields, SPEC-015).

    Informs the human reviewer; **stripped from the file content on write** —
    it never ships in the blueprint.
    """

    generated_by: str = "pipelinekit"
    generation_mode: str = "ai_proposed"
    model: str = ""
    plan_id: str = ""
    source_evidence: list[dict] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unsupported_areas: list[str] = field(default_factory=list)
    requires_human_decisions: list[str] = field(default_factory=list)
    requires_human_approval: bool = True

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict of the provenance."""
        return {
            "generated_by": self.generated_by,
            "generation_mode": self.generation_mode,
            "model": self.model,
            "plan_id": self.plan_id,
            "source_evidence": self.source_evidence,
            "assumptions": self.assumptions,
            "unsupported_areas": self.unsupported_areas,
            "requires_human_decisions": self.requires_human_decisions,
            "requires_human_approval": self.requires_human_approval,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AssetProvenance":
        """Rebuild from a stored dict (tolerant of missing keys)."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ProposedAsset:
    """A single proposed blueprint file, with its lifecycle state."""

    asset_type: str
    filename: str  # relative path within the blueprint directory
    content: str
    state: AssetState = AssetState.PROPOSED
    provenance: Optional[AssetProvenance] = None
    validation_error: Optional[str] = None
    edit_history: list[str] = field(default_factory=list)
    confidence_note: str = ""

    # -- state machine -------------------------------------------------------

    def _transition(self, to_state: AssetState) -> None:
        """Move to ``to_state`` if the transition is valid, else PK-GEN-007."""
        if to_state not in _VALID_TRANSITIONS.get(self.state, set()):
            raise ProposalError(
                "PK-GEN-007",
                f"Invalid asset state transition: {self.state.value} → "
                f"{to_state.value} (asset: {self.filename})",
                {
                    "asset": self.filename,
                    "from": self.state.value,
                    "to": to_state.value,
                },
            )
        self.state = to_state

    def approve(self) -> None:
        """proposed → approved (human approves)."""
        self._transition(AssetState.APPROVED)

    def reject(self) -> None:
        """proposed → rejected (human rejects)."""
        self._transition(AssetState.REJECTED)

    def edit(self, new_content: str) -> None:
        """proposed → edited, recording the previous content."""
        self.edit_history.append(self.content)
        self._transition(AssetState.EDITED)
        self.content = new_content

    def repropose(self) -> None:
        """edited → proposed (re-proposed after an edit)."""
        self._transition(AssetState.PROPOSED)

    def mark_written(self) -> None:
        """approved → written. Called by BlueprintProposer.apply() only."""
        self._transition(AssetState.WRITTEN)

    def mark_validated(self) -> None:
        """written → validated (blueprint validate passed)."""
        self._transition(AssetState.VALIDATED)

    # -- serialization -------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict (for state.db storage)."""
        return {
            "asset_type": self.asset_type,
            "filename": self.filename,
            "content": self.content,
            "state": self.state.value,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "validation_error": self.validation_error,
            "edit_history": self.edit_history,
            "confidence_note": self.confidence_note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProposedAsset":
        """Rebuild from a stored dict."""
        prov = data.get("provenance")
        return cls(
            asset_type=data["asset_type"],
            filename=data["filename"],
            content=data["content"],
            state=AssetState(data.get("state", "proposed")),
            provenance=AssetProvenance.from_dict(prov) if prov else None,
            validation_error=data.get("validation_error"),
            edit_history=list(data.get("edit_history", [])),
            confidence_note=data.get("confidence_note", ""),
        )


@dataclass
class ProposalContext:
    """Read-only evidence handed to the provider to ground a proposal."""

    source_type: str
    destination_type: str
    tables: list[str]
    existing_blueprints: list[dict] = field(default_factory=list)
    source_config_fields: list[str] = field(default_factory=list)
    supported_tables: object = field(default_factory=list)  # list[str] | str
    blueprint_schema: dict = field(default_factory=dict)
    contract_examples: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict of the context."""
        return {
            "source_type": self.source_type,
            "destination_type": self.destination_type,
            "tables": self.tables,
            "existing_blueprints": self.existing_blueprints,
            "source_config_fields": self.source_config_fields,
            "supported_tables": self.supported_tables,
            "blueprint_schema": self.blueprint_schema,
            "contract_examples": self.contract_examples,
        }


@dataclass
class BlueprintProposal:
    """A complete proposed blueprint — a plan, not files (ADR-018)."""

    plan_id: str
    blueprint_name: str
    source_type: str
    destination_type: str
    tables: list[str]
    assets: list[ProposedAsset]
    confidence: float
    assumptions: list[str] = field(default_factory=list)
    unsupported_areas: list[str] = field(default_factory=list)
    requires_human_decisions: list[str] = field(default_factory=list)
    provider: str = ""
    generated_at: str = ""
    can_auto_apply: bool = False  # always False (ADR-018)
    applied: bool = False

    def approved_assets(self) -> list[ProposedAsset]:
        """Return only the assets a human has approved."""
        return [a for a in self.assets if a.state == AssetState.APPROVED]

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict (for state.db storage)."""
        return {
            "plan_id": self.plan_id,
            "blueprint_name": self.blueprint_name,
            "source_type": self.source_type,
            "destination_type": self.destination_type,
            "tables": self.tables,
            "assets": [a.to_dict() for a in self.assets],
            "confidence": self.confidence,
            "assumptions": self.assumptions,
            "unsupported_areas": self.unsupported_areas,
            "requires_human_decisions": self.requires_human_decisions,
            "provider": self.provider,
            "generated_at": self.generated_at,
            "can_auto_apply": self.can_auto_apply,
            "applied": self.applied,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BlueprintProposal":
        """Rebuild a proposal from a stored dict (for show / apply plan)."""
        return cls(
            plan_id=data["plan_id"],
            blueprint_name=data["blueprint_name"],
            source_type=data["source_type"],
            destination_type=data["destination_type"],
            tables=list(data.get("tables", [])),
            assets=[ProposedAsset.from_dict(a) for a in data.get("assets", [])],
            confidence=float(data.get("confidence", 0.0)),
            assumptions=list(data.get("assumptions", [])),
            unsupported_areas=list(data.get("unsupported_areas", [])),
            requires_human_decisions=list(data.get("requires_human_decisions", [])),
            provider=data.get("provider", ""),
            generated_at=data.get("generated_at", ""),
            can_auto_apply=False,
            applied=bool(data.get("applied", False)),
        )
