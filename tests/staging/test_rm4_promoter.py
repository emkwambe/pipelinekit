"""Tests for RM-4 atomic staging → production promotion.

Deterministic, no AI. Each test builds its own DuckDB file and state database
under ``tmp_path`` — the real destination and ``.pipelinekit/state.db`` are never
touched. Follows the adapter/CLI test patterns already in the suite.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import duckdb
import pytest
from pipelinekit.adapters.factory import AdapterFactory
from pipelinekit.cli.main import app
from pipelinekit.config.loader import load_config
from pipelinekit.staging.promoter import (
    BUILDING,
    PROMOTED,
    ROLLED_BACK,
    StagingPromoter,
)
from pipelinekit.state import db
from typer.testing import CliRunner

runner = CliRunner()

_PIPELINE = "pipelinekit-demo"
_STAGING = "pipelinekit_staging"
_PRODUCTION = "pipelinekit_transformed"


def _duckdb_file(tmp_path: Path) -> str:
    """Return a DuckDB path with a populated production schema."""
    path = str(tmp_path / "warehouse.duckdb")
    con = duckdb.connect(path)
    con.execute(f'CREATE SCHEMA "{_PRODUCTION}"')
    con.execute(f'CREATE TABLE "{_PRODUCTION}".orders AS SELECT 1 AS id, 10 AS amount')
    con.close()
    return path


def _promoter(tmp_path: Path) -> StagingPromoter:
    """Return a promoter wired to this test's DuckDB file and state db."""
    return StagingPromoter(_duckdb_file(tmp_path), str(tmp_path / "state.db"))


def _stage_table(duckdb_path: str, rows: str = "SELECT 2 AS id, 20 AS amount") -> None:
    """Write one table into the staging schema, as a dbt build would."""
    con = duckdb.connect(duckdb_path)
    con.execute(f'CREATE OR REPLACE TABLE "{_STAGING}".orders AS {rows}')
    con.close()


def _production_rows(duckdb_path: str) -> list[tuple]:
    """Return the current contents of the production orders table."""
    con = duckdb.connect(duckdb_path)
    try:
        return con.execute(f'SELECT id, amount FROM "{_PRODUCTION}".orders').fetchall()
    finally:
        con.close()


def _schemas(duckdb_path: str) -> set[str]:
    """Return every schema name present in the DuckDB file."""
    con = duckdb.connect(duckdb_path)
    try:
        return {
            row[0]
            for row in con.execute(
                "SELECT schema_name FROM information_schema.schemata"
            ).fetchall()
        }
    finally:
        con.close()


def _write_config(tmp_path: Path, duckdb_path: str, staging_enabled: bool) -> None:
    """Write a complete pipelinekit.yaml into tmp_path."""
    (tmp_path / "pipelinekit.yaml").write_text(
        textwrap.dedent(
            f"""
            pipeline:
              name: {_PIPELINE}
              version: '1.0'
            runtime:
              environment: local
            ingestion:
              source:
                type: postgres
              destination:
                type: duckdb
                path: {duckdb_path}
            transformation:
              enabled: true
              project_dir: ./transform
              staging:
                enabled: {str(staging_enabled).lower()}
                schema: {_STAGING}
              production:
                schema: {_PRODUCTION}
            contracts:
              enabled: false
              directory: ./contracts
            quality:
              enabled: false
            diagnostics:
              enabled: false
            notifications:
              enabled: false
            """
        ).strip(),
        encoding="utf-8",
    )


def test_rm4_staging_schema_created_before_dbt_run(tmp_path: Path) -> None:
    """create_staging_schema makes an empty staging schema and records it."""
    promoter = _promoter(tmp_path)

    run = promoter.create_staging_schema(_STAGING, _PIPELINE, _PRODUCTION)

    assert run.status == BUILDING
    assert run.staging_schema == _STAGING
    assert _STAGING in _schemas(promoter.duckdb_path)
    # A leftover schema from an earlier failed run must not survive into this one.
    _stage_table(promoter.duckdb_path)
    promoter.create_staging_schema(_STAGING, _PIPELINE, _PRODUCTION)
    con = duckdb.connect(promoter.duckdb_path)
    remaining = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema = ?",
        (_STAGING,),
    ).fetchone()
    con.close()
    assert remaining is not None and remaining[0] == 0


def test_rm4_production_untouched_when_staging_fails(tmp_path: Path) -> None:
    """An empty staging schema is refused, leaving production exactly as it was."""
    promoter = _promoter(tmp_path)
    before = _production_rows(promoter.duckdb_path)
    run = promoter.create_staging_schema(_STAGING, _PIPELINE, _PRODUCTION)

    # dbt wrote nothing to staging — promoting would silently leave prod stale.
    promoted = promoter.promote_to_production(_STAGING, _PRODUCTION, run.id)

    assert promoted is False
    assert _production_rows(promoter.duckdb_path) == before == [(1, 10)]
    status = promoter.get_staging_status(_PIPELINE)
    assert status is not None
    assert status.status == "failed"
    assert "empty" in (status.error or "")


def test_rm4_promote_renames_schemas_correctly(tmp_path: Path) -> None:
    """Promotion replaces production contents with staging's, then drops staging."""
    promoter = _promoter(tmp_path)
    run = promoter.create_staging_schema(_STAGING, _PIPELINE, _PRODUCTION)
    _stage_table(promoter.duckdb_path)

    assert promoter.promote_to_production(_STAGING, _PRODUCTION, run.id) is True

    assert _production_rows(promoter.duckdb_path) == [(2, 20)]
    assert _STAGING not in _schemas(promoter.duckdb_path)


def test_rm4_rollback_drops_staging_only(tmp_path: Path) -> None:
    """Rollback removes staging and never touches production."""
    promoter = _promoter(tmp_path)
    run = promoter.create_staging_schema(_STAGING, _PIPELINE, _PRODUCTION)
    _stage_table(promoter.duckdb_path)

    assert promoter.rollback(_STAGING, _PRODUCTION, run.id) is True

    assert _STAGING not in _schemas(promoter.duckdb_path)
    assert _production_rows(promoter.duckdb_path) == [(1, 10)]
    status = promoter.get_staging_status(_PIPELINE)
    assert status is not None and status.status == ROLLED_BACK


def test_rm4_staging_run_recorded_in_state_db(tmp_path: Path) -> None:
    """The staging run is persisted with its schemas and lifecycle status."""
    promoter = _promoter(tmp_path)
    run = promoter.create_staging_schema(_STAGING, _PIPELINE, _PRODUCTION)

    row = db.get_staging_run(run.id, promoter.db_path)

    assert row is not None
    assert row["pipeline_name"] == _PIPELINE
    assert row["staging_schema"] == _STAGING
    assert row["production_schema"] == _PRODUCTION
    assert row["status"] == BUILDING
    assert row["promoted_at"] is None


def test_rm4_staging_disabled_uses_existing_behavior(tmp_path: Path) -> None:
    """With staging off the dbt adapter is built exactly as before RM-4."""
    duckdb_path = _duckdb_file(tmp_path)
    _write_config(tmp_path, duckdb_path, staging_enabled=False)
    config = load_config(tmp_path)

    adapter = AdapterFactory.create_transformation(config)

    assert adapter is not None
    assert adapter.target_schema is None
    assert adapter._dbt_env() is None  # inherits the environment unchanged

    # Enabling staging is what switches the adapter onto the staging schema.
    _write_config(tmp_path, duckdb_path, staging_enabled=True)
    staged_adapter = AdapterFactory.create_transformation(load_config(tmp_path))
    assert staged_adapter is not None
    assert staged_adapter.target_schema == _STAGING
    env = staged_adapter._dbt_env()
    assert env is not None and env["PK_DBT_SCHEMA"] == _STAGING


def test_rm4_staging_status_shows_current_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`staging status` reports the recorded run; no runs is not an error."""
    duckdb_path = _duckdb_file(tmp_path)
    _write_config(tmp_path, duckdb_path, staging_enabled=True)
    monkeypatch.chdir(tmp_path)

    empty = runner.invoke(app, ["staging", "status"])
    assert empty.exit_code == 0
    assert "No staging runs recorded" in empty.output

    StagingPromoter(duckdb_path, str(db.get_db_path())).create_staging_schema(
        _STAGING, _PIPELINE, _PRODUCTION
    )
    result = runner.invoke(app, ["staging", "status"])

    assert result.exit_code == 0
    assert BUILDING in result.output
    assert _STAGING in result.output


def test_rm4_manual_promote_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`staging promote` promotes a built staging schema into production."""
    duckdb_path = _duckdb_file(tmp_path)
    _write_config(tmp_path, duckdb_path, staging_enabled=True)
    monkeypatch.chdir(tmp_path)
    StagingPromoter(duckdb_path, str(db.get_db_path())).create_staging_schema(
        _STAGING, _PIPELINE, _PRODUCTION
    )
    _stage_table(duckdb_path)

    result = runner.invoke(app, ["staging", "promote"])

    assert result.exit_code == 0
    assert _production_rows(duckdb_path) == [(2, 20)]

    # A promoted run is terminal — promoting again is refused, not repeated.
    again = runner.invoke(app, ["staging", "promote"])
    assert again.exit_code == 1


def test_rm4_manual_rollback_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`staging rollback` drops staging and reports production untouched."""
    duckdb_path = _duckdb_file(tmp_path)
    _write_config(tmp_path, duckdb_path, staging_enabled=True)
    monkeypatch.chdir(tmp_path)
    StagingPromoter(duckdb_path, str(db.get_db_path())).create_staging_schema(
        _STAGING, _PIPELINE, _PRODUCTION
    )
    _stage_table(duckdb_path)

    result = runner.invoke(app, ["staging", "rollback"])

    assert result.exit_code == 0
    assert _STAGING not in _schemas(duckdb_path)
    assert _production_rows(duckdb_path) == [(1, 10)]


def test_rm4_run_table_records_promotion_timestamp(tmp_path: Path) -> None:
    """A promoted run records promoted_at and the staged row count."""
    promoter = _promoter(tmp_path)
    run = promoter.create_staging_schema(_STAGING, _PIPELINE, _PRODUCTION)
    _stage_table(
        promoter.duckdb_path, "SELECT * FROM (VALUES (2, 20), (3, 30)) AS t(id, amount)"
    )

    promoter.promote_to_production(_STAGING, _PRODUCTION, run.id)

    row = db.get_staging_run(run.id, promoter.db_path)
    assert row is not None
    assert row["status"] == PROMOTED
    assert row["promoted_at"] is not None
    assert row["rows_staged"] == 2


def test_rm4_promotion_is_atomic_across_tables(tmp_path: Path) -> None:
    """A failure mid-promotion leaves production wholly unchanged.

    This is the guarantee the sprint exists for: production is never left
    holding some tables from the new run and some from the old.
    """
    promoter = _promoter(tmp_path)
    run = promoter.create_staging_schema(_STAGING, _PIPELINE, _PRODUCTION)

    con = duckdb.connect(promoter.duckdb_path)
    con.execute(f'CREATE TABLE "{_STAGING}".orders AS SELECT 2 AS id, 20 AS amount')
    # Sorts after 'orders', so orders is copied before this one fails. Production
    # already holds a *view* of this name, which CREATE OR REPLACE TABLE cannot
    # overwrite — the promotion aborts partway through.
    con.execute(f'CREATE TABLE "{_STAGING}".zz_blocked AS SELECT 1 AS id')
    con.execute(f'CREATE VIEW "{_PRODUCTION}".zz_blocked AS SELECT 99 AS id')
    con.close()

    assert promoter.promote_to_production(_STAGING, _PRODUCTION, run.id) is False

    # orders was copied first, but the transaction rolled it back.
    assert _production_rows(promoter.duckdb_path) == [(1, 10)]
