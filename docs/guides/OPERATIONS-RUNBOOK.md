# Operations Runbook

What to do when a PipelineKit pipeline misbehaves. Aimed at on-call engineers and data platform teams.

---

## First Response

```bash
pipelinekit health      # is the installation and project sound?
pipelinekit status      # what were the recent runs and how did they end?
pipelinekit diagnose    # AI root-cause analysis of the most recent run
```

`health` checks the environment (deps, security, blueprints, specs, tests). `status` shows the last five runs with their status and error codes. `diagnose` reads the run's evidence and explains the likely root cause with a confidence score — it does not fix anything.

---

## Error Code Quick Reference

Every failure carries a `PK-[AREA]-[NUMBER]` code. By area:

| Area | Meaning |
|---|---|
| `PK-CONFIG-*` | Configuration problems (`pipelinekit.yaml`, credentials) |
| `PK-STATE-*` | Local state store (`.pipelinekit/state.db`) |
| `PK-RUNTIME-*` | Pipeline execution failures |
| `PK-ADAPTER-*` | Ingestion / transformation / quality adapter failures |
| `PK-CONTRACT-*` | Data contract violations |
| `PK-BLUEPRINT-*` | Blueprint structure/manifest problems |
| `PK-AI-*` | AI provider issues |
| `PK-DIAG-*` | Diagnostics engine issues |
| `PK-ARCH-*` | Architecture reasoning issues |
| `PK-HEALTH-*` | Health-check tooling issues |
| `PK-GEN-*` | Blueprint proposal issues |
| `PK-REGISTRY-*` | Registry connectivity / install |
| `PK-MIGRATE-*` | Migration analysis issues |
| `PK-NOTIFY-*` | Notification delivery |

The full table is in `docs/reference/Error-Codes.md` and the [CLI Reference](CLI-REFERENCE.md).

---

## Common Failures and Fixes

### `PK-ADAPTER-001` — Source unreachable
The ingestion adapter could not connect. Check that the source host/credentials are correct and reachable, that the relevant `${VAR}` environment variables are set, and that any required network/VPN access is in place. Confirm with `pipelinekit run --dry-run`, which validates adapter reachability without moving data.

### `PK-ADAPTER-002` — dbt build failed
The transformation step failed. Inspect the dbt run output and the blueprint's `transform/logs/`. Common causes: a model references a missing source/column, or the destination schema differs from what the models expect. Fix the model or the source, then re-run.

### Recovery model in v0.1.0

PipelineKit does not yet support partial reruns, step-level retries, or automatic retry logic. When a run fails, the recovery path is:

1. Inspect the failing step using `pipelinekit status` and the `PK-*` error code.
2. Apply the fix (source connectivity, dbt model, contract definition, etc.).
3. Re-run the entire pipeline with `pipelinekit run`.

This is consistent with the current full-refresh ingestion model (`write_disposition="replace"`). Future releases may add incremental loads and step-level retries.

### `PK-AI-001` — Missing API key
The configured AI provider has no key (or is unreachable). Set the provider's environment variable — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, or `MISTRAL_API_KEY` — or use `ollama` (local, no key). You can override per-invocation with `--provider`.

### `PK-CONTRACT-008` — Contract file invalid
A contract YAML is malformed or fails its schema. Run `pipelinekit validate --contracts` to see which file and why, then fix the definition (see the [Configuration Reference](CONFIGURATION-REFERENCE.md) contract format).

### `PK-REGISTRY-001` — Registry unreachable
The remote registry at `registry.pipelinekit.dev` could not be reached and no cached catalog is available. Check network connectivity, or use the three catalog blueprints already present in the repo under `blueprints/`.

---

## Health Monitoring

A simple cadence keeps a project healthy:

```bash
# Monthly — dependency freshness and known vulnerabilities
pipelinekit health deps
pipelinekit health security

# After deploys — blueprint structure still valid
pipelinekit health blueprints

# Before demos / releases — everything
pipelinekit health           # or: pipelinekit health --strict  (exit 1 on any warning)
```

`health` is non-blocking by default (always exits 0) so it is safe to run anywhere. Use `--strict` in CI when you want a warning to fail the build. Each full run is recorded in state.

---

## Pipeline Semantics

### v0.1.0 ingestion behavior

`pipelinekit run` currently performs a **full refresh** on every execution: the ingestion adapter uses `write_disposition="replace"`. There is no incremental loading, append mode, or change-data-capture in this release. Plan rerun frequency and warehouse costs accordingly.

---

## Resetting Pipeline State

To start a project clean:

```bash
# dlt working directory and any local DuckDB output
rm -rf .dlt/ *.duckdb

# local PipelineKit state (run history, diagnostics, health records)
rm -rf .pipelinekit/

# regenerate a fresh config if needed
rm -f pipelinekit.yaml
pipelinekit init
```

State is metadata only — never your pipeline data — and lives under `.pipelinekit/state.db`. Removing it discards run history and recorded diagnostics; it does not touch your warehouse.

---

## Getting AI Diagnosis

```bash
pipelinekit diagnose                 # most recent run
pipelinekit diagnose <run-id>        # a specific run from `pipelinekit status`
pipelinekit diagnose --approve       # review recommended actions interactively
```

- **Reading confidence scores.** The result reports `confidence` from `0.00` to `1.00`. A low score, or an explicitly *inconclusive* status, means the evidence was insufficient — treat it as a lead, not a verdict.
- **Acting on recommendations.** Recommended actions are listed with a risk level and reversibility. PipelineKit never executes them; with `--approve` it records which you approved so the decision is auditable, but you perform the action yourself.

---

## Escalation

Before escalating, gather:

- The exact `PK-*` error code and message.
- `pipelinekit status` output (the failing run ID and recent history).
- The `pipelinekit diagnose` result for the failing run (finding, confidence, evidence).
- `pipelinekit health` output.
- The relevant adapter logs (e.g. `transform/logs/` for dbt failures).

Include all of the above in the escalation. The error code plus the diagnosis is usually enough to route the issue without a live reproduction.
