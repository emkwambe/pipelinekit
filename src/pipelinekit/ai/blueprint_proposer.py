"""The blueprint proposal orchestrator (SPEC-015, ADR-018).

Proposes. Does not write. The trust boundary of the proposal system:

    proposed → approved → written → validated

``propose()`` returns a ``BlueprintProposal`` and writes **nothing**. Only
``apply()`` writes, and only assets a human has APPROVED. ``can_auto_apply`` is
always False. The adapter capability registry is consulted *before* any AI call
so an unsupported connector fails fast with ``PK-GEN-006`` (ADR-008).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import jsonschema

from pipelinekit.ai.adapter_registry import AdapterCapabilityRegistry
from pipelinekit.ai.proposal_models import (
    AssetProvenance,
    BlueprintProposal,
    ProposalContext,
    ProposedAsset,
)
from pipelinekit.ai.provider import LLMProvider
from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import ProposalError
from pipelinekit.state import db

# repo_root/src/pipelinekit/ai/blueprint_proposer.py -> parents[3] == repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_BLUEPRINT_SCHEMA = _REPO_ROOT / "schemas" / "blueprint.schema.json"
_PROPOSAL_SCHEMA = _REPO_ROOT / "schemas" / "blueprint_proposal.schema.json"

# A top-level YAML "_provenance:" block (the key plus its indented body).
_YAML_PROVENANCE_RE = re.compile(r"(?m)^_provenance:\n(?:[ \t]+.*\n?)*")


class BlueprintProposer:
    """Orchestrates context → AI proposal → human approval → apply (write)."""

    def __init__(self, config: PipelineConfig, provider: LLMProvider) -> None:
        self.config = config
        self.provider = provider
        self.registry_reader = BlueprintRegistry()
        self.adapter_registry = AdapterCapabilityRegistry()

    # -- propose (never writes) ---------------------------------------------

    def propose(
        self,
        source_type: str,
        destination_type: str,
        tables: list[str],
        cwd: Path | None = None,
    ) -> BlueprintProposal:
        """Produce a ``BlueprintProposal``. Writes no blueprint files.

        Raises:
            ProposalError: ``PK-GEN-006`` if the source or destination is not in
                the adapter capability registry (checked *before* any AI call),
                ``PK-GEN-002`` if the assembled proposal fails schema validation.
        """
        # 1. Deterministic capability gate — never call AI for what we can't run.
        if not self.adapter_registry.is_source_supported(source_type):
            raise ProposalError(
                "PK-GEN-006",
                f"Source type '{source_type}' not supported. Supported: "
                f"{self.adapter_registry.supported_source_names()}",
                {"source": source_type},
            )
        if not self.adapter_registry.is_destination_supported(destination_type):
            raise ProposalError(
                "PK-GEN-006",
                f"Destination type '{destination_type}' not supported. Supported: "
                f"{self.adapter_registry.supported_destination_names()}",
                {"destination": destination_type},
            )

        # 2. Build read-only evidence and 3. call the provider.
        context = self._build_context(source_type, destination_type, tables)
        proposal = self.provider.propose_blueprint(context)

        # 4. Stamp identity the provider does not own.
        now = datetime.now(timezone.utc)
        proposal.plan_id = (
            f"plan-{source_type}-{destination_type}-{now.strftime('%Y%m%d-%H%M%S')}"
        )
        proposal.generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 5. Attach provenance to every asset (informs the human; stripped on write).
        for asset in proposal.assets:
            self._attach_provenance(asset, proposal)

        # 6. Validate the blueprint.json asset; record (do not raise) so the human
        #    can see and edit it during review.
        for asset in proposal.assets:
            if asset.asset_type == "blueprint_json" or asset.filename.endswith(
                "blueprint.json"
            ):
                asset.validation_error = self._validate_blueprint_json(asset.content)

        # 7. Phase invariant: never auto-apply (ADR-018).
        proposal.can_auto_apply = False

        # 8. Validate the assembled plan and 9. persist it (audit record).
        self._validate_proposal(proposal)
        db.insert_blueprint_proposal(proposal.to_dict(), cwd=cwd)
        return proposal

    # -- apply (writes only approved assets) --------------------------------

    def apply(
        self,
        proposal: BlueprintProposal,
        cwd: Path | None = None,
    ) -> list[str]:
        """Write only APPROVED assets to ``blueprints/<name>/``.

        Strips provenance from each asset before writing and transitions it
        ``approved → written``. Never writes a non-approved asset.

        Raises:
            ProposalError: ``PK-GEN-003`` if no assets are approved,
                ``PK-GEN-004`` if the blueprint directory already exists.
        """
        approved = proposal.approved_assets()
        if not approved:
            raise ProposalError(
                "PK-GEN-003",
                f"No approved assets to apply for plan {proposal.plan_id}.",
                {"plan_id": proposal.plan_id},
            )

        base = (cwd if cwd is not None else Path.cwd()) / "blueprints"
        blueprint_dir = base / proposal.blueprint_name
        if blueprint_dir.exists():
            raise ProposalError(
                "PK-GEN-004",
                f"Blueprint directory already exists: {blueprint_dir}",
                {"path": str(blueprint_dir)},
            )

        written: list[str] = []
        for asset in approved:
            target = blueprint_dir / asset.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self._strip_provenance(asset.content), encoding="utf-8")
            asset.mark_written()  # approved → written
            written.append(str(target))

        proposal.applied = True
        db.mark_proposal_applied(
            proposal.plan_id, [a.to_dict() for a in proposal.assets], cwd=cwd
        )
        return written

    # -- helpers -------------------------------------------------------------

    def _build_context(
        self, source_type: str, destination_type: str, tables: list[str]
    ) -> ProposalContext:
        """Assemble read-only evidence for the provider."""
        existing = [bp.model_dump() for bp in self.registry_reader.list()]
        source_info = self.adapter_registry.get_source_info(source_type)
        return ProposalContext(
            source_type=source_type,
            destination_type=destination_type,
            tables=tables,
            existing_blueprints=existing,
            source_config_fields=list(source_info.get("credential_fields", [])),
            supported_tables=self.adapter_registry.get_supported_tables(source_type),
            blueprint_schema=self._load_json(_BLUEPRINT_SCHEMA),
            contract_examples=self._read_contract_examples(),
        )

    def _attach_provenance(
        self, asset: ProposedAsset, proposal: BlueprintProposal
    ) -> None:
        """Attach an ``AssetProvenance`` to a proposed asset."""
        evidence = [
            {"type": "blueprint_pattern", "name": bp.name, "version": bp.version}
            for bp in self.registry_reader.list()
        ]
        evidence.append({"type": "schema", "name": "blueprint.schema.json"})
        asset.provenance = AssetProvenance(
            model=proposal.provider,
            plan_id=proposal.plan_id,
            source_evidence=evidence,
            assumptions=list(proposal.assumptions),
            unsupported_areas=list(proposal.unsupported_areas),
            requires_human_decisions=list(proposal.requires_human_decisions),
            requires_human_approval=True,
        )

    def _strip_provenance(self, content: str) -> str:
        """Remove any embedded provenance block before writing the file.

        Provenance lives in the proposal (and review display), never in the
        shipped blueprint (ADR-018). Handles both a JSON ``_provenance`` key and
        a top-level YAML ``_provenance:`` block.
        """
        stripped = content.strip()
        if stripped.startswith("{"):
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "_provenance" in data:
                    data.pop("_provenance", None)
                    return json.dumps(data, indent=2) + "\n"
            except ValueError:
                pass
        return _YAML_PROVENANCE_RE.sub("", content)

    def _validate_blueprint_json(self, content: str) -> Optional[str]:
        """Return a validation error message for blueprint.json, or None."""
        try:
            instance = json.loads(content)
        except ValueError as exc:
            return f"blueprint.json is not valid JSON: {exc}"
        try:
            jsonschema.validate(
                instance=instance, schema=self._load_json(_BLUEPRINT_SCHEMA)
            )
        except jsonschema.ValidationError as exc:
            return str(exc.message)
        return None

    def _validate_proposal(self, proposal: BlueprintProposal) -> None:
        """Validate the assembled plan against blueprint_proposal.schema.json."""
        try:
            jsonschema.validate(
                instance=proposal.to_dict(),
                schema=self._load_json(_PROPOSAL_SCHEMA),
            )
        except jsonschema.ValidationError as exc:
            raise ProposalError(
                "PK-GEN-002",
                f"Proposed plan failed schema validation: {exc.message}",
                {"detail": exc.message},
            ) from exc

    @staticmethod
    def _load_json(path: Path) -> dict:
        """Load a JSON file, returning ``{}`` if it is missing or not an object."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _read_contract_examples(self) -> list[dict]:
        """Read existing blueprint contract files as format examples (best-effort)."""
        examples: list[dict] = []
        blueprints_dir = _REPO_ROOT / "blueprints"
        if not blueprints_dir.is_dir():
            return examples
        for contract in sorted(blueprints_dir.glob("*/contracts/*.yaml")):
            examples.append(
                {"name": contract.name, "content": contract.read_text(encoding="utf-8")}
            )
        return examples
