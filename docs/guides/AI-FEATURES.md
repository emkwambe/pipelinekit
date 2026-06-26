# AI Features in PipelineKit

PipelineKit's AI layer diagnoses failures, proposes blueprints, reasons about architecture, and analyzes migrations. Every capability is grounded in structured evidence and bounded by one rule: **AI observes, diagnoses, and proposes — it never executes and never auto-applies.**

---

## The AI Boundary (non-negotiable)

AI in PipelineKit may inspect, diagnose, recommend, summarize, classify, and generate proposals. It may not silently deploy, delete, migrate, or modify production. Every production change requires explicit human approval.

This is enforced in code, not just policy:

- `can_auto_fix` (diagnostics) is always `false`.
- `can_auto_apply` (architecture, blueprint proposal, migration) is always `false`.
- Recommended actions and proposals are displayed for review; PipelineKit records an approval decision but never runs the action.

---

## Supported Providers

PipelineKit depends on the `LLMProvider` interface, not on any single vendor. Five providers are implemented; you bring your own key (BYOK).

| Provider | Region / residency | Key env var | Default model | Use case |
|---|---|---|---|---|
| `anthropic` | US | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` | Default; best reasoning |
| `openai` | US | `OPENAI_API_KEY` | `gpt-4o` | Alternative US provider |
| `ollama` | Local | `OLLAMA_HOST` (default `http://localhost:11434`; no key) | `llama3` | Air-gapped / privacy-first |
| `deepseek` | China | `DEEPSEEK_API_KEY` | `deepseek-chat` | Cost-sensitive, Asian markets |
| `mistral` | EU (France) | `MISTRAL_API_KEY` | `mistral-large-latest` | GDPR data residency |

A missing key or unreachable provider raises `PK-AI-001`. Ollama needs no key — it talks to a local server.

---

## Setting Your Provider

The default provider comes from `diagnostics.provider` in `pipelinekit.yaml`. Any AI command accepts `--provider` / `-p` to override it for that invocation:

```bash
pipelinekit diagnose --provider mistral
pipelinekit generate blueprint -s postgres -d snowflake -t orders --plan --provider deepseek
pipelinekit architect analyze --provider anthropic
pipelinekit migrate analyze connector.json --provider openai
```

AI features require `diagnostics.enabled: true` in `pipelinekit.yaml`. When disabled, the AI commands print a notice and exit cleanly.

---

## AI Diagnostics

```bash
pipelinekit diagnose                 # diagnose the most recent run
pipelinekit diagnose <run-id>        # diagnose a specific run
pipelinekit diagnose --approve       # review recommended actions interactively
```

- **What it reads** — an evidence package assembled by the `EvidenceCollector`: the run record, contract results, and related state for the run being diagnosed. It uses only what is in local state; it never invents evidence.
- **What it returns** — a `DiagnosticResult` with a `finding_type`, a `confidence` score, an `explanation`, the `evidence` used, and a list of `recommended_actions` (each with a risk level and reversibility).
- **How to act** — actions are shown for you to perform. With `--approve`, you review each action and PipelineKit records which you approved — but it never executes them. An inconclusive diagnosis says so rather than guessing.

---

## Architecture Intelligence

```bash
pipelinekit architect analyze "Should we move from dbt to SQLMesh?"
pipelinekit architect analyze --type cost_optimization
pipelinekit architect check-adrs "Add a Kafka streaming source"
pipelinekit architect compare dbt sqlmesh
```

Reasoning types: `tool_selection`, `cost_optimization`, `adr_compliance`, `stack_evolution`, `blueprint_selection` (default `tool_selection`).

- **`analyze`** — reason about your stack; pass a free-text question and/or `--type`. Add `--approve` to review the recommendation and record a decision.
- **`check-adrs`** — check whether a proposed change complies with your ADRs (runs `adr_compliance`).
- **`compare`** — compare two tools for your specific data profile.

The output gives a recommendation, rationale, tradeoffs, ADR-compliance notes, and an explanation. It is advisory only — PipelineKit never applies architecture changes. If the project has too little run history to reason about (`PK-ARCH-004`), the command says so and exits cleanly rather than failing.

---

## AI Blueprint Proposal

PipelineKit proposes a complete blueprint from a short spec, then a human reviews and applies it. Full workflow in the [Blueprint Guide](BLUEPRINT-GUIDE.md).

- **Confidence scores** — an overall score plus a per-asset note; a low overall score prints a warning to review every asset carefully.
- **Provenance metadata** — each asset carries what evidence it was based on, the assumptions made, and the decisions you must make. View it with the `[x]explain` option during review (it is stripped from the file before writing).
- **The `--interactive` review loop** — accept / reject / edit / explain / accept-remaining / quit, asset by asset. Only approved assets are written, and only by `apply()`.

---

## Migration Intelligence

PipelineKit reads an existing Airbyte/Fivetran/Python config and proposes a PipelineKit equivalent. Full workflow in the [Migration Guide](MIGRATION-GUIDE.md).

- **How the analyzer builds evidence** — it parses the source config deterministically (the Python parser uses `ast.parse()` only, never executing the file), then hands the parsed config plus available blueprints and adapter capabilities to the provider.
- **Why confidence may be low** — custom Python parsing is best-effort: a connection string infers the source type, a `destination=` keyword infers the destination, and list literals infer tables. Ambiguous files yield low confidence by design.
- **How to improve confidence** — provide richer source configs (an Airbyte/Fivetran export carries far more structure than a Python script), and ensure the source/destination types are ones PipelineKit supports.

---

## Trust Model

- **Why AI never auto-applies.** Trusted analytics require a human in the loop for any production change. The boundary is structural: proposals and diagnoses are data, not actions, and the only code paths that write are explicit `apply()` calls a human triggers.
- **The evidence architecture.** AI is always given structured evidence (an `EvidencePackage`, a parsed config, or architecture context) — never raw, unbounded input. Diagnoses cite the evidence they used.
- **Schema validation as a trust boundary.** AI output is parsed and validated before it is trusted. Architecture and diagnostic responses must satisfy their models, and proposals are checked against their schemas.
- **What `PK-AI-001` and `PK-AI-002` mean.** `PK-AI-001` — the provider is unavailable (missing key or unreachable). `PK-AI-002` — the provider returned output that failed schema validation. Both are surfaced as structured errors, never as a crash.
