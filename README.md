# PipelineKit

**The AI-native operating system for trusted analytics pipelines.**

PipelineKit is a CLI-first, local-first tool for building, validating, running, and diagnosing data pipelines you can trust. It coordinates ingestion (dlt), transformation (dbt), data contracts, and quality checks (Soda) behind a single deterministic command surface — and adds an AI layer that diagnoses failures, proposes blueprints, and reasons about architecture without ever touching production on its own.

---

## What it does

PipelineKit turns a `pipelinekit.yaml` file into a verifiable analytics pipeline: it validates configuration before execution, runs ingestion → transformation → quality as deterministic steps, and enforces data contracts so you know your numbers are correct. When something breaks, AI diagnostics explain the root cause with evidence — they never auto-fix it. Everything is reproducible from the terminal, and every AI capability observes, diagnoses, and proposes, but never executes or auto-applies.

---

## Quick Install

PipelineKit is a Python package managed with Poetry.

```bash
git clone https://github.com/emkwambe/pipelinekit.git
cd pipelinekit
poetry install
poetry run pipelinekit --version
```

Requirements: **Python 3.11+**, **Poetry**. Running the local Blueprint #001 verification additionally needs **Docker Desktop** (for a throwaway Postgres) — not required for the quickstart below.

---

## 5-Minute Quickstart

```bash
# 1. Create a project config in the current directory
poetry run pipelinekit init

# 2. Validate the generated pipelinekit.yaml
poetry run pipelinekit validate

# 3. See the blueprints available locally
poetry run pipelinekit blueprint list

# 4. Dry-run: check adapters without executing the pipeline
poetry run pipelinekit run --dry-run
```

`init` writes a default `pipelinekit.yaml` and adds `.pipelinekit/` to `.gitignore`. `validate` confirms the config is well-formed. `run --dry-run` checks that the configured adapters are reachable without moving any data.

For a full walkthrough that loads real rows end-to-end, see **[docs/guides/GETTING-STARTED.md](docs/guides/GETTING-STARTED.md)**.

---

## Blueprint Catalog

A blueprint is a complete, verifiable pipeline package (ingestion + transform + contracts + quality + alerts + docs).

| Name | Source | Destination | Status |
|---|---|---|---|
| `postgres-to-snowflake` | Postgres | Snowflake | Hand-crafted · locally verified (1,000 rows) |
| `salesforce-to-snowflake` | Salesforce | Snowflake | Hand-crafted · locally verified (800 rows) |
| `stripe-to-snowflake` | Stripe | Snowflake | AI-proposed, human-approved · local verification pending |

See **[docs/guides/BLUEPRINT-GUIDE.md](docs/guides/BLUEPRINT-GUIDE.md)**.

---

## CLI Reference

| Command | Purpose |
|---|---|
| `pipelinekit init` | Create a default `pipelinekit.yaml` in the current directory |
| `pipelinekit validate [--contracts]` | Validate config (and optionally data contracts) |
| `pipelinekit run [--dry-run]` | Execute the pipeline (or validate adapters only) |
| `pipelinekit status` | Show recent run history |
| `pipelinekit blueprint list/validate/info/search/install` | Manage blueprints |
| `pipelinekit diagnose [run-id]` | AI root-cause analysis of a run |
| `pipelinekit architect analyze/check-adrs/compare` | AI architecture reasoning |
| `pipelinekit health [--strict]` | Check installation and project health |
| `pipelinekit generate blueprint` | Propose a blueprint with AI (review before applying) |
| `pipelinekit apply plan <plan-id>` | Write approved assets from a proposal |
| `pipelinekit migrate analyze <config>` | Propose a migration from Airbyte/Fivetran/Python |

Full reference: **[docs/guides/CLI-REFERENCE.md](docs/guides/CLI-REFERENCE.md)**.

---

## Architecture

PipelineKit is organized in five layers: a **Foundation** (CLI, config, local SQLite state), a **Data Layer** (ingestion/transformation/quality adapters), a **Trust Layer** (data contracts and blueprints), an **Intelligence Layer** (the `LLMProvider` contract and AI diagnostics/proposal/migration), and an **Architecture Layer** (AI reasoning about the stack itself). Every external tool sits behind an adapter, every AI provider behind one interface, and architecture changes flow only through the document chain `Constitution → ADR → SPEC → Code`. See **[docs/reference/ARCHITECTURE.md](docs/reference/ARCHITECTURE.md)**.

---

## Contributing

PipelineKit follows a strict document chain — architecture lives in version-controlled documents, never in prompts:

1. Read `docs/constitution/Product-Constitution.md`, then the relevant ADR and SPEC.
2. Check `docs/reference/Architectural-Smells.md` before writing code.
3. Implement the smallest useful version behind an interface, with tests.
4. Keep the SPEC and code in sync; flag any deviation explicitly.

Quality gate for every change: `pytest` (≥80% coverage), `ruff`, `black`, `mypy` — all clean.

---

## License

Apache License 2.0. See [LICENSE](LICENSE).
