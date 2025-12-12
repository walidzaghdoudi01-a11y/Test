import asyncio
import uuid
from datetime import datetime

import pytest

from services.monitoring.models import AlertSeverity, AlertStatus, DetectionEvent
from services.monitoring.notifier import (
    MockEmailNotifier,
    MockWebhookNotifier,
    NotificationManager,
)
from services.monitoring.processor import StreamingProcessor


@pytest.fixture
async def processor():
    """Create streaming processor for testing"""
    notification_manager = NotificationManager()
    notification_manager.add_notifier("email", MockEmailNotifier())
    notification_manager.add_notifier("webhook", MockWebhookNotifier())
    
    processor = StreamingProcessor(
        notification_manager=notification_manager,
        alert_threshold=10,
        window_seconds=60,
    )
    
    task = asyncio.create_task(processor.start())
    
    yield processor
    
    await processor.stop()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_ingest_single_event(processor):
    """Test ingesting a single detection event"""
    event = DetectionEvent(
        event_id="test-event-1",
        timestamp=datetime.utcnow(),
        source="test-source",
        severity=AlertSeverity.HIGH,
        title="Test Event",
        description="Test event description",
        indicators=["192.168.1.100"],
        affected_assets=["server-1"],
    )
    
    await processor.ingest_event(event)
    await asyncio.sleep(0.2)
    
    assert len(processor.event_history) > 0
    assert processor.events_by_severity[AlertSeverity.HIGH] > 0


@pytest.mark.asyncio
async def test_critical_alert_generation(processor):
    """Test that critical events generate alerts"""
    event = DetectionEvent(
        event_id="critical-event",
        timestamp=datetime.utcnow(),
        source="detection-engine",
        severity=AlertSeverity.CRITICAL,
        title="Critical Security Event",
        description="Critical threat detected",
        indicators=["203.0.113.10"],
        affected_assets=["prod-server"],
    )
    
    await processor.ingest_event(event)
    await asyncio.sleep(0.2)
    
    alerts = processor.get_alerts(severity=AlertSeverity.CRITICAL)
    assert len(alerts) > 0
    assert alerts[0].title == "Critical Security Event"
    assert alerts[0].status == AlertStatus.NEW


@pytest.mark.asyncio
async def test_alert_burst_simulation(processor):
    """Test burst detection with many rapid events"""
    processor.burst_threshold = 10
    
    events = []
    for i in range(15):
        event = DetectionEvent(
            event_id=f"burst-event-{i}",
            timestamp=datetime.utcnow(),
            source="scanner",
            severity=AlertSeverity.MEDIUM,
            title=f"Burst Event {i}",
            description=f"Event {i} in burst",
            indicators=[f"10.0.0.{i}"],
            affected_assets=["test-asset"],
        )
        events.append(event)
        await processor.ingest_event(event)
    
    await asyncio.sleep(0.5)
    
    assert len(processor.event_history) >= 15
    
    all_alerts = processor.get_alerts()
    burst_alerts = [a for a in all_alerts if "burst" in a.title.lower()]
    assert len(burst_alerts) > 0, "Burst alert should be generated"


@pytest.mark.asyncio
async def test_notification_sending(processor):
    """Test that notifications are sent for high severity alerts"""
    email_notifier = processor.notification_manager.notifiers["email"]
    webhook_notifier = processor.notification_manager.notifiers["webhook"]
    
    initial_email_count = len(email_notifier.sent_alerts)
    initial_webhook_count = len(webhook_notifier.sent_alerts)
    
    event = DetectionEvent(
        event_id="notification-test",
        timestamp=datetime.utcnow(),
        source="test",
        severity=AlertSeverity.HIGH,
        title="Test Notification",
        description="Testing notification delivery",
        indicators=["198.51.100.20"],
        affected_assets=["test-server"],
    )
    
    await processor.ingest_event(event)
    await asyncio.sleep(0.2)
    
    assert len(email_notifier.sent_alerts) > initial_email_count
    assert len(webhook_notifier.sent_alerts) > initial_webhook_count


@pytest.mark.asyncio
async def test_alert_status_update(processor):
    """Test updating alert status"""
    event = DetectionEvent(
        event_id="status-test",
        timestamp=datetime.utcnow(),
        source="test",
        severity=AlertSeverity.CRITICAL,
        title="Status Test Alert",
        description="Testing status updates",
        indicators=[],
        affected_assets=[],
    )
    
    await processor.ingest_event(event)
    await asyncio.sleep(0.2)
    
    alerts = processor.get_alerts(limit=1)
    assert len(alerts) > 0
    
    alert_id = alerts[0].alert_id
    
    success = await processor.update_alert_status(alert_id, AlertStatus.ACKNOWLEDGED)
    assert success
    
    updated_alert = processor.get_alert(alert_id)
    assert updated_alert.status == AlertStatus.ACKNOWLEDGED


@pytest.mark.asyncio
async def test_dashboard_metrics(processor):
    """Test dashboard metrics collection"""
    for i in range(5):
        event = DetectionEvent(
            event_id=f"metrics-event-{i}",
            timestamp=datetime.utcnow(),
            source="test-source",
            severity=AlertSeverity.HIGH,
            title=f"Metrics Test {i}",
            description="Test event for metrics",
            indicators=["192.168.1.100", "malicious-site.evil"],
            affected_assets=["asset-1"],
        )
        await processor.ingest_event(event)
    
    await asyncio.sleep(0.3)
    
    metrics = processor.get_dashboard_metrics()
    
    assert metrics.alerts_total > 0
    assert metrics.events_processed_last_hour > 0
    assert len(metrics.top_indicators) > 0
    assert len(metrics.top_sources) > 0


@pytest.mark.asyncio
async def test_high_volume_processing(processor):
    """Test processing high volume of events"""
    event_count = 100
    
    for i in range(event_count):
        event = DetectionEvent(
            event_id=f"volume-{i}",
            timestamp=datetime.utcnow(),
            source=f"source-{i % 5}",
            severity=AlertSeverity.MEDIUM,
            title=f"Volume Test {i}",
            description="High volume test",
            indicators=[f"10.0.{i // 256}.{i % 256}"],
            affected_assets=["test"],
        )
        await processor.ingest_event(event)
    
    await asyncio.sleep(1.0)
    
    assert len(processor.event_history) >= event_count
    assert processor.event_queue.qsize() == 0, "All events should be processed"


@pytest.mark.asyncio
async def test_indicator_tracking(processor):
    """Test that repeated indicators are tracked"""
    indicator = "192.168.1.100"
    
    for i in range(5):
        event = DetectionEvent(
            event_id=f"indicator-{i}",
            timestamp=datetime.utcnow(),
            source="test",
            severity=AlertSeverity.LOW,
            title=f"Indicator Test {i}",
            description="Testing indicator tracking",
            indicators=[indicator],
            affected_assets=[],
        )
        await processor.ingest_event(event)
    
    await asyncio.sleep(0.3)
    
    assert processor.indicator_counts[indicator] == 5
