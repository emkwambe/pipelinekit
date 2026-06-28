# PipelineKit Installation Guide

**Version:** 0.1.0  
**Last updated:** June 28, 2026

---

## Requirements

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | 3.12 recommended |
| Git | Any recent | For cloning the repo |
| Poetry | 1.8+ | Dependency management |
| Docker Desktop | Any recent | Required for Blueprint #001 local verification |
| dbt-core | 1.6+ | Installed automatically via Poetry |

**AI provider (choose one):**

| Provider | Requirement | Use case |
|---|---|---|
| Anthropic | `ANTHROPIC_API_KEY` | Recommended for diagnostics |
| OpenAI | `OPENAI_API_KEY` | Alternative |
| Ollama | Ollama running locally | Air-gapped / no API key |
| Mistral | `MISTRAL_API_KEY` | EU GDPR-compliant |
| DeepSeek | `DEEPSEEK_API_KEY` | Cost-sensitive |

At least one provider is required for `pipelinekit diagnose` and `pipelinekit generate blueprint`. All other commands work without an AI provider.

---

## Windows (PowerShell)

### Step 1 — Install Python 3.11+

Download from https://python.org/downloads — choose Python 3.12.

During install: ✅ **Add Python to PATH**

Verify:
```powershell
python --version
# Python 3.12.x
```

### Step 2 — Install Poetry

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

Add Poetry to PATH (restart PowerShell after):
```powershell
$env:PATH += ";$env:APPDATA\Python\Scripts"
```

Verify:
```powershell
poetry --version
# Poetry 2.x.x
```

### Step 3 — Install Git

Download from https://git-scm.com/download/win

Verify:
```powershell
git --version
```

### Step 4 — Clone and install PipelineKit

```powershell
git clone https://github.com/emkwambe/pipelinekit.git
cd pipelinekit
poetry install
```

### Step 5 — Set your AI provider key

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-api03-YOUR-KEY-HERE"
```

To persist across sessions add to your PowerShell profile:
```powershell
Add-Content $PROFILE "`n`$env:ANTHROPIC_API_KEY = 'sk-ant-api03-YOUR-KEY-HERE'"
```

### Step 6 — Verify installation

```powershell
poetry run pipelinekit health --strict
```

Expected output:
```
✓ Python 3.11+
✓ dbt-core installed
✓ dlt installed
✓ soda-core installed
✓ Docker running
✓ ANTHROPIC_API_KEY set
All health checks passed.
```

If any check fails — see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### Step 7 — Install your first blueprint

```powershell
poetry run pipelinekit blueprint install postgres-to-snowflake
poetry run pipelinekit blueprint info postgres-to-snowflake
```

---

## macOS

### Step 1 — Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2 — Install Python 3.12

```bash
brew install python@3.12
python3 --version
# Python 3.12.x
```

### Step 3 — Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add to PATH (add to `~/.zshrc` or `~/.bashrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

Reload:
```bash
source ~/.zshrc
poetry --version
```

### Step 4 — Install Git

```bash
brew install git
git --version
```

### Step 5 — Install Docker Desktop

Download from https://docker.com/products/docker-desktop

Start Docker Desktop and verify:
```bash
docker --version
docker ps
```

### Step 6 — Clone and install PipelineKit

```bash
git clone https://github.com/emkwambe/pipelinekit.git
cd pipelinekit
poetry install
```

### Step 7 — Set your AI provider key

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-YOUR-KEY-HERE"
```

To persist:
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-YOUR-KEY-HERE"' >> ~/.zshrc
source ~/.zshrc
```

### Step 8 — Verify installation

```bash
poetry run pipelinekit health --strict
```

### Step 9 — Install your first blueprint

```bash
poetry run pipelinekit blueprint install postgres-to-snowflake
```

---

## Linux (Ubuntu/Debian)

### Step 1 — Install Python 3.12

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip -y
python3.12 --version
```

### Step 2 — Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
poetry --version
```

### Step 3 — Install Git and Docker

```bash
sudo apt install git -y

# Docker
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect
docker --version
```

### Step 4 — Clone and install PipelineKit

```bash
git clone https://github.com/emkwambe/pipelinekit.git
cd pipelinekit
poetry install
```

### Step 5 — Set your AI provider key

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-YOUR-KEY-HERE"
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-YOUR-KEY-HERE"' >> ~/.bashrc
source ~/.bashrc
```

### Step 6 — Verify installation

```bash
poetry run pipelinekit health --strict
```

---

## Using Ollama (no API key required)

If you prefer to run locally without any cloud AI provider:

### Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:** Download from https://ollama.ai

### Pull a model

```bash
ollama pull llama3.1
```

### Use with PipelineKit

```bash
poetry run pipelinekit diagnose --provider ollama
poetry run pipelinekit generate blueprint --source stripe --destination snowflake --provider ollama --plan
```

No API key required. Runs entirely locally. Air-gap capable.

---

## Verify everything works

Run the full verification sequence:

```bash
# 1. Health check
poetry run pipelinekit health --strict

# 2. List available blueprints from registry
poetry run pipelinekit blueprint search postgres

# 3. Install a blueprint
poetry run pipelinekit blueprint install postgres-to-snowflake

# 4. Validate the blueprint config
poetry run pipelinekit validate

# 5. AI blueprint proposal (requires AI provider)
poetry run pipelinekit generate blueprint \
  --source stripe \
  --destination snowflake \
  --tables charges,customers \
  --plan
```

If all five steps complete without error — PipelineKit is fully installed and operational.

---

## Common installation issues

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for the top 10 errors and their fixes.

Most common on first install:
- Docker not running → start Docker Desktop before `pipelinekit health`
- API key not set → `PK-AI-001` error on any AI command
- Poetry not in PATH → restart terminal after install

---

## Next steps

- [Quickstart](../guides/QUICKSTART.md) — run your first pipeline
- [Blueprint Catalog](../../registry/v1/catalog.json) — browse available blueprints
- [CLI Reference](CLI-REFERENCE.md) — all commands and flags
- [pipelinekit.dev](https://pipelinekit.dev) — product website

---

*PyPI package coming soon. Star the repo to be notified: https://github.com/emkwambe/pipelinekit*
