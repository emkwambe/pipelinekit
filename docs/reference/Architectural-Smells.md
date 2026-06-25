# PipelineKit — Architectural Smells

**File:** `docs/reference/Architectural-Smells.md`  
**Owner:** Command Center (Claude Chat)  
**Purpose:** Pre-flight checklist evaluated before any new capability, dependency, or structural change is approved.  
**Rule:** Claude Chat evaluates every proposed change against this list before Claude Code writes a single line.  
**Version:** 2.0 — directional guidance added to all smells

---

## What Is an Architectural Smell?

An architectural smell is a signal that a proposed change — even if technically correct — is moving the system away from its governing principle.

Smells do not automatically block work. They trigger a pause, a question, and a deliberate decision. If the decision is to proceed, it goes through an ADR. If no ADR exists yet, the ADR is written first.

**The governing principle that every smell traces back to:**

> PipelineKit is the AI-native operating system for trusted analytics pipelines.

---

## How to Use This Document

Each smell has four parts:

- **Signal** — how to recognize it
- **Test** — the question to ask
- **Direction** — which way to move when the smell fires
- **Action** — the concrete next step

The Direction is the most important part. Detecting a smell is easy. Knowing which way to walk is what matters.

---

## The Smell Checklist

Evaluate every proposed feature, dependency, MCP, or structural change against all 15 smells before approving.

---

### Smell 1 — Untraceable Feature

**Signal:** A proposed feature cannot be traced cleanly through:

```
Governing Principle → Constitution → ADR → Specification → Contract → Schema → Implementation → Tests
```

Any broken link in this chain is a smell.

**Test:** Can you name the ADR and SPEC that authorize this feature?

**Direction:** Move toward the chain, not around it. The instinct when a feature feels obviously right is to skip the documentation and just build it. Resist that instinct. The chain exists because "obviously right" features have a habit of quietly contradicting each other six weeks later. Write the ADR first — it takes 20 minutes and saves days.

**Action:** If no ADR exists → write it. If no SPEC exists → write it. If neither can be justified → do not build the feature. The chain is not bureaucracy. It is the memory of the project.

---

### Smell 2 — Concrete Provider Dependency

**Signal:** A module imports or directly depends on a concrete provider (dlt, dbt, Soda, Resend, OpenAI, Anthropic) outside its designated adapter file.

**Test:** Are all provider imports isolated inside `src/pipelinekit/adapters/<type>/<provider>/adapter.py`?

**Direction:** Move toward the interface, away from the vendor. The adapter boundary is what makes PipelineKit replaceable. Every time a vendor import leaks into the runtime or CLI, PipelineKit becomes harder to maintain, harder to test, and harder to migrate. The short-term convenience of a direct import costs compounding long-term debt.

The correct direction is always: if you need provider behavior, define it as a method on `BaseAdapter` and call that method. The concrete adapter implements it. The rest of the system never knows which vendor is underneath.

**Action:** Move the import. If the method doesn't exist on `BaseAdapter` yet — add it there first, then implement in the adapter. Never skip the interface.

---

### Smell 3 — Agent Boundary Violation

**Signal:** An agent modifies files outside its designated ownership.

**Agent ownership map:**
| Agent | Owns | Never Touches |
|---|---|---|
| cli-engineer | `src/pipelinekit/cli/`, `tests/cli/` | runtime, adapters, AI, state logic |
| runtime-engineer | `src/pipelinekit/runtime/`, `adapters/`, `contracts/` | CLI layer, AI layer |
| blueprint-engineer | `src/pipelinekit/blueprints/`, `blueprints/` | runtime internals, adapters, CLI |
| diagnostics-engineer | `src/pipelinekit/ai/`, `src/pipelinekit/diagnostics/` | contracts, runtime, adapters |
| release-engineer | `.github/workflows/`, `pyproject.toml` versioning | source code, tests |
| quality-engineer | `tests/` | source code, contracts, schemas |
| documentation-engineer | `docs/` (post-implementation only) | any source code, any spec |

**Test:** Does the PR touch files outside the active agent's ownership?

**Direction:** Move toward explicit handoffs, not silent crossings. When a feature genuinely requires two agents — for example, a new runtime capability that also needs a new CLI command — the correct direction is to complete the runtime work first, commit it, then open a new prompt for the CLI engineer to build the command on top of it. Sequential, clean, traceable. Never simultaneous and tangled.

**Action:** Refactor the PR to respect boundaries. If a capability genuinely spans two agents — sequence the work, don't merge the ownership.

---

### Smell 4 — Specification Drift

**Signal:** Implementation diverges from the authoritative SPEC without the SPEC being updated.

**Known existing drift (as of Phase 2):**
- SPEC-002 shows `cwd: Path = Path.cwd()` — implementation uses `cwd: Path | None = None`
- SPEC-003 describes 3 lifecycle steps — runner has 5
- PK-CONFIG-005 exists in code — not in Error-Codes.md at time of creation

**Test:** Does every implementation decision trace to a current SPEC? Does every SPEC accurately describe the current implementation?

**Direction:** Move toward the SPEC, not away from it. When implementation deviates from the SPEC — even for good reasons — the SPEC must be updated before the PR closes. The SPEC is what Claude Code reads at the start of every sprint. A stale SPEC means Claude Code is building on a false foundation. That compounds with every sprint.

The correct update order: implement → detect drift → update SPEC → commit both together.

**Action:** Update the SPEC in the same PR as the implementation change. Never merge drift. Add the change to the Decision Log in PROJECT-STATUS.

---

### Smell 5 — Contract Version Bump Missing

**Signal:** A contract file (`contracts/*.yaml`) changes without a version increment.

**Test:** Was `version:` incremented when the contract changed?

**Direction:** Move toward versioned stability, not silent mutation. Contracts are interfaces. Every system that depends on a contract deserves to know when it changed. A silent contract change is the data infrastructure equivalent of changing a function signature without updating its callers — except the callers might be production pipelines running at 2am.

**Action:** Increment the version field. Document the change in the contract file header. If the change is breaking — write a migration note.

---

### Smell 6 — Prompt-Driven Architecture

**Signal:** An architectural decision originates from a Claude Code suggestion or a sprint prompt rather than from a Constitution, ADR, or SPEC.

**Test:** Is the decision recorded in a version-controlled document before implementation?

**Direction:** Move toward documents, away from conversation. The danger here is subtle. Claude Code is genuinely helpful and its suggestions are often good. The problem is that good suggestions made in conversation are invisible to future sprints. Three months from now, nobody knows why a module is structured a certain way. The Constitution and ADRs are the memory. Conversations are not.

The correct direction: when Claude Code surfaces an architectural insight — treat it as a draft ADR, not as permission to implement. Bring it to the Command Center. Write the ADR. Commit it. Then implement.

**Action:** Stop implementation. Return the decision to Command Center. Write the ADR. Proceed only after the ADR is committed to main.

---

### Smell 7 — MCP Without ADR

**Signal:** A new MCP server is added to `.mcp/registry/servers.md` or used in production without an approved ADR.

**Authorized MCPs (current):**
- Resend — Phase 3, email alerts only (ADR-013 to be formalized)
- AI provider MCP layer — Phase 4 only (ADR-014 pending)

**Test:** Does a new MCP have an approved ADR?

**Direction:** Move toward minimum viable MCP surface, not maximum connectivity. Every MCP is a dependency. Every dependency is a failure mode, a security surface, and a maintenance burden. The instinct when discovering a useful MCP (GitHub MCP, Postgres MCP, Slack MCP) is to add it immediately. Resist.

The question is never "is this MCP useful?" It is always "does PipelineKit need this MCP to fulfill its governing principle, and what is the cost of adding it?"

**Action:** Write ADR-0NN before the MCP is registered or used. The ADR must justify the MCP against the governing principle. If the justification is weak — do not add the MCP.

---

### Smell 8 — Single-Implementation Abstraction

**Signal:** A new abstraction exists for only a single concrete implementation with no realistic prospect of a second.

**Test:** Does this abstraction serve at least two concrete implementations, or is there a realistic roadmap to a second?

**Direction:** Move toward the right level of abstraction — which is usually one level above the concrete case, not five. The failure mode here has two directions: under-abstraction (hardcoding Snowflake instead of building WarehouseAdapter) and over-abstraction (building a six-layer provider factory for a feature that will only ever have one provider). Both are smells. The correct direction is the middle: abstract when a second implementation is either present or clearly planned.

**Action:** If only one implementation exists and no second is planned — use a concrete class. If two exist or are planned — build the interface. Document the decision.

---

### Smell 9 — Placeholder Inflation

**Signal:** Files exist in the repo with no content, no status, and no clear activation gate.

**Required status header for every non-trivial file:**

```
Status: Placeholder | Draft | Approved | Implemented | Deprecated
```

**Test:** Does every file in `docs/specifications/`, `docs/decisions/`, and `docs/institutional-memory/` have a status header?

**Direction:** Move toward intentional placeholders, not accidental ones. A placeholder with a clear status and activation gate is useful — it signals intent and prevents premature work. A placeholder with no status is noise that erodes confidence in the repository. When a new contributor (human or AI) sees 40 empty files, they cannot distinguish signal from silence.

**Action:** Every placeholder must have status + activation condition. Example:
```
Status: Placeholder
Activation: When Phase 4 begins and SPEC-005 is approved
```
Empty files with no gate get populated or deleted.

---

### Smell 10 — Customer Capability Absent

**Signal:** A sprint delivers technical work but no new customer-facing capability.

**Test:** What can a customer do after this sprint that they could not do before?

**Valid answers by phase:**
- Phase 1: Initialize and validate a project configuration
- Phase 2: Run a pipeline, validate contracts, see structured failures
- Phase 3: Deploy Blueprint #001 end-to-end, receive failure alerts, push to CI
- Phase 4: Diagnose pipeline failures with AI-assisted root cause analysis

**Direction:** Move toward customer capability, not infrastructure polish. Infrastructure work is necessary but it must serve a customer outcome within a reasonable time horizon. If two consecutive sprints deliver only internal improvements — that is a signal that the product has become the engineering, not the customer.

The test is concrete: can a design partner use this? Can they point to it? Will they pay for it?

**Action:** If the answer is "no customer capability gained" — add one customer-facing deliverable to the sprint scope before firing Claude Code. If infrastructure genuinely requires a full sprint — name the customer capability it unblocks and when that unblocking will happen.

---

### Smell 11 — Capability Creep

**Signal:** A proposed feature sounds reasonable but expands PipelineKit toward a category it is explicitly not.

**Boundary — PipelineKit is NOT:**
- A BI dashboard
- A hosted cloud platform
- A general AI chatbot
- A notebook platform
- A data warehouse
- A workflow scheduler replacement
- A Kubernetes platform
- A general-purpose MCP aggregator

**Feature test:** Does this make PipelineKit a better AI-native operating system for trusted analytics pipelines?

**Direction:** Move toward the core, not the periphery. The pattern is always the same: a reasonable-sounding feature ("let's add a simple dashboard"), followed by another ("now we need auth for the dashboard"), followed by another ("the dashboard needs real-time updates"). Three steps later, PipelineKit is building Metabase. Each step felt justified. The direction was wrong from the first step.

When a feature feels like it belongs in PipelineKit but sits at the edge of the boundary — ask: is this making the analytics more trusted, or just more visible? Visibility is a BI problem. Trust is a PipelineKit problem.

**Action:** Reject the feature, or write an ADR that explicitly argues for boundary expansion with founder approval required.

---

### Smell 12 — Trust Regression

**Signal:** A proposed change reduces the trustworthiness, explainability, determinism, or observability of the system.

**Examples:**
- Removing structured PK error codes, replacing with free-form strings
- Allowing AI to modify production data automatically
- Removing contract validation from the run lifecycle
- Introducing non-deterministic behavior in pipeline execution
- Skipping state recording on pipeline runs
- Making evidence dicts in ContractViolation optional

**Test:** Does this change improve or maintain trust, reliability, explainability, and diagnosability?

**Direction:** Move toward more evidence, not less. PipelineKit's value proposition is trust. Every time the system produces less evidence, less structure, or less explainability — it is moving away from its own reason for existing. The short-term convenience of skipping a structured error or an evidence dict is a long-term erosion of what makes PipelineKit different from a bash script.

When facing a tradeoff between convenience and explainability — choose explainability. Always.

**Action:** Reject or redesign. No convenience trade is worth a trust regression.

---

### Smell 13 — Observer Becomes Actor (AI Safety)

**Signal:** AI is given the ability to modify, delete, deploy, or trigger production actions without explicit human approval at that moment.

**The approved AI boundary (from ADR-007):**

AI may: inspect, diagnose, recommend, summarize, classify, generate  
AI may not: deploy, delete, migrate, modify production, rotate secrets, approve releases

**Test:** Does this AI capability require human approval before any production action?

**Direction:** Move toward human-on-the-loop, not human-out-of-the-loop. The failure mode is gradual. Phase 4 starts with AI recommending fixes. Then "auto-fix" seems like a natural next step. Then "auto-fix with notification" feels safer than "auto-fix silently." None of these feel like large steps. Together they produce a system that modifies production data based on AI confidence scores.

PipelineKit's AI is a diagnostician, not a surgeon. It explains what is wrong and recommends what to do. A human holds the scalpel.

**Action:** Any AI capability that crosses this boundary requires an explicit ADR arguing for the exception. The ADR must explain the approval mechanism, the rollback plan, and the audit trail.

---

### Smell 14 — State Orphan

**Signal:** A pipeline operation completes — successfully or with failure — but leaves no record in `.pipelinekit/state.db`.

**Test:** Is every pipeline execution, validation run, contract check, and diagnostic result recorded in state?

**Direction:** Move toward complete state coverage, not selective recording. State is evidence. Evidence is what Phase 4 AI diagnostics reads. Evidence is what `pipelinekit doctor` displays. Evidence is what a support conversation references. A pipeline that runs and leaves no trace is a pipeline that cannot be debugged, audited, or trusted.

The `try/finally` pattern in `runner.py` exists precisely for this. The state update happens in the `finally` block — it cannot be skipped even on exception. Every new execution path must follow the same pattern.

**Action:** Audit the execution path. If state is not recorded — add the recording. If the recording can be bypassed by an exception — wrap it in `try/finally`.

---

### Smell 15 — Blueprint Shortcut

**Signal:** A blueprint ships without all required assets, substituting placeholder files or stub implementations for real ones.

**Required assets for every production blueprint:**
- `blueprint.json` — validates against `schemas/blueprint.schema.json`
- `ingestion/pipeline.py` — working dlt pipeline definition
- `transform/` — real dbt project with at least one staging and one core model
- `contracts/` — at least one real ContractDefinition YAML
- `quality/` — Soda checks
- `alerts/config.yaml` — notification configuration
- `docs/README.md` — prerequisites and installation steps
- `docs/runbook.md` — operational runbook with troubleshooting guide

**Test:** Does this blueprint deploy and produce trusted analytics in under 60 minutes on a clean machine?

**Direction:** Move toward production quality, not demo quality. The blueprint catalog is the long-term moat. Its value comes from being production-tested and complete. A blueprint with stub dbt models or empty contracts is not a blueprint — it is a template. Templates are not the product. Complete, tested, production-ready blueprints are the product.

The standard is: a data engineer who has never seen PipelineKit should be able to follow the runbook, deploy the blueprint, and have trusted analytics running within 60 minutes. If that is not achievable — the blueprint is not ready to ship.

**Action:** Complete all required assets before the blueprint is committed to main. No placeholder files in production blueprints.

---

## Pre-Flight Evaluation Protocol

Before any sprint prompt is sent to Claude Code, the Command Center evaluates the proposed work against this checklist:

```
Smell 1  — Untraceable Feature              □ traceable through full chain
Smell 2  — Concrete Provider Leak           □ all provider imports isolated
Smell 3  — Agent Boundary Violation         □ ownership respected
Smell 4  — Specification Drift              □ SPECs match implementation
Smell 5  — Contract Version Missing         □ contract versions bumped
Smell 6  — Prompt-Driven Architecture       □ decision in version control
Smell 7  — MCP Without ADR                 □ MCP has approved ADR
Smell 8  — Single-Implementation Abs.      □ abstraction serves 2+ impls
Smell 9  — Placeholder Inflation            □ all files have status headers
Smell 10 — Customer Capability Absent       □ customer gains something
Smell 11 — Capability Creep                 □ stays within product boundary
Smell 12 — Trust Regression                 □ trust improves or holds
Smell 13 — Observer Becomes Actor           □ AI stays in advisory role
Smell 14 — State Orphan                     □ all executions recorded
Smell 15 — Blueprint Shortcut               □ all required assets present
```

All 15 must pass before the sprint prompt is sent.  
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
Current count: 15 smells. Target: the minimum number that prevents the maximum damage.
