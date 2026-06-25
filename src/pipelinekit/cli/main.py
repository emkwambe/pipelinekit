"""Typer application: command registration and the ``--version`` callback.

The CLI orchestrates. Each command delegates to the ``config`` and ``state``
modules and never implements file, database, or provider logic itself.

See: SPEC-001, ADR-003 (CLI-first).
"""

from __future__ import annotations

import sys
from importlib.metadata import version

# Ensure Unicode-safe output on legacy Windows consoles (cp1252). Rich and
# Typer emit box-drawing and status glyphs (─ ✓ ✗ ⚠); without this the default
# charmap codec raises UnicodeEncodeError and commands crash with exit 1.
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        _reconfigure(encoding="utf-8", errors="replace")

import typer  # noqa: E402 — must follow stdout reconfiguration above

from pipelinekit.cli.architect import architect_app  # noqa: E402
from pipelinekit.cli.blueprint import blueprint_app  # noqa: E402
from pipelinekit.cli.diagnose import diagnose_command  # noqa: E402
from pipelinekit.cli.health import health_app  # noqa: E402
from pipelinekit.cli.init import init_command  # noqa: E402
from pipelinekit.cli.run import run_command  # noqa: E402
from pipelinekit.cli.status import status_command  # noqa: E402
from pipelinekit.cli.validate import validate_command  # noqa: E402

app = typer.Typer(
    name="pipelinekit",
    help="Trusted Analytics Infrastructure. Reduce Time-to-Trusted-Data.",
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print the installed version and exit when ``--version`` is passed."""
    if value:
        typer.echo(f"pipelinekit {version('pipelinekit')}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Trusted Analytics Infrastructure. Reduce Time-to-Trusted-Data."""


app.command("init")(init_command)
app.command("validate")(validate_command)
app.command("status")(status_command)
app.command("run")(run_command)
app.add_typer(blueprint_app, name="blueprint")
app.command("diagnose")(diagnose_command)
app.add_typer(architect_app, name="architect")
app.add_typer(health_app, name="health")
