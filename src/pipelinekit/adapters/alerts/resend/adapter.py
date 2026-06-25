"""Resend email notification adapter.

Implements :class:`BaseAdapter` and adds :meth:`send`. **All ``resend`` imports
stay inside this file** (lazily, inside methods) — never in the dispatcher,
runtime, or CLI. The API key comes from the ``RESEND_API_KEY`` environment
variable via the dispatcher; it is never hardcoded or logged (ADR-005, BYOK).

``send`` never raises — it returns a :class:`NotificationResult` with
``sent=False`` on failure, mapping Resend errors to ``PK-NOTIFY-*`` codes
(SPEC-008).
"""

from __future__ import annotations

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.notifications.models import Notification, NotificationResult
from pipelinekit.runtime.result import PipelineStatus, StepResult

_STEP = "notification"


class ResendNotificationAdapter(BaseAdapter):
    """Sends notifications via the Resend email API. Email only in Phase 3."""

    def __init__(self, api_key: str, from_address: str) -> None:
        self.api_key = api_key
        self.from_address = from_address

    # -- BaseAdapter ---------------------------------------------------------

    def initialize(self) -> None:
        """No-op initialization; key validity is checked at send time."""

    def validate(self) -> StepResult:
        """Verify an API key is configured, without sending anything."""
        if not self.api_key:
            return StepResult(
                _STEP,
                PipelineStatus.INVALID,
                0.0,
                error_code="PK-NOTIFY-004",
                error_msg="RESEND_API_KEY is not set",
            )
        return StepResult(_STEP, PipelineStatus.VALID, 0.0)

    def execute(self) -> StepResult:
        """Not used directly — notifications are sent via :meth:`send`."""
        return StepResult(_STEP, PipelineStatus.SUCCESS, 0.0)

    def status(self) -> dict:
        """Return adapter status (never exposes the API key)."""
        return {
            "adapter": "resend",
            "step": _STEP,
            "from_address": self.from_address,
            "api_key_present": bool(self.api_key),
        }

    # -- notification API ----------------------------------------------------

    def send(self, notification: Notification) -> NotificationResult:
        """Send one notification via Resend. Never raises."""
        if not self.api_key:
            return self._failure(
                notification, "PK-NOTIFY-004", "RESEND_API_KEY not set"
            )
        if not notification.recipient:
            return self._failure(
                notification, "PK-NOTIFY-003", "Recipient address is empty"
            )

        try:
            import resend  # noqa: PLC0415 — provider import isolated to this file

            resend.api_key = self.api_key
            resend.Emails.send(
                {
                    "from": self.from_address,
                    "to": [notification.recipient],
                    "subject": notification.subject,
                    "text": notification.message,
                }
            )
        except Exception as exc:
            return self._failure(notification, "PK-NOTIFY-002", str(exc))

        return NotificationResult(
            sent=True,
            channel=notification.channel,
            recipient=notification.recipient,
        )

    @staticmethod
    def _failure(
        notification: Notification, code: str, detail: str
    ) -> NotificationResult:
        return NotificationResult(
            sent=False,
            channel=notification.channel,
            recipient=notification.recipient,
            error=f"[{code}] {detail}",
        )
