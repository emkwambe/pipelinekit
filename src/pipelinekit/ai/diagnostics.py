"""The diagnostics engine — the trust boundary between evidence and AI output.

Pipeline: collect evidence (read-only) → provider.diagnose → schema validation →
threshold check → force ``can_auto_fix=False`` → persist → return. No invalid
output ever reaches the CLI, and no recommended action is ever executed
(ADR-007, ADR-014, Smell 13).

Note (Specification Drift, flagged): SPEC-005 sources ``confidence_threshold``
from ``pipelinekit.yaml``, but ``config/schema.py`` is read-only this phase, so
the threshold is a module default here. The Command Center decides whether to
add the config field and update the SPEC.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from pipelinekit.ai.evidence import EvidenceCollector
from pipelinekit.ai.models import DiagnosticResult
from pipelinekit.ai.provider import LLMProvider
from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import LLMError
from pipelinekit.state import db

DEFAULT_CONFIDENCE_THRESHOLD = 0.7

# repo_root/src/pipelinekit/ai/diagnostics.py -> parents[3] == repo root
_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "schemas" / "diagnostic.schema.json"
)


class DiagnosticsEngine:
    """Coordinates evidence → AI diagnosis → validation → storage."""

    def __init__(self, config: PipelineConfig, provider: LLMProvider) -> None:
        self.config = config
        self.provider = provider
        self.collector = EvidenceCollector()
        self.threshold = DEFAULT_CONFIDENCE_THRESHOLD

    def diagnose(self, run_id: str, cwd: Path | None = None) -> DiagnosticResult:
        """Run the full diagnostic cycle for ``run_id``.

        Never executes recommendations. Always persists the result.
        """
        evidence = self.collector.collect(run_id, cwd=cwd)
        evidence.config_snapshot = self.config.model_dump()

        result = self.provider.diagnose(evidence)

        # Trust boundary: validate before anything else trusts the output.
        self._validate_against_schema(result)

        # Phase 4 invariant: AI never auto-fixes (ADR-007, Smell 13).
        result.can_auto_fix = False

        # Honest confidence: low-confidence results are shown as inconclusive,
        # never suppressed.
        if result.confidence < self.threshold and result.status == "diagnosed":
            result.status = "inconclusive"

        # Carry run context for rendering and storage.
        result.run_id = result.run_id or run_id
        result.pipeline_name = result.pipeline_name or evidence.pipeline_name

        provider_name = getattr(self.provider, "name", "unknown")
        db.insert_diagnostic_result(
            run_id, result.model_dump(mode="json"), provider_name, cwd=cwd
        )
        return result

    def _validate_against_schema(self, result: DiagnosticResult) -> None:
        """Validate the result against ``diagnostic.schema.json``.

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
