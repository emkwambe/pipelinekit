# CLI Command Map

Every command, its arguments/flags, the `state.db` tables it reads and writes, and the external system it calls. Verified against `src/pipelinekit/cli/`.

| Command | Arguments / flags | Reads (state) | Writes (state) | External |
|---|---|---|---|---|
| `init` | — | — | — | writes `pipelinekit.yaml`, `.gitignore` |
| `validate` | `[--contracts]` | `pipelinekit.yaml`, `contracts/` | — | — |
| `run` | `[--dry-run]` | `pipelinekit.yaml` | `pipeline_runs` (pending → final) | dlt / dbt / Soda |
| `status` | — | `pipeline_runs` | — | — |
| `blueprint list` | — | `blueprints/` | — | — |
| `blueprint validate` | `[name]` | `blueprints/`, schema | — | — |
| `blueprint info` | `<name>` | `blueprints/` | — | — |
| `blueprint search` | `<query> [--verified]` | — | — | remote registry |
| `blueprint install` | `<name> [--version] [--force]` | — | `installed_blueprints` | remote registry |
| `generate blueprint` | `-s -d -t [--plan\|--interactive] [-p] [-n]` | `blueprints/`, schema | `blueprint_proposals` | AI provider |
| `generate show` | `<plan-id>` | `blueprint_proposals` | — | — |
| `apply plan` | `<plan-id> [--interactive]` | `blueprint_proposals` | `blueprint_proposals`; `blueprints/` files | — |
| `diagnose` | `[run-id] [--provider] [--approve]` | `pipeline_runs` / evidence | `diagnostic_results` | AI provider |
| `architect analyze` | `[question] [--type] [--provider] [--approve]` | project state | `architecture_results` | AI provider |
| `architect check-adrs` | `<change> [--provider]` | ADRs | `architecture_results` | AI provider |
| `architect compare` | `<tool-a> <tool-b> [--provider]` | project state | `architecture_results` | AI provider |
| `health` | `[--strict]` | project / tooling | `health_runs` | poetry / pip-audit |
| `health deps` | — | dependencies | — | poetry |
| `health security` | — | dependencies | — | pip-audit |
| `health blueprints` | — | `blueprints/`, schema | — | — |
| `health specs` | `[--fix]` | `docs/specifications/` | — | — |
| `health tests` | — | coverage report | — | — |
| `migrate analyze` | `<config> [--provider] [--apply] [--write-draft]` | — | writes `pipelinekit.proposed.yaml` | AI provider |

Notes: the full `health` run (no subcommand) records one row in `health_runs`; the individual `health <check>` subcommands render a single result and do not record. `apply plan` writes the approved blueprint assets to the filesystem under `blueprints/<name>/` and updates the proposal's applied state.
