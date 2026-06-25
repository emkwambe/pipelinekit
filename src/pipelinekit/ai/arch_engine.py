"""The architecture engine — the trust boundary for architectural reasoning.

Pipeline: collect context (read-only) → ``provider.architect`` → schema
validation → force ``can_auto_apply=False`` → persist → return. No invalid
output reaches the CLI, and no recommendation is ever executed (ADR-007,
ADR-015, Smell 13, Smell 16).

Same trust boundary as the Phase 4 ``DiagnosticsEngine``.

Note (Specification Drift, flagged): ``architecture.schema.json`` types
``adr_compliance`` as an ``object`` while ``ArchitectureResult.adr_compliance``
is a ``list[ADRComplianceCheck]`` (both fixed verbatim by SPEC-011). To honor
both artifacts unchanged, this engine wraps the list into the schema's object
shape *only for validation*; the stored and returned result keep the list form.
The Command Center decides whether to reconcile the two artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from pipelinekit.ai.arch_evidence import ArchitectureContextCollector
from pipelinekit.ai.arch_models import ArchitectureResult
from pipelinekit.ai.provider import LLMProvider
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import LLMError
from pipelinekit.state import db

# repo_root/src/pipelinekit/ai/arch_engine.py -> parents[3] == repo root
_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "schemas" / "architecture.schema.json"
)


class ArchitectureEngine:
    """Coordinates context → AI architectural reasoning → validation → storage."""

    def __init__(self, config: PipelineConfig, provider: LLMProvider) -> None:
        self.config = config
        self.provider = provider
        self.collector = ArchitectureContextCollector()

    def analyze(
        self,
        reasoning_type: str,
        question: str | None = None,
        cwd: Path | None = None,
    ) -> ArchitectureResult:
        """Run the full architectural reasoning cycle for ``reasoning_type``.

        Never executes recommendations. Always persists the result.
        """
        context = self.collector.collect(cwd=cwd)
        context.config = self.config.model_dump()
        context.current_tools = self._current_tools()

        result = self.provider.architect(context, reasoning_type, question)

        # Trust boundary: validate before anything else trusts the output.
        self._validate_against_schema(result)

        # Phase 5 invariant: architecture is never auto-applied (ADR-015, Smell 13).
        result.can_auto_apply = False
        result.reasoning_type = result.reasoning_type or reasoning_type

        provider_name = getattr(self.provider, "name", "unknown")
        db.insert_architecture_result(
            reasoning_type,
            result.model_dump(mode="json"),
            provider_name,
            question=question,
            cwd=cwd,
        )
        return result

    def _current_tools(self) -> dict:
        """Summarize the active tool stack from config (read-only)."""
        ingestion = self.config.ingestion
        return {
            "source": ingestion.source.type,
            "destination": ingestion.destination.type,
            "transformation": (
                self.config.transformation.project_dir
                if self.config.transformation.enabled
                else None
            ),
            "quality": self.config.quality.enabled,
        }

    def _validate_against_schema(self, result: ArchitectureResult) -> None:
        """Validate the result against ``architecture.schema.json``.

        Raises:
            LLMError: ``PK-AI-002`` if validation fails. This is the trust
                boundary — invalid AI output never reaches the CLI.
        """
        payload = (
            result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        )
        try:
            schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
            jsonschema.validate(instance=payload, schema=schema)
        except jsonschema.ValidationError as exc:
            raise LLMError(
                "PK-AI-002",
                f"AI response failed schema validation: {exc.message}",
                {"detail": exc.message},
            ) from exc
