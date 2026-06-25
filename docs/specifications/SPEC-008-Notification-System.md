# SPEC-008-Notification-System.md

**Status:** Implemented  
**Owner:** runtime-engineer  
**Phase:** 3 — Trust Layer  
**Date:** June 25, 2026  
**ADRs:** ADR-005 (BYOK), ADR-009 (Human-Readable), ADR-010 (Explainability Before Automation)  
**Contracts:** contracts/notification.yaml  
**Depends on:** SPEC-003 (Runtime), SPEC-004 (Contracts), SPEC-009 (Adapters)  
**MCP:** Resend — first MCP entry in the stack

---

## Purpose

Define the notification system — the mechanism by which PipelineKit alerts operators when pipelines fail, contracts are violated, or quality checks do not pass.

Notifications are not optional.
A pipeline that fails silently is a pipeline that cannot be trusted.
Every failure must produce actionable context — not just a subject line.

This SPEC also defines the first MCP entry: Resend for email delivery.

---

## Governing Rules (from contracts/notification.yaml)

- Notifications must include actionable context
- Failure notifications must include evidence
- Notification providers must be replaceable
- Required fields per contract: `channel`, `recipient`, `severity`, `message`, `evidence`
- Notifications are sent after pipeline execution — never during
- Notification failure must never block pipeline result recording
- AI may not trigger notifications autonomously — only post-execution dispatch

---

## Notification Model

```python
# src/pipelinekit/notifications/models.py

from enum import Enum
from pydantic import BaseModel
from typing import Optional

class NotificationSeverity(str, Enum):
    INFO    = "info"
    WARNING = "warning"
    ERROR   = "error"
    CRITICAL = "critical"

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"    # Phase 4
    WEBHOOK = "webhook"  # Phase 4

class Notification(BaseModel):
    """A single notification — maps to contracts/notification.yaml."""
    channel: NotificationChannel
    recipient: str
    severity: NotificationSeverity
    subject: str
    message: str
    evidence: dict = {}           # structured — feeds Phase 4 diagnostics
    pipeline_name: str = ""
    run_id: str = ""
    error_code: Optional[str] = None

class NotificationResult(BaseModel):
    """Result of a notification dispatch attempt."""
    sent: bool
    channel: NotificationChannel
    recipient: str
    error: Optional[str] = None
```

---

## Notification Dispatcher

```python
# src/pipelinekit/notifications/dispatcher.py

from pipelinekit.notifications.models import Notification, NotificationResult
from pipelinekit.runtime.result import PipelineResult
from pipelinekit.contracts.models import ContractResult
from pipelinekit.config.schema import NotificationsSection

class NotificationDispatcher:
    """Routes notifications to the correct adapter.

    Notification failure never raises — always returns NotificationResult.
    A broken notification channel must not corrupt pipeline state.

    Contract: contracts/notification.yaml
    """

    def __init__(self, config: NotificationsSection):
        self.config = config
        self._adapter = None

    def initialize(self) -> None:
        """Build the notification adapter from config."""
        ...

    def dispatch(self, notification: Notification) -> NotificationResult:
        """Send notification. Never raises — returns result."""
        ...

    def notify_pipeline_result(
        self,
        result: PipelineResult,
        contract_results: list[ContractResult] | None = None,
    ) -> list[NotificationResult]:
        """
        Build and dispatch notifications from a PipelineResult.
        Returns list of NotificationResult (one per channel).
        Only sends if notifications.enabled=True in config.
        """
        ...
```

---

## Notification Templates

Every notification type has a standard template.
Templates are human-readable — no opaque JSON blobs in subject lines.

### Pipeline failure notification

```
Subject: [PipelineKit] Pipeline failed — {pipeline_name}

Pipeline:   {pipeline_name}
Run ID:     {run_id}
Status:     FAILED
Error:      {error_code} — {error_message}
Started:    {started_at}
Duration:   {duration_s}s

Failed steps:
  - ingestion: PK-ADAPTER-001 Connection refused to postgres://...

Evidence:
  {evidence_json}

Next steps:
  Run 'pipelinekit doctor' to diagnose.
  Run 'pipelinekit status' to see run history.
```

### Contract violation notification

```
Subject: [PipelineKit] Contract violations — {pipeline_name}

Pipeline:   {pipeline_name}
Run ID:     {run_id}
Tables:     {violation_count} violation(s) across {table_count} table(s)

Violations:
  orders: [PK-CONTRACT-002] Freshness violation — data is 18h old (max: 12h)
  orders: [PK-CONTRACT-001] Required column missing — customer_id

Evidence:
  {evidence_json}

Next steps:
  Review contracts in {contracts_dir}
  Run 'pipelinekit validate --contracts' to recheck.
```

### Pipeline success notification (optional)

```
Subject: [PipelineKit] Pipeline succeeded — {pipeline_name}

Pipeline:   {pipeline_name}
Run ID:     {run_id}
Status:     SUCCESS
Duration:   {duration_s}s
Rows:       {rows_processed:,}
```

---

## Resend Adapter — Phase 3 MCP Entry

Resend is the Phase 3 notification provider.
It is the first MCP in the PipelineKit stack.

### Why Resend

- Simple developer API — matches PipelineKit's developer-first audience
- Replaceable — implements `BaseAdapter` behind the notification interface
- BYOK — customer provides their own Resend API key
- ADR-005 (BYOK) compliant

### Resend Adapter

```python
# src/pipelinekit/adapters/alerts/resend/adapter.py

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.notifications.models import Notification, NotificationResult
from pipelinekit.runtime.result import StepResult

class ResendNotificationAdapter(BaseAdapter):
    """Resend email notification adapter.

    All Resend-specific imports stay inside this file.
    The notification dispatcher calls this adapter — never Resend directly.

    Phase 3: email only.
    Phase 4: Slack, webhook via additional adapters.
    """

    def __init__(self, api_key: str, from_address: str):
        self.api_key = api_key
        self.from_address = from_address

    def initialize(self) -> None:
        """Validate Resend API key is set."""
        ...

    def validate(self) -> StepResult:
        """Verify Resend connectivity without sending."""
        ...

    def execute(self) -> StepResult:
        """Not used directly — use send() instead."""
        ...

    def status(self) -> dict:
        """Return adapter status."""
        ...

    def send(self, notification: Notification) -> NotificationResult:
        """
        Send a single notification via Resend API.
        Never raises — returns NotificationResult with sent=False on failure.
        Maps Resend errors to PK-NOTIFY-* codes.
        """
        ...
```

### MCP Registry Entry

Add to `.mcp/registry/servers.md`:

```markdown
## Resend

**Type:** Notification
**Phase:** 3
**Purpose:** Email delivery for pipeline alerts and contract violation notifications
**API:** https://api.resend.com
**Auth:** RESEND_API_KEY environment variable
**Status:** Active (Phase 3)
```

### pipelinekit.yaml — Notifications section (Phase 3)

```yaml
notifications:
  enabled: true
  channels:
    - type: email
      provider: resend
      api_key: "${RESEND_API_KEY}"
      from: "pipelinekit@yourdomain.com"
      recipients:
        - "data-team@yourcompany.com"
      on:
        - pipeline_failed
        - contract_violated
        - pipeline_succeeded   # optional
```

---

## Notification Trigger Rules

| Event | Severity | Default |
|---|---|---|
| Pipeline failed | ERROR | Always notify |
| Contract violated | WARNING | Always notify |
| Quality check failed | WARNING | Always notify |
| Pipeline succeeded | INFO | Opt-in only |
| Pipeline started | INFO | Off by default |

---

## Integration with PipelineRunner

`PipelineRunner.run()` dispatches notifications after execution — in the finally block, after state is updated.

```python
# runner.py (Phase 3 extension)

def run(self) -> PipelineResult:
    ...
    try:
        # existing execution logic
        ...
    finally:
        # always update state first
        state.db.update_run(...)
        # then dispatch notifications (failure must not corrupt state)
        if self.config.notifications.enabled:
            dispatcher = NotificationDispatcher(self.config.notifications)
            dispatcher.initialize()
            dispatcher.notify_pipeline_result(result, contract_results)
```

---

## Error Codes — Phase 3 Notifications

| Code | Meaning |
|---|---|
| `PK-NOTIFY-001` | Notification provider unavailable |
| `PK-NOTIFY-002` | Notification delivery failed |
| `PK-NOTIFY-003` | Invalid recipient address |
| `PK-NOTIFY-004` | API key missing or invalid |

---

## File Structure

```
src/pipelinekit/
├── notifications/
│   ├── __init__.py
│   ├── models.py         Notification, NotificationResult, enums
│   ├── dispatcher.py     NotificationDispatcher
│   └── templates.py      Message template builders
└── adapters/
    └── alerts/
        ├── __init__.py
        └── resend/
            ├── __init__.py
            └── adapter.py    ResendNotificationAdapter
```

---

## Constraints

- All Resend imports isolated inside `adapters/alerts/resend/adapter.py`
- Notification failure never raises — always returns `NotificationResult`
- Notification failure never blocks pipeline state update
- Notifications sent only when `notifications.enabled=True` in config
- API keys via environment variables only — never hardcoded
- No notification sending in tests — mock `ResendNotificationAdapter.send()`
- Phase 3 supports email only — Slack/webhook is Phase 4

---

## AI Guardrails

- No AI calls in Phase 3 notification system
- `Notification.evidence` structured for Phase 4 AI consumption
- AI may never trigger notifications autonomously
- AI may read notification history as diagnostic evidence in Phase 4

---

## Acceptance Criteria

```
✓ Notification model validates against contracts/notification.yaml requirements
✓ NotificationDispatcher.notify_pipeline_result() builds correct notifications
✓ NotificationDispatcher never raises on delivery failure
✓ ResendNotificationAdapter.send() returns NotificationResult with sent=False on error
✓ All Resend imports isolated inside adapter file
✓ Notification not sent when notifications.enabled=False
✓ PipelineRunner dispatches notifications after state update
✓ .mcp/registry/servers.md updated with Resend entry
✓ poetry run pytest tests/notifications/ → all tests pass
✓ coverage >= 80% on src/pipelinekit/notifications/
```

---

## Out of Scope

- Slack notifications — Phase 4
- Webhook notifications — Phase 4
- Notification history UI — Phase 4
- Notification templates customization — Phase 4
- PagerDuty integration — Phase 4
- SMS notifications — not planned
