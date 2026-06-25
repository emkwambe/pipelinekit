# Pull Request

## Summary

<!--
One sentence: what does this PR deliver?
What customer capability became possible because of this work?
-->

-

## Traceability

<!--
Every change must trace through the full chain.
If any link is missing, add it before merging.
-->

| Link | Reference |
|---|---|
| Governing Principle | PipelineKit is the AI-native OS for trusted analytics pipelines |
| Constitution section | |
| ADR(s) | |
| SPEC(s) | |
| Contract(s) affected | |
| Schema(s) affected | |

## Specification Drift Check

<!--
These four questions are mandatory. Answer each one.
-->

- [ ] Did this PR invalidate or change the behavior described in any SPEC?
  - If yes — which SPEC was updated? _______________
- [ ] Did this PR invalidate or modify any Contract in `contracts/`?
  - If yes — was the contract version bumped? _______________
- [ ] Did this PR invalidate or modify any Schema in `schemas/`?
  - If yes — which schema was updated? _______________
- [ ] Did this PR introduce a new architectural decision not covered by an existing ADR?
  - If yes — which ADR was written? _______________

## Agent Boundary Check

- [ ] This PR only touches files owned by the active agent(s): _______________
- [ ] No provider imports exist outside `src/pipelinekit/adapters/`
- [ ] `docs/reference/PROJECT-STATUS.md` was not touched

## Architectural Smell Check

<!--
Evaluate against docs/reference/Architectural-Smells.md
-->

- [ ] Smell 1 — Feature traceable through full chain
- [ ] Smell 2 — No concrete provider leak outside adapters
- [ ] Smell 3 — Agent boundaries respected
- [ ] Smell 4 — No specification drift (or SPEC updated)
- [ ] Smell 8 — No single-implementation abstraction
- [ ] Smell 10 — Customer gains a capability (or this is explicitly infrastructure)
- [ ] Smell 11 — No capability creep beyond product boundary
- [ ] Smell 12 — Trust, determinism, explainability maintained

## Quality Gates

- [ ] `poetry run pytest --cov=src/pipelinekit --cov-fail-under=80` passes
- [ ] `poetry run ruff check .` passes
- [ ] `poetry run black --check .` passes
- [ ] `poetry run mypy src/pipelinekit` passes
- [ ] All pre-existing tests still pass (no regressions)

## Notes for Reviewer

<!--
Flag any decisions that deviated from the SPEC and why.
Flag any smell that was detected and how it was resolved.
Flag any new error codes added.
-->

-
