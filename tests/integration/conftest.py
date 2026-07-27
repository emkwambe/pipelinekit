"""Shared fixtures for CLI integration tests (Sprint A).

How PipelineKit resolves ``db_path`` (verified in source, not assumed):

* There is **no** ``PIPELINEKIT_DB_PATH`` environment variable. ``db.get_db_path``
  returns ``<cwd>/.pipelinekit/state.db`` and every CLI ``_db_path()`` calls it
  with no arguments, so the database location follows the current working
  directory.
* ``BlueprintRegistry`` scans ``Path("blueprints")``, also relative to the CWD.

Isolation therefore means running each command from a working directory that
contains the real blueprints. Each test gets its **own** ``tmp_path``: the real
``blueprints/`` tree is copied in and the CWD is switched there, so registry-backed
commands read the real blueprint files while every state write lands in that
test's ``tmp_path/.pipelinekit`` — the real project ``state.db`` is never touched.

A per-test copy (rather than a shared session directory) is deliberate: it keeps
tests fully independent and order-insensitive, and avoids Windows file-lock races
when resetting SQLite state between tests.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pipelinekit.state import db

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REAL_BLUEPRINTS = _REPO_ROOT / "blueprints"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Isolated project root: real blueprints staged, CWD switched, fresh state.

    Returns the resolved ``db_path`` (``tmp_path/.pipelinekit/state.db``) so a
    test can seed state directly through the same path the CLI will read.
    """
    shutil.copytree(_REAL_BLUEPRINTS, tmp_path / "blueprints")
    monkeypatch.chdir(tmp_path)
    db.initialize()
    return str(db.get_db_path())
