# PipelineKit — Development Notes

Internal notes for contributors. Not user-facing. Captures non-obvious gotchas
discovered while building PipelineKit.

## Rich markup in CLI output

When printing user-provided strings (regex patterns, names, etc.) that may
contain brackets, always use `markup=False` or `rich.markup.escape()` to prevent
Rich from interpreting brackets as markup tags.

Example: the pattern `^(stg|fct)_[a-z_]+` contains `[a-z_]`, which Rich parses as
a (style) tag and silently drops without this protection — so the printed pattern
would appear as `^(stg|fct)_+`, losing the character class. The stored value is
unaffected; only the rendered output is wrong, which makes it easy to miss.

Guidance:

- `console.print(text, markup=False)` for plain lines that echo user input.
- `rich.markup.escape(text)` when the value goes into a `Table` cell (table cells
  are markup-parsed too).

Affected files: `cli/governance.py` (`convention add`, `check`, `list`).
Fixed in Sprint 9 (commit `c5948ab`).

## SOC 2 CC8 — Change Management evidence

GM-3 (Approval Workflow) provides the record layer for SOC 2 CC8.
Approval requests and decisions are stored in state.db:
- gm_approvers: who is authorized to approve for each blueprint
- gm_approval_requests: full audit trail of requests and decisions

Approvals are RECORD-ONLY in v1. They do not block pipeline execution.
Hard enforcement gates are planned for GM-6 (Policy Enforcement).

When presenting to auditors:
- Export gm_approval_requests for the audit period
- Show request_code, blueprint_name, change_description,
  requested_by, status, decided_by, decision_reason, decided_at

## AI Provider Cascade

The cascade is implemented in `src/pipelinekit/ai/cascade.py`. It runs a prompt
against a primary provider, then ordered fallbacks.

Key implementation notes:
- `MAX_CONTEXT_TOKENS` is declared as a class constant on each provider.
- Token estimation is `int(len(prompt.split()) * 1.3) + 1` (conservative).
- The cascade logs at INFO level under the `pipelinekit.ai.cascade` logger —
  check logs when debugging provider routing.
- `CascadeConfig` is built by `get_cascade_config()` at call time.
- Zero-config: no fallbacks configured = a single provider, same as before.
- The only AI exception is `LLMError`; there is no `RateLimitError`/`NetworkError`
  hierarchy, so the cascade catches `LLMError`/`Exception` and detects rate limits
  heuristically from the error text. `CascadeExhaustedError` subclasses `LLMError`
  with code `PK-AI-001`.

Configuration (current implementation): cascade config is **environment-variable
driven** — `PIPELINEKIT_AI_PRIMARY` and `PIPELINEKIT_AI_FALLBACKS` (comma-separated).
The strict Pydantic `PipelineConfig` has no `ai:` section, so a pipelinekit.yaml
`ai:` cascade block is not yet parsed; `get_cascade_config()` is forward-compatible
with one. Single-provider selection remains `diagnostics.provider` (or the
`--provider` flag).

Wiring note: `cascade.py` is provider-agnostic infrastructure that calls a
`complete(prompt)` primitive. The existing engines still call `provider.diagnose`/
`architect` directly; routing those through the cascade is future work (AI-9+).

When adding a new provider:
1. Add the `MAX_CONTEXT_TOKENS` class constant.
2. Register it in `providers/__init__.py` (`get_provider` / `_PROVIDER_NAMES`).
3. Add it to the cascade / provider documentation.

## Contract Lifecycle State Machine (DC-11)

DC-11 implements a formal state machine for contract evolution, defined in
`src/pipelinekit/contracts/lifecycle.py`.

Valid states: `DRAFT | ACTIVE | DEPRECATED | RETIRED`

Transition matrix (`_TRANSITIONS`):

```
DRAFT      → ACTIVE, RETIRED
ACTIVE     → DEPRECATED, RETIRED
DEPRECATED → RETIRED
RETIRED    → (terminal, no transitions)
```

Implementation notes:
- State is stored in the `dc_contract_lifecycle` table, `UNIQUE(blueprint_name,
  contract_file)` — **one row per contract, upserted in place**. The store holds
  the *current* state only; the previous state is overwritten on each transition.
  There is no separate transition-history table and no `lifecycle history` command.
- Default when unset: a contract with no recorded row is treated as `DRAFT`
  (`get_lifecycle_state` returns `None`, which callers interpret as implicit DRAFT).
- `set_lifecycle_state()` validates the target against `_TRANSITIONS[current]` and
  raises `ContractError` with code `PK-DC-013` for an unknown state name or a
  transition that is not permitted.
- `ACTIVE → RETIRED` and `DRAFT → RETIRED` are allowed as emergency/abandon
  transitions; `RETIRED` is terminal, so any transition out of it raises PK-DC-013.
- `id` and `created_at` are preserved across upserts; `changed_by`, `change_reason`,
  and `updated_at` reflect the most recent transition.

SOC 2 CC8 evidence: the `dc_contract_lifecycle` table records the current state
plus the `changed_by`, `change_reason`, and `updated_at` of the latest transition.
For a full per-transition audit trail, pair lifecycle changes with the GM-3 approval
workflow (`gm_approval_requests`), which retains every request and decision.
