"""Slack incoming-webhook notification adapter.

Sends pipeline failure alerts to a Slack channel via an incoming webhook. **All
HTTP uses the standard library (``urllib``)** — no new dependency (same approach
as the registry client). The webhook URL comes from the ``SLACK_WEBHOOK_URL``
environment variable via the dispatcher; it is never hardcoded or logged
(ADR-005, BYOK).

``send`` never raises — it returns a :class:`NotificationResult` with
``sent=False`` on failure, mapping errors to ``PK-NOTIFY-*`` codes (SPEC-008):
``PK-NOTIFY-003`` when the webhook URL is not configured, ``PK-NOTIFY-004`` when
the webhook request fails (non-200 or transport error).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

from pipelinekit.adapters.base import BaseAdapter
from pipelinekit.notifications.models import Notification, NotificationResult
from pipelinekit.runtime.result import PipelineStatus, StepResult

_STEP = "notification"
_TIMEOUT = 10
_USER_AGENT = "PipelineKit/1.0 (https://pipelinekit.dev)"


class SlackNotificationAdapter(BaseAdapter):
    """Sends pipeline alerts to a Slack channel via an incoming webhook.

    Config: ``webhook_url`` from ``${SLACK_WEBHOOK_URL}``.
    """

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    # -- BaseAdapter ---------------------------------------------------------

    def initialize(self) -> None:
        """No-op initialization; webhook validity is checked at send time."""

    def validate(self) -> StepResult:
        """Verify a webhook URL is configured, without sending anything."""
        if not self.webhook_url:
            return StepResult(
                _STEP,
                PipelineStatus.INVALID,
                0.0,
                error_code="PK-NOTIFY-003",
                error_msg="SLACK_WEBHOOK_URL is not set",
            )
        return StepResult(_STEP, PipelineStatus.VALID, 0.0)

    def execute(self) -> StepResult:
        """Not used directly — notifications are sent via :meth:`send`."""
        return StepResult(_STEP, PipelineStatus.SUCCESS, 0.0)

    def status(self) -> dict:
        """Return adapter status (never exposes the webhook URL)."""
        return {
            "adapter": "slack",
            "step": _STEP,
            "webhook_present": bool(self.webhook_url),
        }

    # -- notification API ----------------------------------------------------

    def send(self, notification: Notification) -> NotificationResult:
        """Send one alert to Slack. Never raises."""
        if not self.webhook_url:
            return self._failure(
                notification, "PK-NOTIFY-003", "SLACK_WEBHOOK_URL not set"
            )

        payload = self._build_payload(notification)
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.webhook_url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": _USER_AGENT},
        )
        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
                code = getattr(response, "status", None) or response.getcode()
                if code != 200:
                    return self._failure(
                        notification,
                        "PK-NOTIFY-004",
                        f"Slack webhook returned HTTP {code}",
                    )
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return self._failure(
                notification, "PK-NOTIFY-004", f"Slack webhook request failed: {exc}"
            )

        return NotificationResult(
            sent=True,
            channel=notification.channel,
            recipient=notification.recipient,
        )

    # -- payload -------------------------------------------------------------

    @staticmethod
    def _build_payload(notification: Notification) -> dict:
        """Render the Slack Block Kit payload from a notification."""
        evidence = notification.evidence or {}
        pipeline_name = notification.pipeline_name or "unknown"
        status = str(evidence.get("status") or notification.severity.value)
        error_code = notification.error_code or "—"
        failed_steps = evidence.get("failed_steps") or []
        failed_step = (
            failed_steps[0].get("step", "—")
            if failed_steps
            else str(evidence.get("failed_step") or "—")
        )
        run_id = notification.run_id or "—"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "text": "PipelineKit Alert",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"⚠️ Pipeline Failed: {pipeline_name}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Status:*\n{status}"},
                        {"type": "mrkdwn", "text": f"*Error:*\n{error_code}"},
                        {"type": "mrkdwn", "text": f"*Step:*\n{failed_step}"},
                        {"type": "mrkdwn", "text": f"*Run ID:*\n{run_id}"},
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"PipelineKit | {timestamp}"}
                    ],
                },
            ],
        }

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
