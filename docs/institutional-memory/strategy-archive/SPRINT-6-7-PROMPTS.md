# PipelineKit — Sprint 6-7
## Migration Intelligence — Session Opener + Implementation Prompt

---

## Session Opener

You are Claude Code working inside the PipelineKit repository.

### Read First

```
1. .claude/CLAUDE.md
2. docs/reference/PROJECT-STATUS.md
3. docs/decisions/ADR-020-Migration-Intelligence.md    ← Read completely
4. docs/specifications/SPEC-017-Migration-Intelligence.md  ← Primary SPEC
5. src/pipelinekit/ai/blueprint_proposer.py            ← Pattern to follow
6. src/pipelinekit/ai/proposal_models.py               ← Pattern to follow
7. src/pipelinekit/cli/generate.py                     ← CLI pattern
```

### Confirm Your Understanding Of

1. What Migration Intelligence reads and what it proposes — what it NEVER does
2. The four supported source formats and their parsers
3. What `MigrationGap` with `blocking=True` means for the apply path
4. How `pipelinekit.proposed.yaml` differs from `pipelinekit.yaml`
5. What must never be touched

Confirm when ready.

---

## Implementation Prompt

### Your Identity

diagnostics-engineer. Same agent as Phases 4-5 and Sprint 6-5.

Primary ADR: `docs/decisions/ADR-020-Migration-Intelligence.md`  
Primary SPEC: `docs/specifications/SPEC-017-Migration-Intelligence.md`

---

### Sprint Goal

```powershell
poetry run pipelinekit migrate --help
poetry run pipelinekit migrate analyze --help
poetry run pytest --cov=src/pipelinekit --cov-fail-under=80
poetry run ruff check .
poetry run black --check .
poetry run mypy src/pipelinekit
```

All 268 prior tests must pass.

---

### Files You Are Allowed To Create

```
src/pipelinekit/ai/
├── migration_models.py
├── migration_analyzer.py
└── config_parsers.py

src/pipelinekit/cli/
└── migrate.py

tests/ai/
├── test_migration_models.py
├── test_migration_analyzer.py
└── test_config_parsers.py
```

You may also modify:
```
src/pipelinekit/ai/provider.py              Add analyze_migration() to Protocol
src/pipelinekit/ai/providers/anthropic.py   Implement analyze_migration()
src/pipelinekit/ai/providers/openai.py      Implement analyze_migration()
src/pipelinekit/ai/providers/ollama.py      Implement analyze_migration()
src/pipelinekit/ai/providers/deepseek.py    Implement analyze_migration()
src/pipelinekit/ai/providers/mistral.py     Implement analyze_migration()
src/pipelinekit/cli/main.py                 Register migrate command group
src/pipelinekit/core/errors.py              Add MigrationError
docs/reference/Error-Codes.md              Add PK-MIGRATE-001 to 005
```

---

### Files You Must Not Modify

```
docs/reference/PROJECT-STATUS.md    ← NEVER
blueprints/                         ← READ ONLY
schemas/                            ← READ ONLY
All existing test files             ← READ ONLY
All Phase 1-5 source files          ← READ ONLY (except provider.py + 5 providers)
src/pipelinekit/ai/blueprint_proposer.py  ← READ ONLY
src/pipelinekit/ai/proposal_models.py     ← READ ONLY
```

---

### Critical Constraints

**Never execute the Python file being analyzed:**
`PythonParser.parse()` must use AST parsing (`ast.parse()`) or regex — never `exec()`, `eval()`, or subprocess. A malicious pipeline.py must not be able to run code during analysis.

**Write to `pipelinekit.proposed.yaml` not `pipelinekit.yaml`:**
`apply()` writes the draft to `pipelinekit.proposed.yaml` — never overwrites the active config.

**Blocking gaps prevent apply:**
`apply()` raises `MigrationError(PK-MIGRATE-003)` when `blocking_gaps > 0` unless `--force` is passed.

**can_auto_apply always False:**
Same constraint as ADR-018. MigrationAnalyzer proposes — human applies.

---

### Sample Test Fixtures

Create small sample configs for tests (inline in test files — no fixture files):

```python
# Airbyte sample
AIRBYTE_SAMPLE = {
    "sourceId": "abc-123",
    "destinationId": "def-456",
    "connectionId": "ghi-789",
    "sourceConfiguration": {
        "host": "db.example.com",
        "port": 5432,
        "database": "production",
        "username": "analyst"
    },
    "destinationType": "snowflake",
    "syncCatalog": {
        "streams": [
            {"stream": {"name": "orders"}, "config": {"syncMode": "incremental"}},
            {"stream": {"name": "customers"}, "config": {"syncMode": "full_refresh"}}
        ]
    }
}

# Fivetran sample
FIVETRAN_SAMPLE = {
    "connector": {
        "id": "xyz_789",
        "service": "postgres",
        "schema": "public",
        "config": {
            "host": "db.example.com",
            "port": "5432",
            "database": "production"
        }
    },
    "destination": {
        "service": "snowflake",
        "config": {"host": "abc123.snowflakecomputing.com"}
    },
    "tables": ["orders", "customers", "products"]
}

# Python sample (as string)
PYTHON_SAMPLE = '''
import psycopg2
conn = psycopg2.connect(
    host="db.example.com",
    database="production",
    user="analyst"
)
# Load orders to S3
cursor = conn.cursor()
cursor.execute("SELECT * FROM orders")
'''
```

---

### Definition of Done

```
✓ pipelinekit migrate analyze --help exits 0
✓ AirbyteParser extracts source/destination/streams
✓ FivetranParser extracts connector/schema/tables
✓ PythonParser uses ast.parse() — never exec/eval
✓ MigrationProposal has confidence, mappings, gaps, draft_yaml
✓ apply() writes pipelinekit.proposed.yaml (not pipelinekit.yaml)
✓ Blocking gaps prevent apply without --force
✓ can_auto_apply always False
✓ All 268 prior tests pass
✓ coverage >= 80%
✓ ruff, black, mypy clean
✓ PROJECT-STATUS.md untouched
```

---

### Commit Message

```
feat: Sprint 6-7 — Migration Intelligence (ADR-020, SPEC-017)

- src/pipelinekit/ai/migration_models.py — MigrationProposal, MappingResult, MigrationGap
- src/pipelinekit/ai/migration_analyzer.py — MigrationAnalyzer (analyze + apply)
- src/pipelinekit/ai/config_parsers.py — Airbyte, Fivetran, Python parsers (ast.parse only)
- src/pipelinekit/cli/migrate.py — pipelinekit migrate analyze
- All 5 providers — analyze_migration() implemented

ADR-020 satisfied. ICP-004 migration path established.
PythonParser uses ast.parse — never exec/eval.
apply() writes pipelinekit.proposed.yaml — never overwrites active config.
```
