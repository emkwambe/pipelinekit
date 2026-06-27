# Error Code Taxonomy

Every error carries a stable `PK-[AREA]-[NUMBER]` code. Classes verified against `src/pipelinekit/core/errors.py`; code ranges verified against `docs/reference/Error-Codes.md`. All classes derive from the base `PipelineKitError(code, message, context)`.

| Error class | Codes | Triggered by | What to do |
|---|---|---|---|
| `ConfigurationError` | `PK-CONFIG-001..006` | `init`, `validate` | Correct `pipelinekit.yaml` / set the `${VAR}` |
| `StateError` | `PK-STATE-001..003` | any (state.db) | Check `.pipelinekit/` permissions |
| `RuntimeError` | `PK-RUNTIME-001..003` | `run` | Read the failing step's detail |
| _(no dedicated class)_ | `PK-ADAPTER-001..003` | `run` | Check source/destination reachability & credentials |
| `ContractError` | `PK-CONTRACT-001..008` | `validate --contracts`, `run` | Fix source data or the contract |
| `BlueprintError` | `PK-BLUEPRINT-001..004` | `blueprint validate/info` | Fix the manifest / directory |
| _(no dedicated class)_ | `PK-NOTIFY-001..004` | `run` (notifications) | Set `RESEND_API_KEY` / fix recipient |
| `LLMError` | `PK-AI-001..003` | `diagnose`, `architect`, `generate`, `migrate` | Set the provider API key / retry |
| `DiagnosticsError` | `PK-DIAG-001..003` | `diagnose` | Check run id / evidence in state |
| `ArchitectureError` | `PK-ARCH-001..004` | `architect` | Run more pipelines (need history) |
| `HealthError` | `PK-HEALTH-001..004` | `health` | Install poetry / pip-audit |
| `ProposalError` | `PK-GEN-001..007` | `generate`, `apply` | Follow the review flow |
| `RegistryError` | `PK-REGISTRY-001..005` | `blueprint search/install` | Check connectivity / use `--force` |
| `MigrationError` | `PK-MIGRATE-001..005` | `migrate analyze` | Check path/format / use `--write-draft` |

`PK-ADAPTER-*` and `PK-NOTIFY-*` have no dedicated exception subclass yet — they are carried by the base `PipelineKitError`. The CLI renders the code and message; it never surfaces a raw stack trace.
