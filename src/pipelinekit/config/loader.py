"""Load, validate, and generate ``pipelinekit.yaml``.

This module is the only place that touches the configuration file on disk. The
CLI orchestrates these functions; it never performs YAML or file I/O itself.

Note on the ``cwd`` parameter: SPEC-002 documents the signatures as
``cwd: Path = Path.cwd()``. A literal ``Path.cwd()`` default binds *once* at
import time, which breaks working-directory isolation in tests and would write
into the wrong directory. We therefore use ``cwd: Path | None = None`` and
resolve ``Path.cwd()`` at call time — identical ergonomics for callers,
correct behaviour under ``chdir``.

See: SPEC-002, ADR-009 (human-readable), docs/reference/Error-Codes.md.
"""

from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from pipelinekit.config.schema import PipelineConfig
from pipelinekit.core.errors import ConfigurationError

CONFIG_FILENAME = "pipelinekit.yaml"

# Canonical, human-readable default configuration (ADR-009). Emitted verbatim
# by ``write_default_config`` so generated files keep their explanatory
# comments. Round-trips cleanly through ``load_config``.
DEFAULT_CONFIG_YAML = """\
# pipelinekit.yaml
# PipelineKit Configuration
# See: https://pipelinekit.dev/docs/configuration

pipeline:
  name: my-project
  version: "0.1.0"
  description: ""

runtime:
  environment: local

ingestion:
  source:
    type: postgres
    host: localhost
    port: 5432
    database: ""
  destination:
    type: snowflake
    account: ""
    database: ""

transformation:
  enabled: false
  project_dir: ./transform

contracts:
  enabled: true
  directory: ./contracts

quality:
  enabled: false
  checks_dir: ./quality

diagnostics:
  enabled: false
  provider: none

notifications:
  enabled: false
  channels: []
"""


def _resolve(cwd: Path | None) -> Path:
    """Resolve the working directory at call time."""
    return cwd if cwd is not None else Path.cwd()


def config_exists(cwd: Path | None = None) -> bool:
    """Return ``True`` if ``pipelinekit.yaml`` exists in ``cwd``."""
    return (_resolve(cwd) / CONFIG_FILENAME).is_file()


def load_config(cwd: Path | None = None) -> PipelineConfig:
    """Load and validate ``pipelinekit.yaml`` from ``cwd``.

    Returns:
        A validated :class:`PipelineConfig`.

    Raises:
        ConfigurationError: ``PK-CONFIG-003`` if the file is not found,
            ``PK-CONFIG-004`` if the YAML is malformed, or ``PK-CONFIG-001``
            if the content fails schema validation.
    """
    path = _resolve(cwd) / CONFIG_FILENAME

    if not path.is_file():
        raise ConfigurationError(
            "PK-CONFIG-003",
            f"{CONFIG_FILENAME} not found in {path.parent}",
            {"path": str(path)},
        )

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            "PK-CONFIG-004",
            f"{CONFIG_FILENAME} is not valid YAML",
            {"path": str(path), "detail": str(exc)},
        ) from exc

    if not isinstance(raw, dict):
        raise ConfigurationError(
            "PK-CONFIG-001",
            f"{CONFIG_FILENAME} must contain a YAML mapping of sections",
            {"path": str(path)},
        )

    try:
        return PipelineConfig(**raw)
    except ValidationError as exc:
        errors = [
            f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        ]
        raise ConfigurationError(
            "PK-CONFIG-001",
            f"{CONFIG_FILENAME} failed schema validation",
            {"path": str(path), "errors": errors},
        ) from exc


def write_default_config(cwd: Path | None = None) -> None:
    """Write the canonical default ``pipelinekit.yaml`` to ``cwd``.

    Raises:
        ConfigurationError: ``PK-CONFIG-005`` if the file cannot be written.
    """
    path = _resolve(cwd) / CONFIG_FILENAME
    try:
        path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(
            "PK-CONFIG-005",
            f"Failed to write {CONFIG_FILENAME}",
            {"path": str(path), "detail": str(exc)},
        ) from exc
