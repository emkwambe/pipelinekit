"""Notification models — map to contracts/notification.yaml.

Required contract fields: ``channel``, ``recipient``, ``severity``, ``message``,
``evidence``. The ``evidence`` dict is structured (not free-form text) so it can
feed Phase 4 AI diagnostics.

See: SPEC-008.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class NotificationSeverity(str, Enum):
    """Severity of a notification."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Delivery channel. Only email is implemented in Phase 3."""

    EMAIL = "email"
    SLACK = "slack"  # Phase 4
    WEBHOOK = "webhook"  # Phase 4


class Notification(BaseModel):
    """A single notification (maps to contracts/notification.yaml)."""

    channel: NotificationChannel
    recipient: str
    severity: NotificationSeverity
    subject: str
    message: str
    evidence: dict = {}
    pipeline_name: str = ""
    run_id: str = ""
    error_code: Optional[str] = None


class NotificationResult(BaseModel):
    """Result of a single notification dispatch attempt."""

    sent: bool
    channel: NotificationChannel
    recipient: str
    error: Optional[str] = None
