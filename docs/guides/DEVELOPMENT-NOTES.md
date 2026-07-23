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
