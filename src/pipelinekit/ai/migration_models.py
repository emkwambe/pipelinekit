"""Data models for Migration Intelligence (SPEC-017, ADR-020).

Migration Intelligence reads an existing pipeline config (Airbyte, Fivetran,
custom Python, or an existing ``pipelinekit.yaml``) and proposes a PipelineKit
equivalent. Like Blueprint Proposal (ADR-018) it is a *proposal* system: the
``MigrationProposal`` is a plan, not files. ``can_auto_apply`` is always False —
AI reads, AI proposes, a human approves, ``apply()`` writes
``pipelinekit.proposed.yaml`` (never ``pipelinekit.yaml``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MappingStatus(Enum):
    """How cleanly one source field maps onto PipelineKit (SPEC-017)."""

    CLEAN = "clean"  # maps directly to PipelineKit
    PARTIAL = "partial"  # maps with minor adjustments
    MANUAL = "manual"  # requires significant human work
    UNSUPPORTED = "unsupported"  # no PipelineKit equivalent


@dataclass
class MappingResult:
    """One field's migration mapping from the source tool to PipelineKit."""

    field: str
    source_value: str
    pipelinekit_equivalent: Optional[str]
    status: MappingStatus
    note: str = ""

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict of the mapping."""
        return {
            "field": self.field,
            "source_value": self.source_value,
            "pipelinekit_equivalent": self.pipelinekit_equivalent,
            "status": self.status.value,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MappingResult":
        """Rebuild a mapping from a stored dict (tolerant of a string status)."""
        return cls(
            field=str(data.get("field", "")),
            source_value=str(data.get("source_value", "")),
            pipelinekit_equivalent=data.get("pipelinekit_equivalent"),
            status=MappingStatus(data.get("status", "manual")),
            note=str(data.get("note", "")),
        )


@dataclass
class MigrationGap:
    """An explicit thing the human must resolve before the migration is usable."""

    gap_type: str  # "credential" | "table" | "transform" | "schedule" | "feature"
    description: str
    required_action: str
    blocking: bool = True  # blocks deployment if not resolved

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict of the gap."""
        return {
            "gap_type": self.gap_type,
            "description": self.description,
            "required_action": self.required_action,
            "blocking": self.blocking,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MigrationGap":
        """Rebuild a gap from a stored dict."""
        return cls(
            gap_type=str(data.get("gap_type", "feature")),
            description=str(data.get("description", "")),
            required_action=str(data.get("required_action", "")),
            blocking=bool(data.get("blocking", True)),
        )


@dataclass
class MigrationProposal:
    """A proposed migration — a plan, not files (ADR-020).

    ``blocking_gaps`` is always recomputed from ``gaps`` in ``__post_init__`` so
    the count can never drift from the gap list. ``can_auto_apply`` defaults
    False and is re-forced False by the analyzer (ADR-020 trust boundary).
    """

    source_tool: str  # "airbyte" | "fivetran" | "python" | "pipelinekit"
    source_file: str
    draft_yaml: str  # proposed pipelinekit.yaml content
    blueprint_recommendation: Optional[str]  # name of matching blueprint
    mappings: list[MappingResult]
    gaps: list[MigrationGap]
    confidence: float  # 0.0–1.0
    blocking_gaps: int = 0  # count of gaps that block deployment (recomputed)
    can_auto_apply: bool = False  # always False
    assumptions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Derive ``blocking_gaps`` from ``gaps`` — the count cannot drift."""
        self.blocking_gaps = sum(1 for g in self.gaps if g.blocking)

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict (for display / persistence)."""
        return {
            "source_tool": self.source_tool,
            "source_file": self.source_file,
            "draft_yaml": self.draft_yaml,
            "blueprint_recommendation": self.blueprint_recommendation,
            "mappings": [m.to_dict() for m in self.mappings],
            "gaps": [g.to_dict() for g in self.gaps],
            "confidence": self.confidence,
            "blocking_gaps": self.blocking_gaps,
            "can_auto_apply": self.can_auto_apply,
            "assumptions": self.assumptions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MigrationProposal":
        """Rebuild a proposal from a stored dict (can_auto_apply forced False)."""
        return cls(
            source_tool=str(data.get("source_tool", "")),
            source_file=str(data.get("source_file", "")),
            draft_yaml=str(data.get("draft_yaml", "")),
            blueprint_recommendation=data.get("blueprint_recommendation"),
            mappings=[MappingResult.from_dict(m) for m in data.get("mappings", [])],
            gaps=[MigrationGap.from_dict(g) for g in data.get("gaps", [])],
            confidence=float(data.get("confidence", 0.0)),
            can_auto_apply=False,
            assumptions=list(data.get("assumptions", [])),
        )
