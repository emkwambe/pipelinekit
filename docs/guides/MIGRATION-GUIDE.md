# Migrating to PipelineKit

PipelineKit reads an existing pipeline definition and proposes a PipelineKit equivalent. It reads and proposes — it never executes your existing pipeline, connects to a source, or writes a file without your approval.

This guide covers the migration path for Airbyte, Fivetran, and custom Python pipelines.

---

## Why Migrate?

- **Licensing.** PipelineKit is Apache 2.0. If your current tooling is under ELv2 or GPL, PipelineKit gives you an open, permissively licensed alternative you can build on freely.
- **AI-native operations.** Once on PipelineKit you get AI diagnostics (`diagnose`), architecture reasoning (`architect`), and blueprint proposal (`generate`) — capabilities that observe and recommend, never auto-apply.
- **Blueprint-driven standardization.** Migrating onto a verified blueprint replaces a bespoke pipeline with a contract-enforced, quality-checked, documented one.

---

## Supported Source Tools

| Tool | Config file | What PipelineKit reads |
|---|---|---|
| Airbyte | `connection.json` (config-API or public-API export) | source/destination type, streams, sync mode |
| Fivetran | `connector.json` | connector type, schema, enabled tables, sync frequency |
| Custom Python | `.py` file | connection strings, destination hint, table names (via AST inspection) |
| Existing `pipelinekit.yaml` | native | upgrade-path analysis |

Parsing is deterministic. The Python parser uses `ast.parse()` only — it **never executes** the file it reads.

---

## The Migration Flow

### Step 1 — Export your existing config

Export your Airbyte connection (`connection.json`), Fivetran connector (`connector.json`), or locate your custom Python pipeline file.

### Step 2 — Analyze

```bash
pipelinekit migrate analyze airbyte-connection.json
pipelinekit migrate analyze connector.json --provider mistral
pipelinekit migrate analyze my_pipeline.py
```

This parses the config deterministically, then asks the configured AI provider to map it onto PipelineKit and identify gaps. No files are written.

If you do not have a `pipelinekit.yaml` in the directory yet, pass `--provider` so PipelineKit knows which AI provider to use (the API key is read from that provider's environment variable).

### Step 3 — Review the proposal

The analysis prints:

- **Confidence** — `0.00`–`1.00` for the overall migration.
- **Mappings** — each source field classified as **clean** (maps directly), **partial** (maps with adjustment), **manual** (needs significant human work), or **unsupported** (no equivalent).
- **Gaps** — explicit items you must resolve, each **blocking** or non-blocking.
- **Blueprint recommendation** — the installed blueprint that best fits, if any.

### Step 4 — Write the draft

```bash
pipelinekit migrate analyze airbyte-connection.json --apply
```

`--apply` writes the proposed config to **`pipelinekit.proposed.yaml`** — never to `pipelinekit.yaml`, so it can't overwrite a live config. If blocking gaps remain, the write is refused with `PK-MIGRATE-003`. To write the draft anyway (with FIXME markers in place of the missing values), add `--write-draft`:

```bash
pipelinekit migrate analyze airbyte-connection.json --apply --write-draft
```

### Step 5 — Fill in FIXME markers

Open `pipelinekit.proposed.yaml` and resolve every gap — credentials, table lists, schedules, and anything the proposal could not infer. Credentials use `${VAR}` interpolation; set the environment variables, do not hardcode secrets.

### Step 6 — Validate

```bash
# rename the draft once you have filled it in
mv pipelinekit.proposed.yaml pipelinekit.yaml
pipelinekit validate
pipelinekit validate --contracts
```

### Step 7 — Run

```bash
pipelinekit run --dry-run    # confirm adapters are reachable
pipelinekit run
```

---

## Reading a Migration Proposal

**Mapping statuses**

- **clean** — the source field maps directly to a PipelineKit field. No action needed.
- **partial** — it maps, but with an adjustment you should review (e.g. an incremental sync mode mapped to an append write disposition).
- **manual** — there is a PipelineKit concept, but translating it requires real work.
- **unsupported** — no PipelineKit equivalent exists; this becomes a gap.

**Blocking gaps** are gaps that prevent a working pipeline — typically missing credentials, an unmapped table set, or a schedule that PipelineKit does not own. `--apply` refuses to write while any blocking gap remains, unless you pass `--write-draft`.

**FIXME markers** appear in the draft wherever a value could not be inferred. Each marks a field you must fill in before `pipelinekit validate` will pass. Treat the draft as a starting point, not a finished config.

**The `pipelinekit.proposed.yaml` format** is a standard `pipelinekit.yaml` — the same eight sections (see the [Configuration Reference](CONFIGURATION-REFERENCE.md)) — with `${VAR}` placeholders and FIXMEs for unresolved fields. `can_auto_apply` is always `false`.

---

## Common Migration Patterns

| From | To | Notes |
|---|---|---|
| Airbyte Postgres source | `postgres-to-snowflake` blueprint | Cleanest path; host/database/user map directly, credentials become `${VAR}` |
| Fivetran Salesforce connector | `salesforce-to-snowflake` blueprint | Object/table list maps to the salesforce source; review the field selection |
| Custom Python (dlt/SQLAlchemy) | any matching blueprint | Best-effort: connection scheme infers the source type, `destination=` infers the destination, list literals infer tables; confidence is intentionally low |

When a recommended blueprint is installed, the analysis names it so you can adopt its verified transform and contracts instead of starting from a blank config.

---

## After Migration

```bash
pipelinekit health          # deps, security, blueprints, specs, tests
pipelinekit diagnose        # AI root-cause analysis once you have runs
```

- **Run `pipelinekit health`** to confirm the installation and project are sound.
- **Set up alerting** by enabling the `notifications` section (Resend email; the API key comes from `RESEND_API_KEY`).
- **Enable AI diagnostics** by setting `diagnostics.enabled: true` and a `diagnostics.provider` in `pipelinekit.yaml`.
