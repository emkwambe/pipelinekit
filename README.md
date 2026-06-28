# PipelineKit

The AI-native operating system for trusted analytics pipelines.

## What is PipelineKit?

PipelineKit is a CLI-first coordination layer that sits above your existing analytics stack — dbt, Snowflake, Airbyte, Soda, and more. Instead of replacing those tools, it orchestrates them behind a single deterministic command surface: it designs pipelines from blueprints, validates configuration and data contracts before anything runs, enforces quality on every execution, and adds an AI layer that diagnoses failures and proposes new pipelines without ever touching production on its own. The goal is to shrink Time-to-Trusted-Data — the gap between "we need this pipeline" and "we trust these numbers."

## Quickstart

**Requirements:** Python 3.11+, Docker (for Blueprint #001), dbt-core

```bash
git clone https://github.com/emkwambe/pipelinekit.git
cd pipelinekit
pip install -e .
pipelinekit health --strict
pipelinekit blueprint install postgres-to-snowflake
pipelinekit validate
pipelinekit run
```

PyPI package coming soon. Star the repo to be notified.

`health --strict` confirms your environment and credentials are ready. `blueprint install` pulls a complete, verified pipeline package. `validate` checks configuration and data contracts before execution, and `run` moves data through ingestion → transformation → quality as deterministic steps.

## Blueprint Catalog

A blueprint is a complete, verifiable pipeline package — ingestion, dbt transformation, data contracts, quality checks, alerts, and docs in one installable unit. Every blueprint ships with dbt tests that gate trust:

| Blueprint | Source → Destination | dbt tests |
|---|---|---|
| `postgres-to-snowflake` | Postgres → Snowflake | 7 |
| `salesforce-to-snowflake` | Salesforce → Snowflake | 5 |
| `stripe-to-snowflake` | Stripe → Snowflake | 35 |

Browse and install from the registry at **[registry.pipelinekit.dev](https://registry.pipelinekit.dev)**.

## Documentation

| Guide | What it covers |
|---|---|
| [Getting Started](docs/guides/GETTING-STARTED.md) | End-to-end first pipeline |
| [Blueprint Guide](docs/guides/BLUEPRINT-GUIDE.md) | Installing, validating, and authoring blueprints |
| [CLI Reference](docs/guides/CLI-REFERENCE.md) | Every command and flag |
| [Configuration Reference](docs/guides/CONFIGURATION-REFERENCE.md) | The `pipelinekit.yaml` schema |
| [AI Features](docs/guides/AI-FEATURES.md) | Diagnostics and blueprint proposal |
| [Migration Guide](docs/guides/MIGRATION-GUIDE.md) | Moving from Airbyte, Fivetran, or Python |
| [Operations Runbook](docs/guides/OPERATIONS-RUNBOOK.md) | Running pipelines in production |

## Design Partner Program

PipelineKit is taking on a small number of design partners — teams who want to shape an AI-native analytics platform while getting hands-on support standing up trusted pipelines. Partners get early access to new blueprints, direct input on the roadmap, and help migrating existing ingestion. Learn more and apply at **[pipelinekit.dev](https://pipelinekit.dev)**.

## License

Apache License 2.0. See [LICENSE](LICENSE).
