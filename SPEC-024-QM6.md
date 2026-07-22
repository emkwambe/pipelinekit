# SPEC-024 — QM-6 Volume Anomaly Detection

**EMS:** EMS-002 Quality Management System  
**Capability code:** QM-6  
**Phase:** 2  
**ADR:** ADR-025-QM6-Volume-Anomaly-Detection.md  
**Depends on:** QM-4 pattern (blueprint scanning) — BUILT  
**Date:** June 29, 2026  
**Status:** Approved — ready to build

---

## Purpose

Record row counts for pipeline tables after each run. Detect when
current counts deviate significantly from the established baseline.
Alert engineers to silent volume failures before they reach dashboards.

---

## CLI Surface

```bash
# Record row counts for all tables in a blueprint
poetry run pipelinekit quality record-counts \
  --blueprint stripe-to-snowflake \
  --table charges:45231 \
  --table customers:12840

# Expected output:
# ✓ Recorded row counts for stripe-to-snowflake
#   charges:    45,231 rows  (baseline: establishing — 1/3 snapshots)
#   customers:  12,840 rows  (baseline: establishing — 1/3 snapshots)

# After 3+ snapshots:
# ✓ Recorded row counts for stripe-to-snowflake
#   charges:    45,231 rows  (baseline: 44,820 avg — within threshold)
#   customers:  12,840 rows  (baseline: 12,950 avg — within threshold)

# Check for anomalies
poetry run pipelinekit quality check-anomalies \
  --blueprint stripe-to-snowflake

# Expected output (clean):
# Volume Anomaly Check — stripe-to-snowflake
# ─────────────────────────────────────────
# ✓ charges    45,231  baseline: 44,820  deviation: +0.9%  OK
# ✓ customers  12,840  baseline: 12,950  deviation: -0.9%  OK

# Expected output (anomaly detected):
# Volume Anomaly Check — stripe-to-snowflake
# ─────────────────────────────────────────
# ✓ charges    45,231  baseline: 44,820  deviation: +0.9%  OK
# ⚠ customers     850  baseline: 12,950  deviation: -93.4% ANOMALY
#
# [PK-QM-003] Volume anomaly detected in stripe-to-snowflake
#   customers: expected ~12,950 rows, got 850 (93.4% below baseline)
#   This may indicate: missing partition, failed extraction, or truncated load.

# Show row count history
poetry run pipelinekit quality row-count-history \
  --blueprint stripe-to-snowflake \
  --table charges

# Expected output:
# Row Count History — stripe-to-snowflake / charges
# ─────────────────────────────────────────────────
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┓
# ┃ Recorded At              ┃ Row Count  ┃ Deviation ┃
# ┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━┩
# │ 2026-06-29T10:00:00+00:00│ 45,231     │ +0.9%     │
# │ 2026-06-28T10:00:00+00:00│ 44,820     │ baseline  │
# │ 2026-06-27T10:00:00+00:00│ 44,100     │ baseline  │
# └──────────────────────────┴────────────┴───────────┘

# With threshold override
poetry run pipelinekit quality check-anomalies \
  --blueprint stripe-to-snowflake \
  --threshold 10
# Uses 10% threshold instead of default 20%
```

---

## Implementation Files

**Files to CREATE (all verified not to exist):**
```
src/pipelinekit/quality/anomaly.py              ← QM-6 core logic
tests/quality/test_qm6_anomaly.py               ← all QM-6 tests
```

**Files to MODIFY (verified to exist):**
```
src/pipelinekit/quality/__init__.py             ← export new functions
src/pipelinekit/state/db.py                     ← add qm_row_counts table
src/pipelinekit/cli/quality.py                  ← add 3 new subcommands
```

**Files NOT to touch:**
```
src/pipelinekit/quality/coverage.py             ← QM-4 untouched
src/pipelinekit/governance/                     ← GM domain untouched
src/pipelinekit/contracts/                      ← DC domain untouched
tests/quality/test_qm4_coverage.py              ← existing tests untouched
tests/governance/                               ← GM tests untouched
blueprints/                                     ← blueprint files untouched
```

---

## Data Model

Add to `src/pipelinekit/state/db.py`:

```sql
CREATE TABLE IF NOT EXISTS qm_row_counts (
    id TEXT PRIMARY KEY,
    blueprint_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_qm_row_counts_blueprint_table
    ON qm_row_counts(blueprint_name, table_name, recorded_at);
```

Add these functions to `db.py`:

```python
def insert_row_count(
    blueprint_name: str,
    table_name: str,
    row_count: int,
    db_path: str
) -> None:
    """Insert a new row count snapshot."""

def get_row_count_history(
    blueprint_name: str,
    table_name: str,
    limit: int,
    db_path: str
) -> list[dict]:
    """Get last N row count snapshots, newest first."""

def get_all_tables_for_blueprint(
    blueprint_name: str,
    db_path: str
) -> list[str]:
    """Get all table names that have row count history for a blueprint."""
```

---

## Data Structures

```python
@dataclass
class RowCountSnapshot:
    id: str
    blueprint_name: str
    table_name: str
    row_count: int
    recorded_at: str         # ISO timestamp with timezone

@dataclass
class VolumeAnomaly:
    blueprint_name: str
    table_name: str
    current_count: int
    baseline_avg: float
    deviation_pct: float     # positive = above baseline, negative = below
    is_anomaly: bool
    threshold_pct: float     # threshold used for this check
    snapshot_count: int      # how many snapshots in baseline window
    status: str              # "OK", "ANOMALY", "ESTABLISHING" (< 3 snapshots)
```

---

## Core Logic

### anomaly.py — key functions

```python
def record_row_counts(
    blueprint_name: str,
    table_counts: dict[str, int],    # {"charges": 45231, "customers": 12840}
    db_path: str
) -> list[RowCountSnapshot]:
    """
    Record row counts for multiple tables in one call.
    Returns list of created RowCountSnapshot objects.
    """

def check_volume_anomalies(
    blueprint_name: str,
    current_counts: dict[str, int],
    db_path: str,
    threshold_pct: float = 20.0,
    window: int = 7
) -> list[VolumeAnomaly]:
    """
    Compare current_counts against rolling baseline.
    For each table:
      - Get last `window` snapshots from db
      - If < 3 snapshots: status = "ESTABLISHING", is_anomaly = False
      - If >= 3 snapshots: compute baseline_avg = mean of last window counts
        deviation_pct = (current - baseline_avg) / baseline_avg * 100
        is_anomaly = abs(deviation_pct) > threshold_pct
    Returns list of VolumeAnomaly, one per table in current_counts.
    """

def get_row_count_history(
    blueprint_name: str,
    table_name: str,
    db_path: str,
    limit: int = 10
) -> list[RowCountSnapshot]:
    """
    Get historical row counts for a specific table.
    Returns newest first.
    """

def compute_baseline(snapshots: list[RowCountSnapshot]) -> float:
    """
    Compute mean row count from a list of snapshots.
    Returns 0.0 if snapshots is empty.
    """

def compute_deviation_pct(current: int, baseline: float) -> float:
    """
    Compute percentage deviation from baseline.
    Returns 0.0 if baseline is 0.
    Formula: (current - baseline) / baseline * 100
    """
```

---

## Error Codes

Add to `docs/reference/Error-Codes.md` under existing `### QM` subsection:

```
PK-QM-003  Volume anomaly detected
           Row count deviates significantly from the established baseline
           Possible causes: missing partition, failed extraction, truncated load,
           duplicate rows loaded, source data issue
           Fix: investigate the pipeline run logs for the affected table
```

---

## Test Requirements

File: `tests/quality/test_qm6_anomaly.py`
Minimum: 10 tests

```python
def test_qm6_record_row_counts_creates_snapshots()
    """record_row_counts creates RowCountSnapshot for each table"""

def test_qm6_record_row_counts_multiple_tables()
    """record_row_counts handles dict with multiple tables"""

def test_qm6_check_anomalies_returns_establishing_with_few_snapshots()
    """status is ESTABLISHING when fewer than 3 snapshots exist"""

def test_qm6_check_anomalies_no_anomaly_within_threshold()
    """is_anomaly is False when deviation is within threshold"""

def test_qm6_check_anomalies_detects_drop_below_threshold()
    """is_anomaly is True when count drops significantly below baseline"""

def test_qm6_check_anomalies_detects_spike_above_threshold()
    """is_anomaly is True when count spikes significantly above baseline"""

def test_qm6_check_anomalies_respects_custom_threshold()
    """custom threshold_pct is used for comparison"""

def test_qm6_compute_baseline_returns_mean()
    """compute_baseline returns correct mean of snapshot row counts"""

def test_qm6_compute_deviation_pct_is_correct()
    """compute_deviation_pct returns correct percentage"""

def test_qm6_get_row_count_history_returns_newest_first()
    """get_row_count_history returns snapshots ordered newest first"""
```

Use `tmp_path` for all test databases.

---

## Definition of Done

- [ ] `pipelinekit quality record-counts` records row counts correctly
- [ ] `pipelinekit quality check-anomalies` detects deviations
- [ ] `pipelinekit quality check-anomalies --threshold N` uses custom threshold
- [ ] `pipelinekit quality row-count-history` shows history table
- [ ] ESTABLISHING status shown when < 3 snapshots
- [ ] All 10 new tests pass
- [ ] 343 + 10 = 353 total tests passing
- [ ] ruff clean, black clean, mypy clean
- [ ] PK-QM-003 in Error-Codes.md
- [ ] qm_row_counts table migration-safe (CREATE TABLE IF NOT EXISTS)
- [ ] No modifications to QM-4 coverage, GM-1, DC domain, or existing tests

---

## Commit Message

```
feat: QM-6 — volume anomaly detection with rolling baseline
```
