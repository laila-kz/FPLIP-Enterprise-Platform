"""
slack_alert.py — Shared Slack notification helper
"""

import os
import json
import urllib.request


def post_slack_message(text: str) -> None:
    """Post a message to Slack via webhook."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ SLACK_WEBHOOK_URL not set — skipping Slack notification")
        return

    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req)
        print("✅ Slack notification sent")
    except Exception as e:
        print(f"❌ Failed to send Slack notification: {e}")