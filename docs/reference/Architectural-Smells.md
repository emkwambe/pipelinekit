# PipelineKit — Architectural Smells

**File:** `docs/reference/Architectural-Smells.md`  
**Owner:** Command Center (Claude Chat)  
**Purpose:** Pre-flight checklist evaluated before any new capability, dependency, or structural change is approved.  
**Rule:** Claude Chat evaluates every proposed change against this list before Claude Code writes a single line.

---

## What Is an Architectural Smell?

An architectural smell is a signal that a proposed change — even if technically correct — is moving the system away from its governing principle.

Smells do not automatically block work. They trigger a pause, a question, and a deliberate decision. If the decision is to proceed, it goes through an ADR. If no ADR exists yet, the ADR is written first.

**The governing principle that every smell traces back to:**

> PipelineKit is the AI-native operating system for trusted analytics pipelines.

---

## The Smell Checklist

Evaluate every proposed feature, dependency, MCP, or structural change against all 12 smells before approving.

---

### Smell 1 — Untraceable Feature

**Signal:** A proposed feature cannot be traced cleanly through:

```
Governing Principle → Constitution → ADR → Specification → Contract → Schema → Implementation → Tests
```

Any broken link in this chain is a smell.

**Test:** Can you name the ADR and SPEC that authorize this feature?  
**Action:** If no — write the ADR and SPEC first. If the ADR cannot be justified — do not build the feature.

---

### Smell 2 — Concrete Provider Dependency

**Signal:** A module imports or directly depends on a concrete provider (dlt, dbt, Soda, Resend, OpenAI, Anthropic) outside its designated adapter file.

**Examples:**
- `import dlt` in `runner.py` — smell
- `import resend` in `dispatcher.py` — smell
- `import dlt` in `adapters/ingestion/dlt/adapter.py` — correct, not a smell

**Test:** Are all provider imports isolated inside `src/pipelinekit/adapters/<type>/<provider>/adapter.py`?  
**Action:** Move the import. Never allow provider logic to leak into core.

---

### Smell 3 — Agent Boundary Violation

**Signal:** An agent modifies files outside its designated ownership.

**Agent ownership map:**
| Agent | Owns | Forbidden |
|---|---|---|
| cli-engineer | `src/pipelinekit/cli/`, `tests/cli/` | runtime, adapters, AI, state logic |
| runtime-engineer | `src/pipelinekit/runtime/`, `adapters/`, `contracts/` | CLI, AI layer |
| blueprint-engineer | `src/pipelinekit/blueprints/`, `blueprints/` | runtime, adapters, CLI internals |
| diagnostics-engineer | `src/pipelinekit/ai/`, `src/pipelinekit/diagnostics/` | contracts, runtime, adapters |
| release-engineer | `.github/workflows/`, `pyproject.toml` versioning | source code, tests |
| quality-engineer | `tests/` | source code, contracts, schemas |
| documentation-engineer | `docs/` (post-implementation only) | any source code |

**Test:** Does the PR touch files outside the active agent's ownership?  
**Action:** Refactor. Each agent owns its territory. If a change requires crossing a boundary, it is a sign the boundary needs a deliberate decision, not a workaround.

---

### Smell 4 — Specification Drift

**Signal:** Implementation diverges from the authoritative SPEC without the SPEC being updated.

**Examples:**
- SPEC-002 shows `cwd: Path = Path.cwd()` but implementation uses `cwd: Path | None = None` — drift
- SPEC-003 describes 3 lifecycle steps but runner has 5 — drift
- A new error code exists in code but not in `docs/reference/Error-Codes.md` — drift

**Test:** Does every implementation decision trace to a current SPEC? Does every SPEC accurately describe the current implementation?  
**Action:** Update the SPEC before the PR merges. Never let code and SPEC diverge.

---

### Smell 5 — Contract Version Bump Missing

**Signal:** A contract file (`contracts/*.yaml`) changes without a version increment.

**Test:** Was `version:` incremented when the contract changed?  
**Action:** Every contract change requires a version bump. Callers depend on contract stability. Silent changes break trust.

---

### Smell 6 — Prompt-Driven Architecture

**Signal:** An architectural decision originates from a Claude Code suggestion or a sprint prompt rather than from a Constitution, ADR, or SPEC.

**Examples:**
- Claude Code suggests adding a caching layer → accepted without ADR — smell
- Sprint prompt adds a new CLI command not in CLI-Commands.md — smell
- Claude Chat suggests a new module structure → accepted without updating master architecture — smell

**Test:** Is the decision recorded in a version-controlled document before implementation?  
**Action:** Stop. Write the ADR. Update the SPEC. Then implement.

---

### Smell 7 — MCP Without ADR

**Signal:** A new MCP server is added to `.mcp/registry/servers.md` or used in production without an approved ADR.

**Authorized MCPs (current):**
- Resend — ADR implicit in Phase 3 design (formalize as ADR-013)
- Full AI provider MCP layer — Phase 4, requires ADR-014

**Every other MCP requires an ADR before activation.**

**Test:** Does a new MCP have an approved ADR?  
**Action:** Write ADR-0NN before the MCP is registered or used.

---

### Smell 8 — Single-Implementation Abstraction

**Signal:** A new abstraction exists for only a single concrete implementation with no realistic prospect of a second.

**Examples:**
- `SnowflakeLoader` (instead of `WarehouseAdapter`) — smell
- `PostgresBlueprint` (instead of `Blueprint interface`) — smell
- `OpenAIDiagnostics` (instead of `LLMProvider`) — smell

**Rule:** Generalize one level. Never five.

**Test:** Does this abstraction serve at least two concrete implementations, or is there a realistic roadmap to a second?  
**Action:** If no second implementation is plausible — use a concrete class. If two exist — build the interface. Never generalize speculatively beyond one level.

---

### Smell 9 — Placeholder Inflation

**Signal:** Files exist in the repo with no content, no status, and no clear activation gate.

**Required status header for every file:**

```
Status: Placeholder | Draft | Approved | Implemented | Deprecated
```

**Test:** Does every file in `docs/specifications/`, `docs/decisions/`, and `docs/institutional-memory/` have a status header?  
**Action:** Every placeholder must have an explicit status and a condition for promotion. Empty files with no gate are noise.

---

### Smell 10 — Customer Capability Absent

**Signal:** A sprint delivers technical work but no new customer-facing capability.

**Test:** What can a customer do after this sprint that they could not do before?

Valid answers per phase:
- Phase 1: Initialize and validate a project
- Phase 2: Run a pipeline and validate contracts
- Phase 3: Deploy Blueprint #001 and receive failure alerts
- Phase 4: Diagnose pipeline failures without manual investigation

**Action:** If the answer is "nothing new for the customer" — the sprint is polishing infrastructure. Reduce scope or add a customer capability before shipping.

---

### Smell 11 — Capability Creep

**Signal:** A proposed feature sounds reasonable but expands PipelineKit toward a category it is explicitly not.

**Boundary test — PipelineKit is NOT:**
- A BI dashboard
- A hosted cloud platform
- A general AI chatbot
- A notebook platform
- A data warehouse
- A workflow scheduler replacement
- A Kubernetes platform
- A general-purpose MCP aggregator

**Feature test:** Does this make PipelineKit a better AI-native operating system for trusted analytics pipelines?

If the answer is not obvious — do not build it.

**Action:** Reject the feature or write an ADR that explicitly argues for expanding the boundary. ADR expansion requires founder approval.

---

### Smell 12 — Trust Regression

**Signal:** A proposed change reduces the trustworthiness, explainability, determinism, or observability of the system.

**Examples:**
- Removing structured error codes and replacing with free-form strings — regression
- Allowing AI to modify production data automatically — regression
- Removing contract validation from the run lifecycle — regression
- Introducing non-deterministic behavior in pipeline execution — regression

**Test:** Does this change improve or maintain trust, reliability, explainability, and diagnosability?  
**Action:** If it reduces any of these — reject or redesign.

---

## Pre-Flight Evaluation Protocol

Before any sprint prompt is sent to Claude Code, the Command Center evaluates the proposed work against this checklist:

```
Smell 1  — Untraceable Feature          □ traceable through full chain
Smell 2  — Concrete Provider Leak       □ all provider imports isolated
Smell 3  — Agent Boundary Violation     □ ownership respected
Smell 4  — Specification Drift          □ SPECs match implementation
Smell 5  — Contract Version Missing     □ contract versions bumped
Smell 6  — Prompt-Driven Architecture   □ decision in version control
Smell 7  — MCP Without ADR             □ MCP has approved ADR
Smell 8  — Single-Implementation Abs.  □ abstraction serves 2+ impls
Smell 9  — Placeholder Inflation        □ all files have status headers
Smell 10 — Customer Capability Absent   □ customer gains something
Smell 11 — Capability Creep             □ stays within product boundary
Smell 12 — Trust Regression             □ trust improves or holds
```

All 12 must pass before the sprint prompt is sent.
Any failure triggers a pause and a deliberate decision.
Decisions that override a smell go through an ADR.

---

## When to Add a New Smell

A new smell is added when:
- A recurring architectural mistake is observed across sprints
- A near-miss is caught that is not covered by existing smells
- A post-mortem identifies a pattern worth preventing

New smells require Command Center review and a commit to this file.
Smells are never added speculatively — only from observed evidence.
