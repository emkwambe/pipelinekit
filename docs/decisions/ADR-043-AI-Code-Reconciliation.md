# ADR-043 — AI Capability Code Reconciliation

**Date:** July 24, 2026
**Status:** Accepted
**Author:** Eddy Mkwambe + Command Center
**Type:** Architectural correction — no code changes required
**Priority:** Critical — must execute before any further AI domain work

---

## Context

During Phase 3 sprint execution (July 2026), three capabilities were built
and assigned the codes AI-7, AI-8, and AI-9. At the time of assignment,
the EMS-CAPABILITY-TAXONOMY.md was not consulted for those specific codes.

The taxonomy defines:
```
AI-7   Prompt Governance          — structured prompt versioning,
                                    template library, injection controls
AI-8   Agent Registry             — register, version, and route AI agents
                                    used in the pipeline lifecycle
AI-9   Evaluation Pipeline        — automated quality evaluation of AI
                                    outputs before they reach engineers
```

What was actually built under those codes:
```
AI-7   EMS Context Injection      — inject EMS operational signals
                                    (QM-8, OM-4, QM-6, QM-7, DC-10)
                                    into DiagnosticsEngine prompts
AI-8   Scorecard Narrative        — AI-generated explanation of the
                                    QM-8 quality scorecard via --narrative
AI-9   Confidence Recalibration   — EMS-aware adjustment of base
                                    confidence scores using operational
                                    signals from state.db
```

All three built capabilities are genuinely valuable and correctly
implemented. The problem is labeling, not code. The taxonomy codes AI-7,
AI-8, and AI-9 now appear to be "done" when in fact three different
capabilities occupy those slots — leaving six engineers who read the
taxonomy believing Prompt Governance, Agent Registry, and Evaluation
Pipeline are built when they are not.

This creates three compounding problems:

1. **Roadmap integrity:** Future AI capabilities (AI-10 Hallucination
   Monitoring, AI-12 Fine-Tuned Model Management) have a broken
   dependency chain. AI-10 depends on AI-9 Evaluation Pipeline. The
   built AI-9 (Confidence Recalibration) is not the Evaluation Pipeline.
   Building AI-10 on top of it would be building on the wrong foundation.

2. **Design partner trust:** An engineer who reads the capability taxonomy
   and sees AI-7 "Prompt Governance" will expect to find versioned prompt
   templates and injection controls in the CLI. They do not exist. This is
   a broken promise in the documentation.

3. **Grant and investor narrative:** The EMS capability count includes
   three capabilities that are present in code but absent in the strategic
   taxonomy — inflating the apparent coverage while hiding three genuine
   gaps.

---

## Decision

Renumber the three built capabilities to new codes beyond the current
taxonomy sequence. Preserve the original AI-7, AI-8, AI-9 codes for
their taxonomy-defined capabilities.

**New assignments:**

```
AI-13   EMS Context Injection
        Module: src/pipelinekit/ai/ems_context.py
        Commit: ae2c11f
        Tests: tests/ai/test_ai7_ems_context.py (rename to test_ai13_)

AI-14   Quality Scorecard Narrative
        Module: src/pipelinekit/ai/narrative.py
        Commit: bb4e065
        Tests: tests/ai/test_ai8_narrative.py (rename to test_ai14_)

AI-15   EMS-Aware Confidence Recalibration
        Module: src/pipelinekit/ai/confidence.py
        Commit: f4e194b
        Tests: tests/ai/test_ai9_confidence.py (rename to test_ai15_)
```

**Preserved for original taxonomy intent:**

```
AI-7    Prompt Governance          — status: planned, Phase 4
AI-8    Agent Registry             — status: planned, Phase 4
AI-9    Evaluation Pipeline        — status: planned, Phase 4
```

---

## What changes

### Files to rename (test files only — no logic changes)
```
tests/ai/test_ai7_ems_context.py  → tests/ai/test_ai13_ems_context.py
tests/ai/test_ai8_narrative.py    → tests/ai/test_ai14_narrative.py
tests/ai/test_ai9_confidence.py   → tests/ai/test_ai15_confidence.py
```

### SPEC references to update
```
SPEC-032 (AI-7 EMS Context)       → rename to SPEC-040 (AI-13)
SPEC-033 (AI-8 Narrative)         → rename to SPEC-041 (AI-14)
SPEC-039 (AI-9 Confidence)        → rename to SPEC-042 (AI-15)
```

### Documentation to update
```
docs/reference/EMS-STATUS.md      → move AI-7/8/9 from ✅ to planned
                                    add AI-13/14/15 as ✅ Phase 3
CHANGELOG.md                      → update Sprint 15/16/22 entries
                                    to reference AI-13/14/15
docs/guides/CLI-REFERENCE.md      → update AI provider section
                                    to reference AI-13/14/15
```

### Internal private repo
```
pipelinekit-internal/reference/   → rename CLAUDE-CODE-PROMPT-AI7-FULL.md
                                    to CLAUDE-CODE-PROMPT-AI13-FULL.md
                                    etc.
AI-NATIVE-DEVELOPMENT-FRAMEWORK.md → update any AI-7/8/9 references
```

### Source modules — NO CHANGES REQUIRED
The Python module names (ems_context.py, narrative.py, confidence.py)
do not encode the capability code. The code inside them does not need
to change. The renumbering is documentation and test file naming only.

---

## What does NOT change

- The capabilities themselves — all three are correctly built and working
- The module names (ems_context.py, narrative.py, confidence.py)
- The function names and APIs
- The state.db schema
- The CLI command surface
- The 502 passing tests (after test file renames)

---

## Phase numbering unification

As part of this reconciliation, the phase vocabulary in all docs should
align with EMS-BUILD-SEQUENCE.md Phase 1-6, not the internal "Phase 2 /
Phase 3" labels used during sprint execution.

Mapping:
```
Internal "v0.1.0 / Phase 1"  → Strategy Phase 1 (Foundation)
Internal "Phase 2" (sprints 1-12) → Strategy Phase 2 (Core EMS)
Internal "Phase 3" (sprints 13-22) → Strategy Phase 2-3 (AI + expansion)
```

EMS-STATUS.md should be updated to use Strategy Phase labels.

---

## AI domain status after reconciliation

```
AI-1   Provider Abstraction          ✅ Phase 1
AI-2   Blueprint Generation          ✅ Phase 1
AI-3   Diagnostics Engine            ✅ Phase 1
AI-4   Confidence Scoring            ✅ Phase 1
AI-5   AI Trust Model                ✅ Phase 1
AI-6   Multi-Provider Routing        ✅ Phase 1 (+ cascade added Phase 3)
AI-7   Prompt Governance             📋 Planned — Phase 4
AI-8   Agent Registry                📋 Planned — Phase 4
AI-9   Evaluation Pipeline           📋 Planned — Phase 4
AI-10  Hallucination Monitoring      📋 Planned — Phase 4
AI-11  AI Acceptance Tracking        📋 Planned — Phase 2
AI-12  Fine-Tuned Model Management   📋 Planned — Phase 5
AI-13  EMS Context Injection         ✅ Phase 3 (was mislabeled AI-7)
AI-14  Quality Scorecard Narrative   ✅ Phase 3 (was mislabeled AI-8)
AI-15  EMS-Aware Confidence          ✅ Phase 3 (was mislabeled AI-9)
```

---

## Consequences

**Positive:**
- Roadmap is honest — AI-7/8/9 appear as genuinely unbuilt
- AI-10 dependency chain (on real AI-9 Evaluation Pipeline) is preserved
- Design partners reading taxonomy get accurate expectations
- Grant/investor narrative reflects true capability coverage
- Future AI sprints build on correct foundations

**Negative:**
- Test file renames require a commit
- CHANGELOG entries reference old codes — need updating
- Internal memory and private repo docs need updating
- 502 tests must still pass after renames (regression risk: low)

**Neutral:**
- No customer-visible CLI changes
- No state.db changes
- No module logic changes

---

## Implementation sprint

See CLAUDE-CODE-PROMPT-AI-RECONCILIATION.md for the Claude Code
execution prompt. This is a documentation and test-rename sprint only.
Estimated: 1 hour, 1 commit.

Commit message:
```
fix: AI capability code reconciliation — AI-7/8/9 reserved for taxonomy,
     built capabilities renumbered to AI-13/14/15
```
