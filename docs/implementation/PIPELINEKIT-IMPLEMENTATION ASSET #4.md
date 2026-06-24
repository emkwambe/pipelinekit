# **PIPELINEKIT-IMPLEMENTATION ASSET \#4**

# **Developer Onboarding Guide**

## **Version 1.0**

---

# **Welcome**

Welcome to PipelineKit.

PipelineKit is a Trusted Analytics Infrastructure platform.

We do not build:

* another ETL tool  
* another orchestrator  
* another observability platform

We build the operational layer that sits above them.

Mission:

Reduce Time-to-Trusted-Data.

Primary KPI:

Time-to-Trusted-Data \< 1 Day.

---

# **Development Principles**

## **Principle 1**

Contracts Own Truth

Not AI.

Not assumptions.

Not dashboards.

Contracts.

---

## **Principle 2**

Observability Is Mandatory

Every component must be observable.

Every failure must be diagnosable.

---

## **Principle 3**

Blueprints Are The Product

Code supports blueprints.

Blueprints create value.

---

## **Principle 4**

Provider Agnostic

Never hardcode:

* OpenAI  
* Anthropic  
* dlt  
* Resend  
* Soda

Everything is an adapter.

---

## **Principle 5**

Local First

PipelineKit should function locally.

Cloud services are optional.

---

# **Local Development Setup**

## **Prerequisites**

Python 3.11+

Docker

Git

Poetry

Snowflake test account

Postgres test database

---

# **Installation**

git clone https://github.com/pipelinekit/pipelinekit

cd pipelinekit

poetry install

poetry shell

---

# **Run Tests**

pytest

---

# **Run Linting**

ruff check .

black .

mypy .

---

# **Start Example Blueprint**

pipelinekit init

pipelinekit run

---

# **Architecture Overview**

CLI  
 │  
 ▼  
Control Plane  
 │  
 ├── Contracts  
 ├── Observability  
 ├── Migration  
 ├── State  
 └── Blueprints  
 │  
 ▼  
Adapters  
 │  
 ├── Ingestion  
 ├── Transformation  
 ├── Quality  
 └── Alerting  
 │  
 ▼  
Providers

---

# **Pull Request Checklist**

Every PR must include:

□ Tests

□ Documentation

□ Type hints

□ Acceptance criteria

□ Example usage

□ Architecture impact notes

---

# **Definition of Done**

A story is complete when:

* tests pass  
* lint passes  
* typing passes  
* docs updated  
* examples included  
* acceptance criteria satisfied

---

# **Security Rules**

Never commit:

* credentials  
* API keys  
* connection strings  
* secrets

Use:

.env

or environment variables.

---

# **AI Development Rules**

AI recommendations:

Allowed

AI autonomous actions:

Not allowed

AI must always return structured output.

AI never bypasses contracts.

---

# **Incident Response**

If a release breaks:

1. Reproduce  
2. Diagnose  
3. Write RCA  
4. Add regression test  
5. Deploy fix

Never patch without a test.

---

# **First Tasks For New Engineers**

1. Understand architecture  
2. Run blueprint locally  
3. Create a simple contract  
4. Create a quality check  
5. Create a migration test  
6. Submit first pull request

Success:

Engineer becomes productive within one day.

