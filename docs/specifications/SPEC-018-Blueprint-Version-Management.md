# SPEC-018-Blueprint-Version-Management.md

**Status:** Approved  
**Owner:** blueprint-engineer  
**Phase:** 7 — Sprint 7-B  
**Date:** June 26, 2026  
**ADRs:** ADR-019 (Registry Governance), ADR-008 (Deterministic Before AI)  
**Depends on:** SPEC-016 (Remote Blueprint Registry — Sprint 6-6)

---

## Purpose

Sprint 6-6 delivered blueprint search and install. Sprint 7-A proved the distribution lifecycle works end to end. The missing piece is version awareness — knowing what is installed, what is outdated, and how to upgrade safely.

This completes the package manager model:

```
install   → first acquisition
verify    → trust
list      → inventory
outdated  → governance  ← this sprint
upgrade   → lifecycle management  ← this sprint
```

Without `outdated` and `upgrade`, PipelineKit is a blueprint installer.  
With them, PipelineKit is a blueprint package manager.

---

## New Commands

### pipelinekit blueprint outdated

```
pipelinekit blueprint outdated [--json]
```

Compares installed blueprint versions against the remote registry catalog.

**Output:**
```
Blueprint Version Status
────────────────────────────────────────────────────────
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Blueprint             ┃ Installed ┃ Registry ┃ Status               ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ postgres-to-snowflake │ 1.0.0     │ 1.1.0    │ ⚠ Update available  │
│ salesforce-to-snowflake│ 1.0.0    │ 1.0.0    │ ✓ Up to date        │
│ stripe-to-snowflake   │ 1.0.0     │ 1.0.0    │ ✓ Up to date        │
└───────────────────────┴───────────┴──────────┴──────────────────────┘

1 blueprint(s) can be upgraded.
Run: pipelinekit blueprint upgrade postgres-to-snowflake
```

**When all are current:**
```
All blueprints are up to date.
```

**`--json` flag output:**
```json
{
  "checked_at": "2026-06-26T21:00:00Z",
  "blueprints": [
    {
      "name": "postgres-to-snowflake",
      "installed_version": "1.0.0",
      "registry_version": "1.1.0",
      "outdated": true
    }
  ]
}
```

---

### pipelinekit blueprint upgrade

```
pipelinekit blueprint upgrade <name> [--dry-run] [--yes]
```

Upgrades a blueprint to the latest registry version.

**Output (with changelog):**
```
Upgrading postgres-to-snowflake 1.0.0 → 1.1.0...

Changes in 1.1.0:
  • Improved contracts — added freshness SLA to orders.yaml
  • Added Soda quality pack — row count anomaly detection
  • Fixed dbt macro — stg_orders now handles NULL amounts

  ✓ Downloaded archive (201.4 KB)
  ✓ Validated blueprint schema
  ✓ Verified required assets
  ✓ Backed up existing blueprint to .pipelinekit/backups/postgres-to-snowflake-1.0.0/
  ✓ Written to blueprints/postgres-to-snowflake/

postgres-to-snowflake upgraded to v1.1.0. ✓ Verified blueprint.
Previous version backed up to .pipelinekit/backups/postgres-to-snowflake-1.0.0/
Rollback: pipelinekit blueprint rollback postgres-to-snowflake
```

**`--dry-run` flag:**
```
Would upgrade postgres-to-snowflake 1.0.0 → 1.1.0
No files written.
```

**`--yes` flag:** Skip confirmation prompt, apply immediately.

---

### pipelinekit blueprint rollback

```
pipelinekit blueprint rollback <name> [--version <version>]
```

Restores a blueprint from the local backup created during upgrade.

**Output:**
```
Rolling back postgres-to-snowflake to 1.0.0...
  ✓ Restored from .pipelinekit/backups/postgres-to-snowflake-1.0.0/
postgres-to-snowflake rolled back to v1.0.0.
```

---

## Implementation

### Modified files

```
src/pipelinekit/blueprints/remote.py      Add outdated(), upgrade(), rollback()
src/pipelinekit/cli/blueprint.py          Add outdated, upgrade, rollback commands
src/pipelinekit/state/db.py              Add blueprint_versions table
docs/reference/Error-Codes.md           Add PK-REGISTRY-006, 007
```

---

### RemoteRegistry additions

```python
def outdated(
    self,
    cwd: Path | None = None,
) -> list[dict]:
    """
    Compare installed blueprints against registry catalog.
    Returns list of {name, installed_version, registry_version, outdated}.
    Uses installed_blueprints table from state.db.
    Uses cached catalog (respects 24h TTL).
    """

def upgrade(
    self,
    name: str,
    dry_run: bool = False,
    yes: bool = False,
    cwd: Path | None = None,
) -> str:
    """
    Upgrade blueprint to latest registry version.
    1. Check if upgrade available — raise PK-REGISTRY-006 if already current
    2. Show changelog from catalog entry
    3. Prompt for confirmation (unless --yes)
    4. Backup existing blueprint to .pipelinekit/backups/<name>-<version>/
    5. Download new version
    6. Validate schema + 8 assets
    7. Write to blueprints/<name>/
    8. Update installed_blueprints table
    Returns new version string.
    """

def rollback(
    self,
    name: str,
    version: str | None = None,
    cwd: Path | None = None,
) -> str:
    """
    Restore blueprint from backup.
    Raises PK-REGISTRY-007 if no backup found.
    Returns restored version string.
    """
```

---

### Catalog schema extension

Add `changelog` field to catalog entries — shown during upgrade:

```json
{
  "name": "postgres-to-snowflake",
  "version": "1.1.0",
  "changelog": {
    "1.1.0": [
      "Improved contracts — added freshness SLA to orders.yaml",
      "Added Soda quality pack — row count anomaly detection",
      "Fixed dbt macro — stg_orders now handles NULL amounts"
    ],
    "1.0.0": [
      "Initial release — locally verified 2026-06-26"
    ]
  }
}
```

---

### State extension

```sql
-- blueprint_versions tracks upgrade history
CREATE TABLE IF NOT EXISTS blueprint_versions (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    from_version TEXT,
    to_version   TEXT NOT NULL,
    action       TEXT NOT NULL,  -- 'install' | 'upgrade' | 'rollback'
    backup_path  TEXT,
    applied_at   TEXT NOT NULL
);
```

---

### Error codes

| Code | Meaning |
|---|---|
| `PK-REGISTRY-006` | Blueprint already at latest version |
| `PK-REGISTRY-007` | No backup found for rollback |

---

## Test Requirements

All 289 prior tests must pass. New tests mock registry calls.

**tests/blueprints/test_version_management.py** — 6 tests:
- `outdated()` returns correct comparison against mocked catalog
- `outdated()` returns empty list when all current
- `upgrade()` backs up existing blueprint before writing new version
- `upgrade()` raises `PK-REGISTRY-006` when already at latest
- `upgrade(dry_run=True)` writes nothing to filesystem
- `rollback()` raises `PK-REGISTRY-007` when no backup exists

---

## Definition of Done

```
✓ pipelinekit blueprint outdated shows installed vs registry versions
✓ pipelinekit blueprint upgrade downloads, backs up, validates, writes
✓ pipelinekit blueprint upgrade --dry-run writes nothing
✓ pipelinekit blueprint rollback restores from backup
✓ Changelog shown during upgrade from catalog entry
✓ blueprint_versions table in state.db
✓ All 289 prior tests pass
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
```

---

## Commit Message

```
feat: Sprint 7-B — Blueprint version management (outdated/upgrade/rollback)

- RemoteRegistry.outdated() — compare installed vs registry versions
- RemoteRegistry.upgrade() — safe upgrade with backup + changelog
- RemoteRegistry.rollback() — restore from backup
- pipelinekit blueprint outdated / upgrade / rollback commands
- blueprint_versions table in state.db
- PK-REGISTRY-006, 007 error codes

Completes the blueprint package manager model:
install → verify → list → outdated → upgrade → rollback
```
