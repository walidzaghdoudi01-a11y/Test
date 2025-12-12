import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

import aiosmtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from services.monitoring.models import (
    Alert,
    EmailNotificationConfig,
    NotificationType,
    WebhookNotificationConfig,
)


class Notifier(ABC):
    """Base class for alert notifications"""

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """Send notification for an alert"""
        pass


class EmailNotifier(Notifier):
    """Email notification sender"""

    def __init__(self, config: EmailNotificationConfig):
        self.config = config

    async def send(self, alert: Alert) -> bool:
        """Send email notification"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"
            message["From"] = self.config.from_address
            message["To"] = ", ".join(self.config.to_addresses)

            body = self._format_email_body(alert)
            text_part = MIMEText(body, "plain")
            message.attach(text_part)

            await aiosmtplib.send(
                message,
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                username=self.config.smtp_username,
                password=self.config.smtp_password,
                use_tls=self.config.use_tls,
            )

            return True
        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False

    def _format_email_body(self, alert: Alert) -> str:
        """Format email body"""
        return f"""
Alert Details
=============

Alert ID: {alert.alert_id}
Severity: {alert.severity.value.upper()}
Status: {alert.status.value}
Created: {alert.created_at.isoformat()}

Title: {alert.title}

Description:
{alert.description}

Source: {alert.source}
Event ID: {alert.event_id}

Indicators: {', '.join(alert.indicators) if alert.indicators else 'None'}
Affected Assets: {', '.join(alert.affected_assets) if alert.affected_assets else 'None'}
Tags: {', '.join(alert.tags) if alert.tags else 'None'}

---
This is an automated alert from the Threat Intelligence Monitoring System.
"""


class WebhookNotifier(Notifier):
    """Webhook notification sender"""

    def __init__(self, config: WebhookNotificationConfig):
        self.config = config

    async def send(self, alert: Alert) -> bool:
        """Send webhook notification"""
        try:
            payload = {
                "alert_id": alert.alert_id,
                "event_id": alert.event_id,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "title": alert.title,
                "description": alert.description,
                "source": alert.source,
                "created_at": alert.created_at.isoformat(),
                "indicators": alert.indicators,
                "affected_assets": alert.affected_assets,
                "tags": alert.tags,
                "metadata": alert.metadata,
            }

            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=self.config.method,
                    url=self.config.url,
                    json=payload,
                    headers=self.config.headers,
                    timeout=self.config.timeout_seconds,
                )

                return response.status_code < 400

        except Exception as e:
            print(f"Failed to send webhook notification: {e}")
            return False


class MockEmailNotifier(Notifier):
    """Mock email notifier for testing"""

    def __init__(self):
        self.sent_alerts: List[Alert] = []

    async def send(self, alert: Alert) -> bool:
        """Mock send email"""
        await asyncio.sleep(0.01)
        self.sent_alerts.append(alert)
        return True


class MockWebhookNotifier(Notifier):
    """Mock webhook notifier for testing"""

    def __init__(self):
        self.sent_alerts: List[Alert] = []

    async def send(self, alert: Alert) -> bool:
        """Mock send webhook"""
        await asyncio.sleep(0.01)
        self.sent_alerts.append(alert)
        return True


class NotificationManager:
    """Manages multiple notification channels"""

    def __init__(self):
        self.notifiers: dict[str, Notifier] = {}

    def add_notifier(self, name: str, notifier: Notifier):
        """Add a notification channel"""
        self.notifiers[name] = notifier

    async def send_alert(self, alert: Alert, channels: List[str] = None) -> dict[str, bool]:
        """Send alert to specified channels (or all if not specified)"""
        if channels is None:
            channels = list(self.notifiers.keys())

        results = {}
        for channel in channels:
            if channel in self.notifiers:
                success = await self.notifiers[channel].send(alert)
                results[channel] = success
            else:
                results[channel] = False

        return results

    async def send_alert_batch(self, alerts: List[Alert]) -> dict[str, int]:
        """Send multiple alerts"""
        success_counts = {name: 0 for name in self.notifiers.keys()}

        for alert in alerts:
            results = await self.send_alert(alert)
            for channel, success in results.items():
                if success:
                    success_counts[channel] += 1

        return success_counts
