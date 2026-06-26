# PipelineKit — Sprint 6-6 Session Opener
## Remote Blueprint Registry

You are Claude Code working inside the PipelineKit repository.

## Repository

```
C:\Users\HP\Documents\pipelinekit
```

## Read First

```
1. .claude/CLAUDE.md
2. docs/reference/PROJECT-STATUS.md
3. docs/decisions/ADR-019-Remote-Blueprint-Registry.md    ← Read completely
4. docs/specifications/SPEC-016-Remote-Blueprint-Registry.md  ← Primary SPEC
5. docs/specifications/SPEC-006-Blueprint-Engine.md
6. src/pipelinekit/blueprints/registry.py                ← You extend this
7. src/pipelinekit/cli/blueprint.py                      ← You add commands
8. docs/reference/Architectural-Smells.md                ← Smell 15 + 16
```

## Confirm Your Understanding Of

1. What the registry catalog structure looks like and where it is hosted
2. The trust model — what validation runs before any blueprint is written
3. The proposal flywheel — how installed blueprints improve AI proposals
4. What `PK-REGISTRY-002` means and when it fires
5. What must never be touched

Confirm when ready.

---

# Sprint 6-6 Implementation Prompt
## Remote Blueprint Registry

## Your Identity

blueprint-engineer + release-engineer

Primary ADR: `docs/decisions/ADR-019-Remote-Blueprint-Registry.md`  
Primary SPEC: `docs/specifications/SPEC-016-Remote-Blueprint-Registry.md`

## Sprint Goal

```powershell
poetry run pipelinekit blueprint search stripe
poetry run pipelinekit blueprint install stripe-to-snowflake
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

All 256 prior tests must pass.

## Files You Are Allowed To Create

```
src/pipelinekit/blueprints/remote.py    RemoteRegistry, BlueprintCatalog, CatalogEntry
tests/blueprints/test_remote_registry.py
```

You may also modify:
```
src/pipelinekit/cli/blueprint.py        Add search, install commands
src/pipelinekit/state/db.py             Add installed_blueprints table
src/pipelinekit/core/errors.py          Add RegistryError
docs/reference/Error-Codes.md          Add PK-REGISTRY-001 to 005
```

## Files You Must Not Modify

```
docs/reference/PROJECT-STATUS.md       ← NEVER
blueprints/                            ← READ ONLY
schemas/                               ← READ ONLY
All existing test files                ← READ ONLY
src/pipelinekit/blueprints/registry.py ← READ ONLY (you import from it)
src/pipelinekit/blueprints/validator.py ← READ ONLY (you use it)
```

## Registry Constants

```python
REGISTRY_BASE_URL = "https://registry.pipelinekit.dev/v1"
CATALOG_URL = f"{REGISTRY_BASE_URL}/catalog.json"
CATALOG_CACHE_TTL_HOURS = 24
```

## Implementation Requirements

See SPEC-016 for full data models and method signatures. Key constraints:

**Validation before write (ADR-019):**
1. Download zip → temp directory
2. Validate `blueprint.json` against `schemas/blueprint.schema.json`
3. Verify all 8 required asset directories present
4. Only then write to `blueprints/<name>/`

**Offline graceful degradation:**
If registry unreachable AND cache exists → use cache with warning.
If registry unreachable AND no cache → `PK-REGISTRY-001` with clear message.

**All network calls mocked in tests.**

## Definition of Done

```
✓ pipelinekit blueprint search <query> works
✓ pipelinekit blueprint install <name> downloads, validates, writes
✓ Validation before write enforced
✓ Catalog cached 24 hours
✓ Offline graceful degradation
✓ installed_blueprints table in state.db
✓ All 256 prior tests pass
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
```

## Commit Message

```
feat: Sprint 6-6 — Remote Blueprint Registry

- src/pipelinekit/blueprints/remote.py — RemoteRegistry, BlueprintCatalog
- pipelinekit blueprint search / install commands
- state/db.py — installed_blueprints table
- core/errors.py — RegistryError (PK-REGISTRY-001 to 005)

ADR-019 satisfied. Blueprints installable from registry.pipelinekit.dev.
Schema validation before write. Proposal flywheel enabled.
```
