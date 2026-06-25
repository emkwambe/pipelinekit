"""Tests for ResendNotificationAdapter (SPEC-008). Resend is mocked."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from pipelinekit.adapters.alerts.resend.adapter import ResendNotificationAdapter
from pipelinekit.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationSeverity,
)


def _notification(recipient: str = "data-team@example.com") -> Notification:
    return Notification(
        channel=NotificationChannel.EMAIL,
        recipient=recipient,
        severity=NotificationSeverity.ERROR,
        subject="[PipelineKit] Pipeline failed",
        message="Pipeline failed.",
        evidence={"error_code": "PK-ADAPTER-001"},
    )


def test_send_success(monkeypatch):
    """send() returns sent=True when Resend accepts the email (mocked)."""
    adapter = ResendNotificationAdapter(api_key="re_test", from_address="x@example.com")
    fake_resend = MagicMock()
    with patch.dict("sys.modules", {"resend": fake_resend}):
        result = adapter.send(_notification())
    assert result.sent is True
    fake_resend.Emails.send.assert_called_once()


def test_send_failure_maps_to_notify_002(monkeypatch):
    """send() returns sent=False with PK-NOTIFY-002 on a Resend error (mocked)."""
    adapter = ResendNotificationAdapter(api_key="re_test", from_address="x@example.com")
    fake_resend = MagicMock()
    fake_resend.Emails.send.side_effect = Exception("api down")
    with patch.dict("sys.modules", {"resend": fake_resend}):
        result = adapter.send(_notification())
    assert result.sent is False
    assert "PK-NOTIFY-002" in (result.error or "")


def test_send_missing_key_maps_to_notify_004():
    """send() returns PK-NOTIFY-004 when no API key is configured."""
    adapter = ResendNotificationAdapter(api_key="", from_address="x@example.com")
    result = adapter.send(_notification())
    assert result.sent is False
    assert "PK-NOTIFY-004" in (result.error or "")


def test_no_resend_imports_outside_adapter_file():
    """No source file outside the Resend adapter imports the resend library."""
    src_root = Path(__file__).resolve().parents[2] / "src" / "pipelinekit"
    allowed = src_root / "adapters" / "alerts" / "resend" / "adapter.py"
    offenders = []
    for path in src_root.rglob("*.py"):
        if path == allowed:
            continue
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import resend", "from resend")):
                offenders.append(str(path))
                break
    assert offenders == [], f"resend imported outside adapter: {offenders}"
