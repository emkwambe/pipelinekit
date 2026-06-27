"""Tests for SlackNotificationAdapter (SPEC-008, Sprint 8-1). Webhook POST mocked."""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

from pipelinekit.adapters.alerts.slack.adapter import SlackNotificationAdapter
from pipelinekit.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationSeverity,
)

_WEBHOOK = "https://hooks.slack.com/services/T000/B000/XXXXXXXX"
_URLOPEN = "pipelinekit.adapters.alerts.slack.adapter.urllib.request.urlopen"


def _notification() -> Notification:
    return Notification(
        channel=NotificationChannel.SLACK,
        recipient="#alerts",
        severity=NotificationSeverity.ERROR,
        subject="[PipelineKit] Pipeline failed — demo",
        message="Pipeline failed",
        evidence={
            "status": "failed",
            "failed_steps": [
                {"step": "ingestion", "error_code": "PK-ADAPTER-001", "error_msg": "x"}
            ],
        },
        pipeline_name="demo",
        run_id="run-abc123",
        error_code="PK-ADAPTER-001",
    )


def _ok_response(code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = code
    resp.getcode.return_value = code
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


def test_send_posts_slack_block_payload():
    """send() POSTs a Slack Block Kit payload (header / section / context)."""
    adapter = SlackNotificationAdapter(webhook_url=_WEBHOOK)
    captured: dict = {}

    def _fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _ok_response()

    with patch(_URLOPEN, side_effect=_fake_urlopen):
        result = adapter.send(_notification())

    assert result.sent is True
    assert captured["url"] == _WEBHOOK
    assert captured["method"] == "POST"
    body = captured["body"]
    assert body["text"] == "PipelineKit Alert"
    blocks = body["blocks"]
    assert blocks[0]["type"] == "header"
    assert "Pipeline Failed: demo" in blocks[0]["text"]["text"]
    assert blocks[1]["type"] == "section"
    field_texts = [f["text"] for f in blocks[1]["fields"]]
    assert any("PK-ADAPTER-001" in t for t in field_texts)
    assert any("ingestion" in t for t in field_texts)
    assert any("run-abc123" in t for t in field_texts)
    assert blocks[2]["type"] == "context"


def test_send_missing_webhook_returns_pk_notify_003():
    """No webhook URL configured -> PK-NOTIFY-003, never touches the network."""
    adapter = SlackNotificationAdapter(webhook_url="")
    with patch(_URLOPEN, side_effect=AssertionError("network must not be called")):
        result = adapter.send(_notification())
    assert result.sent is False
    assert result.error is not None
    assert "PK-NOTIFY-003" in result.error


def test_send_non_200_returns_pk_notify_004():
    """A non-200 webhook response -> PK-NOTIFY-004."""
    adapter = SlackNotificationAdapter(webhook_url=_WEBHOOK)
    http_error = urllib.error.HTTPError(_WEBHOOK, 500, "Server Error", {}, None)
    with patch(_URLOPEN, side_effect=http_error):
        result = adapter.send(_notification())
    assert result.sent is False
    assert result.error is not None
    assert "PK-NOTIFY-004" in result.error


def test_send_success_returns_true():
    """A 200 response -> NotificationResult(sent=True, error=None)."""
    adapter = SlackNotificationAdapter(webhook_url=_WEBHOOK)
    with patch(_URLOPEN, return_value=_ok_response(200)):
        result = adapter.send(_notification())
    assert result.sent is True
    assert result.error is None
    assert result.channel == NotificationChannel.SLACK
