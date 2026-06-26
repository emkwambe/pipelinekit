"""The migration analyzer (SPEC-017, ADR-020).

Reads an existing pipeline config, analyses the migration path, and proposes a
PipelineKit equivalent. Same trust model as ``BlueprintProposer`` (ADR-018):

    AI reads → AI proposes → human approves → apply() writes

``analyze()`` writes **nothing**. ``apply()`` writes the draft to
``pipelinekit.proposed.yaml`` (never ``pipelinekit.yaml``) and refuses to write
while blocking gaps remain unless ``force`` is set. ``can_auto_apply`` is always
False.
"""

from __future__ import annotations

from pathlib import Path

from pipelinekit.ai.adapter_registry import AdapterCapabilityRegistry
from pipelinekit.ai.config_parsers import MigrationConfigParser
from pipelinekit.ai.migration_models import MigrationProposal
from pipelinekit.ai.provider import LLMProvider
from pipelinekit.blueprints.registry import BlueprintRegistry
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import MigrationError

_PROPOSED_FILENAME = "pipelinekit.proposed.yaml"


class MigrationAnalyzer:
    """Read existing config → analyse → propose PipelineKit equivalent."""

    def __init__(self, config: PipelineConfig, provider: LLMProvider) -> None:
        self.config = config
        self.provider = provider
        self.parser = MigrationConfigParser()
        self.registry = BlueprintRegistry()
        self.adapters = AdapterCapabilityRegistry()

    # -- analyze (never writes) ---------------------------------------------

    def analyze(
        self,
        config_path: Path,
        cwd: Path | None = None,
    ) -> MigrationProposal:
        """Produce a ``MigrationProposal``. Writes no files.

        Raises:
            MigrationError: ``PK-MIGRATE-001`` if the config file is missing,
                ``PK-MIGRATE-002`` if the format is unrecognised,
                ``PK-MIGRATE-004`` if the AI analysis returns invalid output,
                ``PK-MIGRATE-005`` if a ``.py`` file fails to parse.
        """
        # 1. Deterministic parse of the existing config (never executes it).
        tool, parsed = self.parser.parse(config_path)

        # 2. Build read-only context (parsed config + capabilities + blueprints).
        context = self._build_context(tool, parsed)

        # 3. Provider analyses the migration path.
        proposal = self.provider.analyze_migration(context)

        # 4. Stamp identity the provider does not own.
        proposal.source_tool = tool
        proposal.source_file = str(config_path)

        # 5. Trust invariant: never auto-apply (ADR-020).
        proposal.can_auto_apply = False
        return proposal

    # -- apply (writes the draft only after review) -------------------------

    def apply(
        self,
        proposal: MigrationProposal,
        cwd: Path | None = None,
        force: bool = False,
    ) -> str:
        """Write the draft ``pipelinekit.proposed.yaml`` after human review.

        Returns the path written.

        Raises:
            MigrationError: ``PK-MIGRATE-003`` if blocking gaps exist and
                ``force`` is not set.
        """
        if proposal.blocking_gaps > 0 and not force:
            raise MigrationError(
                "PK-MIGRATE-003",
                f"{proposal.blocking_gaps} blocking gap(s) must be resolved "
                "before applying. Re-run with --force to write anyway.",
                {"blocking_gaps": proposal.blocking_gaps},
            )
        target = (cwd if cwd is not None else Path.cwd()) / _PROPOSED_FILENAME
        target.write_text(proposal.draft_yaml, encoding="utf-8")
        return str(target)

    # -- helpers -------------------------------------------------------------

    def _build_context(self, tool: str, parsed: dict) -> dict:
        """Assemble read-only evidence for the provider."""
        return {
            "source_tool": tool,
            "parsed_config": parsed,
            "available_blueprints": [
                {
                    "name": bp.name,
                    "source": getattr(bp.source, "type", ""),
                    "destination": getattr(bp.destination, "type", ""),
                }
                for bp in self.registry.list()
            ],
            "supported_sources": self.adapters.supported_source_names(),
            "supported_destinations": self.adapters.supported_destination_names(),
        }
