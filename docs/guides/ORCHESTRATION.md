# Orchestrating PipelineKit

PipelineKit is a **CLI-first coordination layer**, not a scheduler. In v0.1.0 it does not include built-in scheduling, cron, or DAG semantics. Instead, it is designed to be invoked by the orchestrator you already use.

This guide shows minimal examples for running `pipelinekit run` from common orchestration tools.

---

## Airflow

Use a `BashOperator` that runs PipelineKit from a virtual environment or container.

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

with DAG(
    "pipelinekit_postgres_to_snowflake",
    start_date=days_ago(1),
    schedule_interval="0 6 * * *",
    catchup=False,
) as dag:
    run_pipeline = BashOperator(
        task_id="run_pipelinekit",
        bash_command="cd /opt/pipelinekit-project && poetry run pipelinekit run",
        env={
            "PG_HOST": "{{ var.value.pg_host }}",
            "PG_PASSWORD": "{{ var.value.pg_password }}",
            "SNOWFLAKE_PASSWORD": "{{ var.value.snowflake_password }}",
        },
    )
```

Tip: keep `pipelinekit.yaml` and blueprints under version control; let Airflow supply credentials via Variables.

---

## Dagster

Wrap the CLI call in an `@op` and assemble it into a job.

```python
from dagster import op, job, EnvVar
import subprocess


@op
def run_pipelinekit() -> None:
    result = subprocess.run(
        ["poetry", "run", "pipelinekit", "run"],
        cwd="/opt/pipelinekit-project",
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PG_HOST": EnvVar.str("PG_HOST"),
            "PG_PASSWORD": EnvVar.str("PG_PASSWORD"),
        },
    )
    print(result.stdout)


@job
def pipelinekit_job():
    run_pipelinekit()
```

For richer integration, you could parse `state.db` after the run and emit Dagster events for pass/fail status.

---

## Cron

A simple cron entry that runs every 6 hours and appends output to a log file.

```cron
0 */6 * * * cd /home/pipelinekit/project && /usr/local/bin/poetry run pipelinekit run >> /var/log/pipelinekit/run.log 2>&1
```

For strict health gating before the run:

```cron
0 */6 * * * cd /home/pipelinekit/project && /usr/local/bin/poetry run pipelinekit health --strict && /usr/local/bin/poetry run pipelinekit run >> /var/log/pipelinekit/run.log 2>&1
```

---

## GitHub Actions

Run PipelineKit on a schedule or on every push/pull request.

```yaml
name: PipelineKit Run

on:
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Poetry
        run: pip install poetry

      - name: Install dependencies
        run: poetry install --no-interaction

      - name: Run pipeline
        run: poetry run pipelinekit run
        env:
          PG_HOST: ${{ secrets.PG_HOST }}
          PG_PASSWORD: ${{ secrets.PG_PASSWORD }}
          SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PASSWORD }}
```

---

## Choosing an orchestrator

Because PipelineKit itself is stateless and deterministic per invocation, any tool that can run a shell command can orchestrate it. Pick the one that already owns the rest of your data stack.

| Tool | Best when |
| ---- | --------- |
| Airflow | You need a mature, widely-used scheduler with rich ecosystem. |
| Dagster | You want asset-aware orchestration and software-defined assets. |
| cron | You have a single server and simple schedule requirements. |
| GitHub Actions | Your pipeline runs on source changes or a light schedule. |

---

*See also: [Operations Runbook](OPERATIONS-RUNBOOK.md) for health checks, diagnosis, and escalation.*
