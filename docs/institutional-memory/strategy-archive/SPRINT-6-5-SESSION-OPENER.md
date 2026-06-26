# PipelineKit — Sprint 6-5 Session Opener v2
## AI Blueprint Proposal

You are Claude Code working inside the PipelineKit repository.

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

## Read First — In This Exact Order

```
1.  .claude/CLAUDE.md
2.  docs/reference/PROJECT-STATUS.md
3.  docs/decisions/ADR-018-Blueprint-Proposal-Governance.md   ← Read completely
4.  docs/decisions/ADR-007-* (AI is Operator not Owner)
5.  docs/specifications/SPEC-015-AI-Blueprint-Proposal.md     ← Primary SPEC
6.  docs/specifications/SPEC-005-AI-Diagnostics.md            ← LLMProvider pattern
7.  src/pipelinekit/ai/provider.py                            ← You extend this
8.  blueprints/postgres-to-snowflake/                         ← Pattern source
9.  blueprints/salesforce-to-snowflake/                       ← Pattern source
10. schemas/blueprint.schema.json                             ← Proposal must satisfy
11. docs/reference/Architectural-Smells.md                    ← Smell 13 + 15
```

## Naming — Read This First

This sprint is called **AI Blueprint Proposal**, not AI Blueprint Generation.

The architectural phrase is:
> PipelineKit proposes blueprint artifacts. Humans approve what becomes part of the repository.

Every class, method, and command uses "propose/proposal" not "generate/generation".
Exception: the CLI command is `pipelinekit generate blueprint` (user-facing verb).
Internally: `BlueprintProposer`, `BlueprintProposal`, `ProposedAsset`, `propose_blueprint()`.

## Confirm Your Understanding Of

1. **The state machine** — what are the 6 valid asset states and what transitions are allowed vs forbidden?
2. **The command model** — what does `--plan` do vs `--interactive`? When does anything touch the filesystem?
3. **The AdapterCapabilityRegistry** — what does it prevent and why must it be checked before any AI call?
4. **Provenance metadata** — what 8 fields does every asset carry, and what happens to them on write?
5. **Smell 13 extended** — how does "Observer Becomes Actor" apply to a proposal system?
6. **What must never be touched**

Confirm when ready. Do not write any code until confirmation is complete.
