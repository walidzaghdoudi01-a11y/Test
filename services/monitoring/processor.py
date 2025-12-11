import asyncio
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram

from services.monitoring.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    DashboardMetrics,
    DetectionEvent,
)
from services.monitoring.notifier import NotificationManager


event_counter = Counter(
    "detection_events_total",
    "Total number of detection events processed",
    ["source", "severity"],
)
alert_counter = Counter(
    "alerts_generated_total",
    "Total number of alerts generated",
    ["severity", "source"],
)
notification_counter = Counter(
    "notifications_sent_total",
    "Total number of notifications sent",
    ["channel", "success"],
)
processing_duration = Histogram(
    "event_processing_duration_seconds",
    "Duration of event processing",
)
active_alerts_gauge = Gauge(
    "active_alerts",
    "Number of active alerts",
    ["severity"],
)


class StreamingProcessor:
    """
    Streaming processor for detection events and alerts
    
    Subscribes to detection/logging topics, processes events,
    generates alerts, and triggers notifications.
    """

    def __init__(
        self,
        notification_manager: NotificationManager,
        alert_threshold: int = 10,
        window_seconds: int = 60,
    ):
        self.notification_manager = notification_manager
        self.alert_threshold = alert_threshold
        self.window_seconds = window_seconds

        self.event_queue: asyncio.Queue[DetectionEvent] = asyncio.Queue()
        self.alerts: Dict[str, Alert] = {}
        self.event_history: Deque[DetectionEvent] = deque(maxlen=10000)

        self.events_by_severity: Dict[AlertSeverity, int] = defaultdict(int)
        self.events_by_source: Dict[str, int] = defaultdict(int)
        self.indicator_counts: Dict[str, int] = defaultdict(int)

        self.running = False
        self.start_time = time.time()
        self.processing_times: Deque[float] = deque(maxlen=1000)

        self.burst_detection_enabled = True
        self.burst_threshold = 100
        self.recent_events: Deque[datetime] = deque(maxlen=1000)

    async def start(self):
        """Start the streaming processor"""
        self.running = True
        self.start_time = time.time()
        await asyncio.gather(
            self._process_events(),
            self._update_metrics(),
        )

    async def stop(self):
        """Stop the streaming processor"""
        self.running = False

    async def ingest_event(self, event: DetectionEvent):
        """Ingest a detection event for processing"""
        await self.event_queue.put(event)

    async def _process_events(self):
        """Main event processing loop"""
        while self.running:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._handle_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing event: {e}")

    async def _handle_event(self, event: DetectionEvent):
        """Handle a single detection event"""
        start_time = time.time()

        event_counter.labels(
            source=event.source,
            severity=event.severity.value,
        ).inc()

        self.event_history.append(event)
        self.events_by_severity[event.severity] += 1
        self.events_by_source[event.source] += 1

        for indicator in event.indicators:
            self.indicator_counts[indicator] += 1

        self.recent_events.append(event.timestamp)

        if self._should_create_alert(event):
            alert = await self._create_alert(event)
            await self._send_notifications(alert)

        if self.burst_detection_enabled:
            await self._check_burst()

        duration = time.time() - start_time
        self.processing_times.append(duration)
        processing_duration.observe(duration)

    def _should_create_alert(self, event: DetectionEvent) -> bool:
        """Determine if event should generate an alert"""
        if event.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            return True

        if event.severity == AlertSeverity.MEDIUM:
            for indicator in event.indicators:
                if self.indicator_counts[indicator] >= 3:
                    return True

        return False

    async def _create_alert(self, event: DetectionEvent) -> Alert:
        """Create alert from detection event"""
        alert_id = f"alert-{uuid.uuid4().hex[:12]}"

        alert = Alert(
            alert_id=alert_id,
            event_id=event.event_id,
            severity=event.severity,
            status=AlertStatus.NEW,
            title=event.title,
            description=event.description,
            source=event.source,
            indicators=event.indicators,
            affected_assets=event.affected_assets,
            metadata=event.metadata,
            tags=event.tags,
        )

        self.alerts[alert_id] = alert

        alert_counter.labels(
            severity=alert.severity.value,
            source=alert.source,
        ).inc()

        active_alerts_gauge.labels(severity=alert.severity.value).inc()

        return alert

    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert"""
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            channels = list(self.notification_manager.notifiers.keys())
        else:
            channels = ["webhook"]

        results = await self.notification_manager.send_alert(alert, channels)

        for channel, success in results.items():
            notification_counter.labels(
                channel=channel,
                success=str(success),
            ).inc()

        alert.notification_sent = any(results.values())

    async def _check_burst(self):
        """Check for alert burst patterns"""
        now = datetime.utcnow()
        recent_window = now - timedelta(seconds=60)

        recent_count = sum(
            1 for ts in self.recent_events if ts >= recent_window
        )

        if recent_count >= self.burst_threshold:
            burst_event = DetectionEvent(
                event_id=f"burst-{uuid.uuid4().hex[:8]}",
                timestamp=now,
                source="monitoring-processor",
                severity=AlertSeverity.HIGH,
                title=f"Alert Burst Detected: {recent_count} events in 60s",
                description=f"Detected {recent_count} events in the last 60 seconds, exceeding burst threshold of {self.burst_threshold}",
                indicators=[],
                affected_assets=[],
                metadata={"burst_count": str(recent_count)},
                tags=["burst", "anomaly"],
            )

            alert = await self._create_alert(burst_event)
            alert.escalated = True
            await self._send_notifications(alert)

            self.recent_events.clear()

    async def _update_metrics(self):
        """Periodically update metrics"""
        while self.running:
            await asyncio.sleep(10)

            for severity in AlertSeverity:
                count = sum(
                    1
                    for a in self.alerts.values()
                    if a.severity == severity and a.status == AlertStatus.NEW
                )
                active_alerts_gauge.labels(severity=severity.value).set(count)

    def get_dashboard_metrics(self) -> DashboardMetrics:
        """Get current dashboard metrics"""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(hours=24)

        events_1h = sum(
            1 for e in self.event_history if e.timestamp >= one_hour_ago
        )
        events_24h = sum(
            1 for e in self.event_history if e.timestamp >= one_day_ago
        )

        alerts_by_severity = defaultdict(int)
        alerts_by_status = defaultdict(int)

        for alert in self.alerts.values():
            alerts_by_severity[alert.severity.value] += 1
            alerts_by_status[alert.status.value] += 1

        top_indicators = sorted(
            [{"indicator": k, "count": v} for k, v in self.indicator_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

        top_sources = sorted(
            [{"source": k, "count": v} for k, v in self.events_by_source.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

        avg_processing_time = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times
            else 0.0
        )

        return DashboardMetrics(
            alerts_total=len(self.alerts),
            alerts_by_severity=dict(alerts_by_severity),
            alerts_by_status=dict(alerts_by_status),
            events_processed_last_hour=events_1h,
            events_processed_last_24h=events_24h,
            top_indicators=top_indicators,
            top_sources=top_sources,
            average_processing_time_ms=avg_processing_time * 1000,
        )

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        return self.alerts.get(alert_id)

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """Get alerts with optional filters"""
        alerts = list(self.alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if status:
            alerts = [a for a in alerts if a.status == status]

        alerts.sort(key=lambda x: x.created_at, reverse=True)

        return alerts[:limit]

    async def update_alert_status(self, alert_id: str, status: AlertStatus) -> bool:
        """Update alert status"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = status
            self.alerts[alert_id].updated_at = datetime.utcnow()
            return True
        return False
