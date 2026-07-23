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

### `pipelinekit blueprint outdated [--json]`
Compare installed blueprint versions against the registry.

| Option | Description |
|---|---|
| `--json` | Output the status as JSON instead of a table |

Shows each blueprint's installed version, the registry version, and whether an update is available. No installed blueprints exits 0 with a hint.

### `pipelinekit blueprint upgrade <name> [--dry-run] [--yes]`
Upgrade a blueprint to the latest registry version. A backup is taken first so the change can be rolled back.

| Argument / Option | Description |
|---|---|
| `name` (required) | Blueprint to upgrade |
| `--dry-run` | Show the upgrade (`installed → registry`) without writing |
| `--yes` | Skip the confirmation prompt |

Prints the target version's changelog and prompts before writing (unless `--yes`). Fails with `PK-REGISTRY-004` if the blueprint is not in the catalog, or `PK-REGISTRY-006` if it is already at the latest version.

### `pipelinekit blueprint rollback <name> [--version]`
Restore a blueprint from a local backup created during a prior `upgrade`.

| Argument / Option | Description |
|---|---|
| `name` (required) | Blueprint to roll back |
| `--version`, `-v` | A specific backed-up version to restore (defaults to the most recent backup) |

Fails with `PK-REGISTRY-007` if no backup exists for the blueprint.

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

### `pipelinekit architect dependency` (AM-4)
Map dependencies between installed blueprints and analyze the impact of a change. An edge `from → to` means `to` depends on `from` (`from` is upstream). Dependencies are stored in `state.db`; discovery is a static read of blueprint files — no execution, no AI.

#### `pipelinekit architect dependency scan`
Auto-detect dependencies by reading each blueprint's contracts, dbt `sources.yml`, and `blueprint.json`. No options. Finding zero dependencies is a valid result — the current blueprints are independent pipelines.

```
Scanning 3 blueprint(s) for dependencies...
✓ No auto-detected dependencies found (add manual dependencies with 'dependency add')
```

#### `pipelinekit architect dependency list`
Show every stored dependency as a table: From, To, Type, Reason, Detected. Prints `No dependencies defined.` when empty. No options.

#### `pipelinekit architect dependency add <from> <to> --type <type> [--reason]`
Add a manual dependency edge.

| Argument / Option | Description |
|---|---|
| `from` (required) | Upstream (producer) blueprint |
| `to` (required) | Downstream (consumer) blueprint |
| `--type` (required) | `contract` \| `dbt_source` \| `manual` |
| `--reason` | Why the dependency exists |

Fails with `PK-AM-001` if either blueprint is not installed, or `PK-AM-002` for an invalid type.

#### `pipelinekit architect dependency remove <from> <to>`
Remove the dependency between two blueprints (all types for the pair). Prints `No dependency found` if none existed.

#### `pipelinekit architect dependency impact <blueprint>`
Show which blueprints are affected if `<blueprint>` changes (every edge where it is the upstream `from`).

```
Impact Analysis — postgres-to-snowflake
─────────────────────────────────────────
If postgres-to-snowflake changes, these blueprints may be affected:
  → stripe-to-snowflake (manual: orders feed stripe reconciliation)
1 blueprint(s) depend on postgres-to-snowflake
```

---

## Contract Commands (DC-8 / DC-9 / DC-10)

Version data contracts and detect breaking schema changes. Contracts are discovered under `blueprints/<name>/contracts/*.yaml`; version snapshots are stored in `state.db`.

### `pipelinekit contract version [--history] [--blueprint <name>] [--diff <a> <b>]`
Show contract versions: the latest of every contract by default.

| Option | Description |
|---|---|
| `--history` | Show the full version history per contract |
| `--blueprint` | Filter to a single blueprint |
| `--diff <a> <b>` | Diff two versions, e.g. `--diff v1.0.0 v1.1.0` (takes two values; requires `--blueprint`) |

Diff output marks `+` added fields, `-` removed fields, and `~` changed constraints. A `--diff` referencing an unknown version fails with `PK-DC-008`.

### `pipelinekit contract snapshot [--force]`
Snapshot every discovered contract, computing a semantic version bump (PATCH additive / MINOR tightened / MAJOR breaking).

| Option | Description |
|---|---|
| `--force` | Accept a breaking change and write the MAJOR version |

Without `--force`, a snapshot that would introduce a breaking (MAJOR) change is **blocked** with `PK-DC-011` and the existing version is preserved; the command exits 1. The warning block lists removed columns and any dbt models that reference them.

When a breaking change is accepted with `--force` (DC-10), a change notification record is created for every consumer registered against the affected table, and the command prints `✉ N consumer(s) notified`. If no consumers are registered for that table, no notification line is shown (this is normal, not an error — see `PK-DC-012`).

### `pipelinekit contract check-breaking`
Compare current contracts against their latest snapshots without writing anything. No options. Exits 1 if any breaking change is detected; contracts with no baseline are reported as needing a first `snapshot`.

### `pipelinekit contract consumer` (DC-10)
Register downstream consumers who watch a contract table, so they receive a notification record when a breaking change is accepted. Consumers and notifications are stored in `state.db` (`dc_consumers`, `dc_notifications`) — this is the audit-trail layer only; **no email is sent** (delivery via the OM alerting system is a future integration).

#### `pipelinekit contract consumer add <blueprint> --email <email> --table <table>`
Register a consumer to watch one contract table. Re-registering the same blueprint/table/email is idempotent.

| Argument / Option | Description |
|---|---|
| `blueprint` (required) | Blueprint to watch |
| `--email` (required) | Consumer email |
| `--table` (required) | Contract table to watch |

```
✓ Consumer registered: analyst@company.com watching charges (stripe-to-snowflake)
```

#### `pipelinekit contract consumer list`
List every registered consumer across all installed blueprints as a table: Blueprint, Table, Consumer Email, Registered At. Prints `No consumers registered.` when empty. No options.

#### `pipelinekit contract consumer remove <blueprint> --email <email> --table <table>`
Remove a registered consumer.

| Argument / Option | Description |
|---|---|
| `blueprint` (required) | Blueprint to stop watching |
| `--email` (required) | Consumer email |
| `--table` (required) | Contract table |

Prints `✓ Consumer removed`, or `No consumer found for {blueprint}/{table}/{email}` if there was no match.

### `pipelinekit contract notifications [--clear]` (DC-10)
View or clear pending contract-change notifications.

| Option | Description |
|---|---|
| `--clear` | Mark all pending notifications as read |

Without `--clear`, prints a table of unread notifications (Blueprint, Table, Change, Consumer, Created) and a count, or `No pending notifications.` when empty. With `--clear`, prints `✓ N notification(s) marked as read`.

```
Pending Notifications
──────────────────────────────────────────────────────────────────────
┌─────────────────────┬─────────┬───────────────┬─────────────────────┐
│ Blueprint           │ Table   │ Change        │ Consumer            │
├─────────────────────┼─────────┼───────────────┼─────────────────────┤
│ stripe-to-snowflake │ charges │ v1.0.0→v2.0.0 │ analyst@company.com │
└─────────────────────┴─────────┴───────────────┴─────────────────────┘
1 pending notification(s). Run with --clear to mark as read.
```

---

## Quality Commands (QM-4 / QM-6)

Measure test coverage and detect volume anomalies. Coverage is a read-only scan of blueprint files; row counts are stored in `state.db`.

### `pipelinekit quality coverage [--blueprint <name>] [--format <table|json>]`
Report dbt test and Soda check coverage for installed blueprints.

| Option | Description |
|---|---|
| `--blueprint` | Filter to a single blueprint |
| `--format` | `table` (default) or `json` |

Reports per-model column coverage %, untested columns, and the Soda check inventory. Fails with `PK-QM-001` if no blueprints are installed.

### `pipelinekit quality record-counts --blueprint <name> --table <table>:<count> [...]`
Record row-count snapshots for one or more tables.

| Option | Description |
|---|---|
| `--blueprint` (required) | Blueprint name |
| `--table` (required, repeatable) | `table:count` pair, e.g. `charges:45231` |

After recording, each table shows either `establishing — N/3 snapshots` or its baseline status.

### `pipelinekit quality check-anomalies --blueprint <name> [--threshold <pct>]`
Compare the latest recorded counts against the rolling baseline.

| Option | Description |
|---|---|
| `--blueprint` (required) | Blueprint name |
| `--threshold` | Deviation threshold percent (default `20.0`) |

Fewer than 3 snapshots for a table yields `ESTABLISHING`. Exits 1 (with `PK-QM-003` in the output) if any table is flagged `ANOMALY`.

### `pipelinekit quality row-count-history --blueprint <name> --table <name> [--limit <n>]`
Show recorded row counts for one table, newest first, with each snapshot's deviation from the mean.

| Option | Description |
|---|---|
| `--blueprint` (required) | Blueprint name |
| `--table` (required) | Table name |
| `--limit` | Number of snapshots to show (default `10`) |

---

## Governance Commands (GM-1 / GM-2)

Assign ownership to installed blueprints. Ownership is stored in `state.db`; missing ownership surfaces as a warning in `pipelinekit health --strict`.

### `pipelinekit governance owner set <blueprint> --name <name> --email <email> [--team] [--notes]`
Assign or update the owner of a blueprint.

| Argument / Option | Description |
|---|---|
| `blueprint` (required) | Blueprint to assign an owner |
| `--name` (required) | Owner name |
| `--email` (required) | Owner email (validated) |
| `--team` | Team name |
| `--notes` | Free-form notes |

Fails with `PK-GM-001` if the blueprint is not installed, or `PK-GM-002` for an invalid email.

### `pipelinekit governance owner get <blueprint>`
Show the owner of a blueprint, or a message if none is set.

### `pipelinekit governance owner list`
List every installed blueprint with its ownership status; warns about any unowned blueprints.

### `pipelinekit governance owner remove <blueprint>`
Remove the owner from a blueprint.

### `pipelinekit governance convention` (GM-2)
Define regex-based naming conventions and check installed blueprints against them. Conventions are stored in `state.db` (`gm_conventions`). Checking is read-only — **violations are warnings only and never block pipeline execution**. Valid scopes: `blueprint`, `table`, `column`, `contract_file`. A name passes a scope if it matches at least one registered convention for that scope (`re.fullmatch`).

#### `pipelinekit governance convention add --scope <scope> --pattern <regex> [--description <text>]`
Add a naming convention.

| Option | Description |
|---|---|
| `--scope` (required) | `blueprint` \| `table` \| `column` \| `contract_file` |
| `--pattern` (required) | Regex pattern the name must match |
| `--description` | Human-readable description |

Fails with `PK-GM-003` for an invalid scope, or `PK-GM-004` if the pattern is not valid Python regex.

```
✓ Convention added: table → ^(stg|fct|dim|raw)_[a-z_]+
```

#### `pipelinekit governance convention list`
List all conventions as a table: ID, Scope, Pattern, Description. Prints `No naming conventions defined.` when empty. No options.

#### `pipelinekit governance convention check <blueprint>`
Check a blueprint's names against registered conventions. For each scope with a convention, the relevant names are extracted (blueprint name; dbt model names and column names via `schema.yml`; `contracts/*.yaml` filenames) and validated. Exits 1 if any violation is found, 0 if all comply or no conventions are defined.

```
Convention Check — stripe-to-snowflake
───────────────────────────────────────────────────────

✓ All 4 name(s) comply with 1 convention(s)
```

A non-compliant name is reported as `⚠ {name}  {scope}  does NOT match {pattern}`.

#### `pipelinekit governance convention remove <id>`
Remove a convention by its ID (from `convention list`). Prints `✓ Convention removed`, or `No convention found with ID {id}` if the ID does not exist.

---

## Observability Commands (OM-4)

Define and evaluate Service Level Objectives. SLOs are stored in `state.db` and evaluated against existing DC (freshness), QM (row count), and coverage data — no warehouse connection.

### `pipelinekit observability slo set <blueprint> --table <name> --type <type> --threshold <n> [--unit]`
Assign or update an SLO for a blueprint/table.

| Argument / Option | Description |
|---|---|
| `blueprint` (required) | Blueprint name |
| `--table` (required) | Table or dbt model name |
| `--type` (required) | `freshness` \| `row_count` \| `coverage` |
| `--threshold` (required) | Target value (hours / rows / percent) |
| `--unit` | `hours` \| `rows` \| `percent` |

Fails with `PK-OM-002` for an invalid SLO type.

### `pipelinekit observability slo list`
List all defined SLOs as a table: Blueprint, Table, Type, Threshold, Unit.

### `pipelinekit observability slo check <blueprint>`
Evaluate every SLO for a blueprint against current `state.db` data. Each SLO is `OK`, `VIOLATED`, or `NO_DATA` (insufficient history — not a failure). Exits 1 (with `PK-OM-001` in the output) if any SLO is `VIOLATED`.

### `pipelinekit observability slo remove <blueprint> --table <name> --type <type>`
Remove an SLO. Prints a message if no matching SLO exists.

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
| `pipelinekit health ownership` | Check that every installed blueprint has an owner (GM-1) |

The `ownership` check (added in Phase 2, GM-1) is the sixth check; an unowned blueprint is a warning, so `--strict` exits 1 while the default run still exits 0.

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
| `PK-DC-008` | Contract version not found (`--diff`) | Run `contract version --history` for valid versions |
| `PK-DC-009` | Version format invalid (not MAJOR.MINOR.PATCH) | Use e.g. `v1.0.0` |
| `PK-DC-010` | State write failed during contract snapshot | Check disk/permissions on `state.db` |
| `PK-DC-011` | Breaking change blocked (MAJOR bump) | Review changes, re-run `snapshot --force` |
| `PK-DC-012` | No consumers registered (informational) | Register consumers with `contract consumer add` |
| `PK-QM-001` | No blueprints found for coverage scan | Install a blueprint first |
| `PK-QM-002` | `schema.yml` parse error | Fix the YAML syntax |
| `PK-QM-003` | Volume anomaly detected | Investigate the affected table's pipeline run |
| `PK-GM-001` | Blueprint not found | Run `pipelinekit blueprint list` |
| `PK-GM-002` | Invalid owner email | Provide a valid `name@domain.tld` address |
| `PK-GM-003` | Invalid convention scope | Use `blueprint`, `table`, `column`, or `contract_file` |
| `PK-GM-004` | Invalid regex pattern | Fix the regex before adding the convention |
| `PK-OM-001` | SLO violated | Investigate freshness / row count / coverage |
| `PK-OM-002` | Invalid SLO type | Use `freshness`, `row_count`, or `coverage` |
| `PK-AM-001` | Blueprint not found (dependency) | Run `pipelinekit blueprint list` |
| `PK-AM-002` | Invalid dependency type | Use `contract`, `dbt_source`, or `manual` |
