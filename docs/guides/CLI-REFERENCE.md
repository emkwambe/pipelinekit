# CLI Reference

Complete reference for every PipelineKit command. Invoke as `pipelinekit <command>` (or `poetry run pipelinekit <command>` from the source tree).

---

## Global Options

| Option | Description |
|---|---|
| `--version`, `-v` | Print the installed version and exit |
| `--help` | Show help for the app or any command |

Running `pipelinekit` with no command shows help.

---

## Core Commands

### `pipelinekit init`
Create a default `pipelinekit.yaml` in the current directory and add `.pipelinekit/` to `.gitignore`. Refuses to overwrite an existing config.

No options.

### `pipelinekit validate [--contracts]`
Validate `pipelinekit.yaml`.

| Option | Description |
|---|---|
| `--contracts` | Also load and structurally validate the project's data contracts |

Data-level contract checks run during `pipelinekit run` (they need a live warehouse). Exits non-zero on a validation failure.

### `pipelinekit run [--dry-run]`
Execute the configured pipeline.

| Option | Description |
|---|---|
| `--dry-run` | Validate that adapters are reachable without executing the pipeline |

Exits non-zero if the run (or dry-run validation) fails.

### `pipelinekit status`
Show the five most recent pipeline runs with status, start time, and duration. No options.

---

## Blueprint Commands

### `pipelinekit blueprint list`
List blueprints installed under `./blueprints/`. No options.

### `pipelinekit blueprint validate [name]`
Validate blueprint structure against `schemas/blueprint.schema.json`.

| Argument | Description |
|---|---|
| `name` (optional) | Blueprint to validate; defaults to all installed blueprints |

### `pipelinekit blueprint info <name>`
Show details for one blueprint: source, destination, contract count, KPIs, deploy-time and Time-to-Trusted-Data targets.

| Argument | Description |
|---|---|
| `name` (required) | Blueprint name |

### `pipelinekit blueprint search <query> [--verified]`
Search the remote blueprint registry by source, destination, name, or tag.

| Argument / Option | Description |
|---|---|
| `query` (required) | Search term |
| `--verified` | Show only verified blueprints |

### `pipelinekit blueprint install <name> [--version] [--force]`
Download, validate, and write a blueprint from the registry.

| Argument / Option | Description |
|---|---|
| `name` (required) | Blueprint name to install |
| `--version`, `-v` | Specific version to install |
| `--force` | Overwrite if already installed |

> The public registry is live at **[registry.pipelinekit.dev](https://registry.pipelinekit.dev)** and currently lists 3 verified blueprints.

---

## Generate Commands

### `pipelinekit generate blueprint`
Propose a blueprint with AI. Plan-only by default — review before applying.

| Option | Description |
|---|---|
| `--source`, `-s` (required) | Source type (e.g. `postgres`, `salesforce`, `stripe`) |
| `--destination`, `-d` (required) | Destination type (e.g. `snowflake`, `bigquery`, `duckdb`) |
| `--tables`, `-t` (required) | Comma-separated table list |
| `--provider`, `-p` | AI provider override |
| `--name`, `-n` | Override the blueprint name |
| `--plan` | Plan only: print a plan ID, write no files (safe default) |
| `--interactive` | Review each asset and apply approved ones in one session |

### `pipelinekit generate show <plan-id>`
Re-display a stored proposal and its per-asset states.

| Argument | Description |
|---|---|
| `plan-id` (required) | Plan ID from a prior `generate blueprint` |

---

## Apply Commands

### `pipelinekit apply plan <plan-id> [--interactive]`
Write the approved assets from a stored proposal to `blueprints/<name>/`.

| Argument / Option | Description |
|---|---|
| `plan-id` (required) | Plan ID to apply |
| `--interactive` | Review each asset before writing |

Without `--interactive`, only assets already approved in a prior `generate blueprint --interactive` session are written; otherwise it fails with `PK-GEN-003`. There is no generate→auto-apply shortcut.

---

## Diagnose Commands

### `pipelinekit diagnose [run-id] [--provider] [--approve]`
AI-assisted root-cause analysis of a run.

| Argument / Option | Description |
|---|---|
| `run-id` (optional) | Run to diagnose; defaults to the most recent run |
| `--provider`, `-p` | AI provider override |
| `--approve` | Interactively review recommended actions (records approval; never executes) |

---

## Architect Commands

### `pipelinekit architect analyze [question] [--type] [--provider] [--approve]`
Reason about your analytics architecture.

| Argument / Option | Description |
|---|---|
| `question` (optional) | Natural-language architecture question |
| `--type`, `-t` | `tool_selection` \| `cost_optimization` \| `adr_compliance` \| `stack_evolution` \| `blueprint_selection` (default `tool_selection`) |
| `--provider`, `-p` | AI provider override |
| `--approve` | Review the recommendation and record a decision |

### `pipelinekit architect check-adrs <change> [--provider]`
Check whether a proposed change complies with your ADRs.

| Argument / Option | Description |
|---|---|
| `change` (required) | Proposed change to check |
| `--provider`, `-p` | AI provider override |

### `pipelinekit architect compare <tool-a> <tool-b> [--provider]`
Compare two tools for your specific stack and data profile.

| Argument / Option | Description |
|---|---|
| `tool-a`, `tool-b` (required) | The two tools to compare |
| `--provider`, `-p` | AI provider override |

---

## Health Commands

### `pipelinekit health [--strict]`
Run all six health checks (deps, security, blueprints, specs, tests, ownership), print a summary, and record the run.

| Option | Description |
|---|---|
| `--strict` | Exit 1 if any check is a warning or error (default: always exit 0) |

Health is non-blocking by default so it is safe in scripts and CI.

| Subcommand | Description |
|---|---|
| `pipelinekit health deps` | Check for outdated dependencies |
| `pipelinekit health security` | Check for known vulnerabilities (requires `pip-audit`) |
| `pipelinekit health blueprints` | Validate all installed blueprints against their schemas |
| `pipelinekit health specs [--fix]` | Check SPEC status headers for drift; `--fix` rewrites drifted headers to Implemented |
| `pipelinekit health tests` | Report the last test run's coverage |

---

## Migrate Commands

### `pipelinekit migrate analyze <config> [--provider] [--apply] [--write-draft]`
Analyze an existing pipeline config and propose a PipelineKit migration.

| Argument / Option | Description |
|---|---|
| `config` (required) | Path to an Airbyte/Fivetran/Python/pipelinekit config |
| `--provider`, `-p` | AI provider override |
| `--apply` | Write the draft to `pipelinekit.proposed.yaml` after analysis |
| `--write-draft` | Write the draft even when blocking gaps exist (review all FIXMEs before `pipelinekit validate`) |

Without `--write-draft`, `--apply` refuses to write while blocking gaps remain (`PK-MIGRATE-003`). The draft is always written to `pipelinekit.proposed.yaml`, never `pipelinekit.yaml`.

---

## Error Codes Reference

Every error carries a stable `PK-[AREA]-[NUMBER]` code. The table below is the operator-facing summary; the authoritative list is `docs/reference/Error-Codes.md`.

| Code | Meaning | Typical action |
|---|---|---|
| `PK-CONFIG-001` | `pipelinekit.yaml` failed schema validation | Fix the reported field(s) |
| `PK-CONFIG-002` | Required section missing | Add the missing section |
| `PK-CONFIG-003` | `pipelinekit.yaml` not found | Run `pipelinekit init` |
| `PK-CONFIG-004` | `pipelinekit.yaml` is not valid YAML | Fix the YAML syntax |
| `PK-CONFIG-005` | Failed to write `pipelinekit.yaml` | Check directory permissions |
| `PK-CONFIG-006` | Required credential empty after `${VAR}` interpolation | Set the environment variable |
| `PK-STATE-001` | Cannot open/create `state.db` | Check `.pipelinekit/` permissions |
| `PK-STATE-002` | Cannot write to state database | Check disk/permissions |
| `PK-STATE-003` | State schema corrupted or incompatible | Reset state (remove `.pipelinekit/`) |
| `PK-RUNTIME-001` | Pipeline execution failed (general) | Read the failing step's detail |
| `PK-RUNTIME-002` | Provider initialization failed | Check adapter config |
| `PK-RUNTIME-003` | Pipeline already running (state conflict) | Wait or clear the stale run |
| `PK-ADAPTER-001` | Adapter connection failed | Check source/destination reachability and credentials |
| `PK-ADAPTER-002` | Adapter execution failed | Inspect the adapter (e.g. dbt) logs |
| `PK-ADAPTER-003` | Adapter returned invalid result | Check adapter version/config |
| `PK-CONTRACT-001` | Required column missing | Fix the source schema or contract |
| `PK-CONTRACT-002` | Freshness SLA violated | Investigate stale data |
| `PK-CONTRACT-003` | Uniqueness constraint violated | Deduplicate the source |
| `PK-CONTRACT-004` | Not-null constraint violated | Fix nulls in the source |
| `PK-CONTRACT-005` | Accepted-values constraint violated | Fix invalid values |
| `PK-CONTRACT-006` | Row count outside expected range | Investigate volume change |
| `PK-CONTRACT-007` | Contract file not found for table | Add the contract file |
| `PK-CONTRACT-008` | Contract file invalid YAML or schema | Fix the contract definition |
| `PK-BLUEPRINT-001` | `blueprint.json` failed schema validation | Fix the manifest |
| `PK-BLUEPRINT-002` | `blueprint.json` not found | Check the blueprint directory |
| `PK-BLUEPRINT-003` | Blueprint directory not found | Verify the blueprint name |
| `PK-BLUEPRINT-004` | Blueprint dbt project invalid | Fix the dbt project |
| `PK-NOTIFY-001` | Notification provider unavailable | Check provider/config |
| `PK-NOTIFY-002` | Notification delivery failed | Inspect provider response |
| `PK-NOTIFY-003` | Invalid recipient address | Fix the recipient |
| `PK-NOTIFY-004` | API key missing or invalid | Set `RESEND_API_KEY` |
| `PK-AI-001` | AI provider unavailable (missing key / unreachable) | Set the provider's API key |
| `PK-AI-002` | AI response failed schema validation | Retry; try another provider |
| `PK-AI-003` | AI confidence below threshold | Treat the result as advisory |
| `PK-DIAG-001` | Run ID not found in `state.db` | Run `pipelinekit status` for valid IDs |
| `PK-DIAG-002` | Evidence collection failed | Check state availability |
| `PK-DIAG-003` | Diagnosis engine initialization failed | Check provider/config |
| `PK-ARCH-001` | Architecture context collection failed | Check project state |
| `PK-ARCH-002` | Architecture result failed schema validation | Retry; try another provider |
| `PK-ARCH-003` | ADR parsing failed | Check `docs/decisions/` |
| `PK-ARCH-004` | Insufficient run history (< 5 runs) | Run more pipelines, then retry |
| `PK-HEALTH-001` | Dependency check failed (poetry unavailable) | Install/repair Poetry |
| `PK-HEALTH-002` | Security check failed (pip-audit error) | Install `pip-audit` |
| `PK-HEALTH-003` | Blueprint validation failed | Fix the blueprint |
| `PK-HEALTH-004` | SPEC drift detected | Reconcile SPEC and code |
| `PK-GEN-001` | Proposal failed — provider error / invalid JSON | Retry; try another provider |
| `PK-GEN-002` | Proposed plan failed schema validation | Re-propose; review the plan |
| `PK-GEN-003` | Apply failed — no approved assets | Review with `generate blueprint --interactive` |
| `PK-GEN-004` | Blueprint directory already exists | Remove it or choose a new name |
| `PK-GEN-005` | Proposed `blueprint.json` failed schema validation | Edit the manifest during review |
| `PK-GEN-006` | Source/destination not supported by adapter registry | Choose a supported connector |
| `PK-GEN-007` | Asset state transition violation | Internal guard; follow the review flow |
| `PK-REGISTRY-001` | Registry unreachable — network error (no cache) | Check connectivity / wait for deploy |
| `PK-REGISTRY-002` | Blueprint validation failed — schema or missing assets | Inspect the blueprint |
| `PK-REGISTRY-003` | Blueprint already installed — use `--force` | Re-run with `--force` |
| `PK-REGISTRY-004` | Blueprint not found in catalog | Check the name |
| `PK-REGISTRY-005` | Version not found in catalog | Check the version |
| `PK-MIGRATE-001` | Config file not found | Check the path |
| `PK-MIGRATE-002` | Config format not recognized | Use Airbyte/Fivetran/Python/pipelinekit config |
| `PK-MIGRATE-003` | Blocking gaps exist — use `--write-draft` to write anyway | Resolve gaps or pass `--write-draft` |
| `PK-MIGRATE-004` | AI analysis failed (invalid response) | Retry; try another provider |
| `PK-MIGRATE-005` | Python file parsing failed (syntax error) | Fix the Python syntax |
