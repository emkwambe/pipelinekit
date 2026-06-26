# Glossary

Precise definitions of PipelineKit terms. Where a term maps to a concrete type, the type name is given.

---

**Adapter** — A provider-specific implementation behind a stable PipelineKit interface (e.g. a dlt ingestion adapter, a dbt transformation adapter, an `LLMProvider`). Callers depend on the interface, never the concrete tool.

**AI Boundary** — The non-negotiable rule that AI may observe, diagnose, recommend, summarize, classify, and propose, but never execute or modify production. Enforced in code: `can_auto_fix` and `can_auto_apply` are always `false`.

**AssetState** — The lifecycle state of a `ProposedAsset` in the blueprint proposal system: `proposed`, `approved`, `rejected`, `edited`, `written`, `validated`. Transitions are code-enforced; an invalid transition raises `PK-GEN-007`.

**Blueprint** — A complete, verifiable pipeline package under `blueprints/<name>/`, providing eight required assets (manifest, ingestion, transform, contracts, quality, alerts, readme, runbook). A reference implementation, not a blank template.

**Blueprint Proposal** — A complete blueprint proposed by AI from a short specification, returned as a plan (not files). A human reviews it and only `apply()` writes the approved assets. Modeled by `BlueprintProposal`. (Supersedes the older term *Generation Plan*.)

**Blueprint Registry** — The catalog of blueprints. Locally, `BlueprintRegistry` scans `blueprints/`. Remotely, `RemoteRegistry` fetches a versioned catalog and installs blueprints after validation. The public remote registry is not yet deployed.

**Contract** — A data contract: a YAML definition of what "correct" means for a table (required columns, uniqueness, not-null, freshness, row-count range). Lives under `contracts/`.

**ContractValidator** — The component that loads and validates data contracts. Structural validation runs in `pipelinekit validate --contracts`; data-level enforcement runs during `pipelinekit run`.

**Data Layer** — The layer of ingestion, transformation, and quality adapters (dlt, dbt, Soda). It moves and shapes data behind adapter interfaces.

**DestinationConfig** — Not a separate type: destinations are described by the same connection model as sources (`SourceConfig`). The `ingestion.destination` block sets `type` plus the fields for that backend (e.g. `account`, `warehouse`, `database` for Snowflake).

**Diagnosis** — An evidence-based explanation of a pipeline failure (a `DiagnosticResult`): a finding type, confidence, explanation, the evidence used, and recommended actions. Never a fix.

**Evidence Package** — The structured input handed to an AI provider for diagnosis (`EvidencePackage`): the run record, contract results, and related state. AI reasons only over this evidence and never invents facts.

**EvidenceCollector** — The component that assembles an `EvidencePackage` from local state for a given run, and resolves the most recent run when none is specified.

**Generation Plan** — *Deprecated term.* Use **Blueprint Proposal**. The proposal system replaced the earlier "generation" framing; the architecture is propose → approve → write, not generate.

**Intelligence Layer** — The AI layer: the `LLMProvider` contract plus AI diagnostics, blueprint proposal, and migration intelligence. It observes and proposes; it never acts.

**LLMProvider** — The stable interface every AI provider implements (`diagnose`, `summarize`, `recommend`, `architect`, `propose_blueprint`, `analyze_migration`). The engines call this interface only and never know which provider is active. Implementations: `anthropic`, `openai`, `ollama`, `deepseek`, `mistral`.

**MappingStatus** — In a migration proposal, how cleanly a source field maps onto PipelineKit: `clean`, `partial`, `manual`, or `unsupported`.

**MigrationGap** — An explicit item the human must resolve to make a migrated pipeline work (a credential, table set, transform, schedule, or feature). Each gap is `blocking` or non-blocking.

**MigrationProposal** — The result of `pipelinekit migrate analyze`: a draft `pipelinekit.yaml`, the field mappings, the gaps, a blueprint recommendation, and a confidence score. `can_auto_apply` is always `false`.

**Pipeline** — A configured data flow defined by `pipelinekit.yaml`: ingestion → transformation → quality, with contracts.

**PipelineRunner** — The runtime entry point that executes a pipeline. The CLI calls it and renders the result; it never reaches into adapters directly.

**PipelineResult** — The structured outcome of a run: per-step status, duration, and rows processed, plus an overall status. Returned by `PipelineRunner`.

**ProposedAsset** — A single proposed blueprint file with its lifecycle state and provenance, inside a `BlueprintProposal`. Only `apply()` writes it, and only when `approved`.

**SourceConfig** — The connection model for an ingestion source *or* destination (the same model serves both). Only `type` is required; the remaining fields depend on the connector. Credentials arrive via `${VAR}` interpolation and are never stored at rest.

**Specification (SPEC)** — An implementation-ready document defining one buildable capability. Code must match its SPEC; drift is a defect.

**State** — Metadata about pipeline execution, validation, diagnosis, health, proposals, and installs — never pipeline data. Stored in local SQLite at `.pipelinekit/state.db`.

**Trust Layer** — The layer that makes analytics trustworthy: data contracts and blueprints. It is where "the pipeline ran" becomes "the data is correct."

**TTTD (Time-to-Trusted-Data)** — PipelineKit's guiding metric: the time from requirements to analytics you can trust. Every feature must improve at least one TTTD dimension (design speed, validation speed, deployment safety, diagnostic speed, pipeline confidence).

**Verified Blueprint** — A blueprint that has been run end-to-end with the result recorded in its `docs/runbook.md`. Local verification runs against a local source and DuckDB; production verification runs against the real warehouse and is the bar for `verified: true` in the registry.
