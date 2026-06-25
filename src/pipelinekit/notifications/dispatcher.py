"""Route notifications to the configured adapter.

The dispatcher is the safety boundary for alerting: ``dispatch`` never raises
and a broken channel never blocks pipeline state recording. Notifications are
only sent when ``notifications.enabled`` is True (SPEC-008).
"""

from __future__ import annotations

import os

from pipelinekit.adapters.alerts.resend.adapter import ResendNotificationAdapter
from pipelinekit.config.schema import NotificationsSection
from pipelinekit.contracts.models import ContractResult
from pipelinekit.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationResult,
)
from pipelinekit.notifications.templates import (
    contract_violated_notification,
    pipeline_failed_notification,
    pipeline_succeeded_notification,
)
from pipelinekit.runtime.result import PipelineResult


class NotificationDispatcher:
    """Builds and dispatches notifications from a pipeline outcome."""

    def __init__(self, config: NotificationsSection) -> None:
        self.config = config
        self._adapter: ResendNotificationAdapter | None = None

    def initialize(self) -> None:
        """Build the notification adapter from config. Never raises."""
        if self.config.provider == "resend":
            api_key = os.environ.get("RESEND_API_KEY", "")
            self._adapter = ResendNotificationAdapter(
                api_key=api_key, from_address=self.config.from_address
            )

    def dispatch(self, notification: Notification) -> NotificationResult:
        """Send a single notification. Never raises — returns a result."""
        if self._adapter is None:
            return NotificationResult(
                sent=False,
                channel=notification.channel,
                recipient=notification.recipient,
                error="[PK-NOTIFY-001] No notification adapter configured",
            )
        try:
            return self._adapter.send(notification)
        except Exception as exc:
            return NotificationResult(
                sent=False,
                channel=notification.channel,
                recipient=notification.recipient,
                error=f"[PK-NOTIFY-002] {exc}",
            )

    def notify_pipeline_result(
        self,
        result: PipelineResult,
        contract_results: list[ContractResult] | None = None,
    ) -> list[NotificationResult]:
        """Build and dispatch all applicable notifications for a run."""
        if not self.config.enabled:
            return []

        notifications = self._build_notifications(result, contract_results or [])
        results: list[NotificationResult] = []
        for notification in notifications:
            for recipient in self.config.recipients:
                addressed = notification.model_copy(update={"recipient": recipient})
                results.append(self.dispatch(addressed))
        return results

    def _build_notifications(
        self, result: PipelineResult, contract_results: list[ContractResult]
    ) -> list[Notification]:
        notifications: list[Notification] = []
        events = self.config.notify_on

        if "pipeline_failed" in events and result.failed():
            notifications.append(pipeline_failed_notification(result))

        has_violations = any(not cr.passed() for cr in contract_results)
        if "contract_violated" in events and has_violations:
            notifications.append(
                contract_violated_notification(result, contract_results)
            )

        if "pipeline_succeeded" in events and result.succeeded():
            notifications.append(pipeline_succeeded_notification(result))

        return notifications

    @staticmethod
    def _supported_channels() -> set[NotificationChannel]:
        """Channels implemented in Phase 3 (email only)."""
        return {NotificationChannel.EMAIL}
