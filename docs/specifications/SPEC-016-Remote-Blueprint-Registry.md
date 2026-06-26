# SPEC-016-Remote-Blueprint-Registry.md

**Status:** Approved  
**Owner:** blueprint-engineer + release-engineer  
**Phase:** 6 — Sprint 6-6  
**Date:** June 26, 2026  
**ADRs:** ADR-019 (Registry Governance), ADR-005 (BYOK), ADR-008 (Deterministic)  
**Depends on:** SPEC-006 (Blueprint Engine), SPEC-015 (AI Blueprint Proposal)

---

## Purpose

Define the Remote Blueprint Registry — the distribution layer that makes blueprints installable from a curated catalog with one command.

```powershell
pipelinekit blueprint search stripe
pipelinekit blueprint install stripe-to-snowflake
pipelinekit blueprint install salesforce-to-snowflake --version 1.1.0
```

---

## New Files

```
src/pipelinekit/blueprints/
└── remote.py              RemoteRegistry, BlueprintCatalog, CatalogEntry

tests/blueprints/
└── test_remote_registry.py
```

## Modified Files

```
src/pipelinekit/cli/blueprint.py    Add search, install commands
docs/reference/Error-Codes.md      Add PK-REGISTRY-* codes
```

---

## Registry Constants

```python
# src/pipelinekit/blueprints/remote.py

REGISTRY_BASE_URL = "https://registry.pipelinekit.dev/v1"
CATALOG_URL = f"{REGISTRY_BASE_URL}/catalog.json"
CATALOG_CACHE_TTL_HOURS = 24
```

---

## Data Models

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class CatalogEntry:
    name: str
    version: str
    description: str
    source: str
    destination: str
    verified: bool
    verified_at: Optional[str]
    verified_by: Optional[str]
    downloads: int
    tags: list[str]
    url: str

@dataclass
class BlueprintCatalog:
    version: str
    updated_at: str
    blueprints: list[CatalogEntry]

    def search(self, query: str) -> list[CatalogEntry]:
        """Search by name, source, destination, or tag."""

    def get(self, name: str, version: str | None = None) -> Optional[CatalogEntry]:
        """Get a specific blueprint by name and optional version."""
```

---

## RemoteRegistry

```python
class RemoteRegistry:
    """Fetches, caches, and installs blueprints from the remote catalog.

    All installed blueprints are validated before writing to disk.
    ADR-019: schema validation + 8-asset check before any write.
    """

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path.home() / ".pipelinekit" / "cache"

    def fetch_catalog(self, force_refresh: bool = False) -> BlueprintCatalog:
        """
        Fetch catalog.json from registry.
        Cache for CATALOG_CACHE_TTL_HOURS hours.
        Raises RegistryError(PK-REGISTRY-001) if unreachable.
        Returns cached catalog if offline and cache exists.
        """

    def install(
        self,
        name: str,
        version: str | None = None,
        cwd: Path | None = None,
    ) -> str:
        """
        1. Fetch catalog and find blueprint
        2. Download zip archive
        3. Extract to temp directory
        4. Validate against blueprint.schema.json
        5. Verify all 8 required assets present
        6. Write to blueprints/<name>/
        7. Return installed version
        Raises RegistryError(PK-REGISTRY-002) on validation failure.
        Raises RegistryError(PK-REGISTRY-003) if blueprint already installed.
        """

    def search(self, query: str) -> list[CatalogEntry]:
        """Search catalog. Returns empty list if no matches."""

    def _download_archive(self, url: str) -> bytes:
        """Download blueprint zip archive."""

    def _validate_blueprint(self, extract_dir: Path) -> None:
        """
        Validate extracted blueprint:
        1. blueprint.json exists and validates against schema
        2. All 8 required asset directories/files present
        Raises RegistryError(PK-REGISTRY-002) on failure.
        """

    def _check_cache(self, ttl_hours: int) -> Optional[BlueprintCatalog]:
        """Return cached catalog if fresh, None otherwise."""

    def _write_cache(self, catalog: BlueprintCatalog) -> None:
        """Write catalog to cache."""
```

---

## CLI Commands

### pipelinekit blueprint search

```python
@blueprint_app.command("search")
def search_command(
    query: str = typer.Argument(..., help="Search term: source, destination, or name"),
    verified_only: bool = typer.Option(False, "--verified", help="Show only verified blueprints"),
):
    """Search the remote blueprint registry."""
```

**Output:**
```
Blueprint Registry Search: "stripe"
────────────────────────────────────

  Name                    Version  Source    Destination  Verified
  ──────────────────────  ───────  ────────  ───────────  ────────
  stripe-to-snowflake     1.0.0    stripe    snowflake    ✓
  stripe-to-bigquery      1.0.0    stripe    bigquery     ✓

2 blueprints found. Install with: pipelinekit blueprint install <name>
```

### pipelinekit blueprint install

```python
@blueprint_app.command("install")
def install_command(
    name: str = typer.Argument(...),
    version: str = typer.Option(None, "--version", "-v"),
    force: bool = typer.Option(False, "--force", help="Overwrite if already installed"),
):
    """Install a blueprint from the registry."""
```

**Output:**
```
Installing stripe-to-snowflake v1.0.0...
  ✓ Downloaded archive (24.3 KB)
  ✓ Validated blueprint schema
  ✓ Verified 8 required assets
  ✓ Written to blueprints/stripe-to-snowflake/

stripe-to-snowflake v1.0.0 installed. ✓ Verified blueprint.
Run 'pipelinekit blueprint info stripe-to-snowflake' for details.
```

**Unverified warning:**
```
⚠ This blueprint has not been verified by the Mpingo Systems team.
  Review all assets carefully before deploying to production.
```

---

## Error Codes

| Code | Meaning |
|---|---|
| `PK-REGISTRY-001` | Registry unreachable — network error |
| `PK-REGISTRY-002` | Blueprint validation failed — schema or missing assets |
| `PK-REGISTRY-003` | Blueprint already installed — use --force to overwrite |
| `PK-REGISTRY-004` | Blueprint not found in catalog |
| `PK-REGISTRY-005` | Version not found in catalog |

Add `RegistryError` to `core/errors.py`.

---

## Catalog Hosting (Phase 1)

The catalog is maintained in a separate `pipelinekit-registry` GitHub repository:

```
pipelinekit-registry/
├── v1/
│   ├── catalog.json
│   └── blueprints/
│       ├── postgres-to-snowflake-1.0.0.zip
│       ├── salesforce-to-snowflake-1.0.0.zip
│       └── stripe-to-snowflake-1.0.0.zip
```

Deployed via Cloudflare Pages to `registry.pipelinekit.dev`.

**Initial catalog contains:** All 3 current blueprints (postgres-to-snowflake, salesforce-to-snowflake, stripe-to-snowflake).

---

## State Extension

```sql
CREATE TABLE IF NOT EXISTS installed_blueprints (
    name            TEXT PRIMARY KEY,
    version         TEXT NOT NULL,
    source          TEXT,
    destination     TEXT,
    verified        INTEGER DEFAULT 0,
    installed_at    TEXT NOT NULL,
    registry_url    TEXT
);
```

`pipelinekit blueprint list` shows installed-from-registry blueprints alongside local blueprints.

---

## The Proposal Flywheel Integration

After `pipelinekit blueprint install`, the newly installed blueprint is immediately available as a pattern source for `pipelinekit generate blueprint`. The `BlueprintRegistry` already scans the `blueprints/` directory — no additional wiring needed.

---

## Test Requirements

All 256 prior tests must pass. All network calls mocked.

**tests/blueprints/test_remote_registry.py** — 6 tests:
- `fetch_catalog()` returns `BlueprintCatalog` from mocked HTTP
- `fetch_catalog()` returns cached catalog when within TTL
- `search()` finds blueprints by name, source, destination, tag
- `install()` writes blueprint to `blueprints/<name>/` (mocked download + tmp_path)
- `install()` raises `RegistryError(PK-REGISTRY-002)` on schema validation failure
- `install()` raises `RegistryError(PK-REGISTRY-003)` when already installed

---

## Acceptance Criteria

```
✓ pipelinekit blueprint search <query> shows matching blueprints
✓ pipelinekit blueprint install <name> downloads, validates, and writes blueprint
✓ Schema validation runs before write — PK-REGISTRY-002 on failure
✓ 8-asset check runs before write
✓ Catalog cached for 24 hours
✓ Offline graceful degradation — uses cache if registry unreachable
✓ Unverified blueprints show warning
✓ installed_blueprints table in state.db
✓ All 256 prior tests pass
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
```

---

## Out of Scope

- Blueprint publish (Phase 2)
- User authentication (Phase 2)
- Blueprint ratings and reviews (Phase 2)
- Private registries (Phase 3)
