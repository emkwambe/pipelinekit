"""Tests for notification models (SPEC-008, contracts/notification.yaml)."""

from __future__ import annotations

from pipelinekit.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationResult,
    NotificationSeverity,
)


def test_notification_satisfies_contract_fields():
    """Notification carries the contract-required fields."""
    n = Notification(
        channel=NotificationChannel.EMAIL,
        recipient="data-team@example.com",
        severity=NotificationSeverity.ERROR,
        subject="[PipelineKit] Pipeline failed",
        message="Pipeline failed.",
        evidence={"error_code": "PK-ADAPTER-001"},
    )
    # contracts/notification.yaml requires: channel, recipient, severity,
    # message, evidence.
    assert n.channel == NotificationChannel.EMAIL
    assert n.recipient == "data-team@example.com"
    assert n.severity == NotificationSeverity.ERROR
    assert n.message
    assert isinstance(n.evidence, dict)


def test_notification_result_sent_false_on_failure():
    """NotificationResult records a failed delivery."""
    result = NotificationResult(
        sent=False,
        channel=NotificationChannel.EMAIL,
        recipient="x@example.com",
        error="[PK-NOTIFY-002] delivery failed",
    )
    assert result.sent is False
    assert result.error is not None


def test_evidence_is_structured_not_string():
    """The evidence field is a structured dict, not free-form text."""
    n = Notification(
        channel=NotificationChannel.EMAIL,
        recipient="x@example.com",
        severity=NotificationSeverity.WARNING,
        subject="s",
        message="m",
        evidence={"violations": [{"table": "orders", "code": "PK-CONTRACT-002"}]},
    )
    assert isinstance(n.evidence, dict)
    assert n.evidence["violations"][0]["table"] == "orders"
