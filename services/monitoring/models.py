from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    """Alert status"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class NotificationType(str, Enum):
    """Notification delivery types"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"


class DetectionEvent(BaseModel):
    """Detection/logging event from threat detection systems"""
    event_id: str = Field(description="Unique event identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(description="Source system (e.g., detection-engine, scanner)")
    severity: AlertSeverity = Field(description="Event severity")
    title: str = Field(description="Event title")
    description: str = Field(description="Detailed description")
    indicators: List[str] = Field(default_factory=list, description="IOCs (IPs, domains)")
    affected_assets: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class Alert(BaseModel):
    """Processed alert from detection events"""
    alert_id: str = Field(description="Unique alert identifier")
    event_id: str = Field(description="Original event ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    severity: AlertSeverity
    status: AlertStatus = Field(default=AlertStatus.NEW)
    title: str
    description: str
    source: str
    indicators: List[str] = Field(default_factory=list)
    affected_assets: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    notification_sent: bool = Field(default=False)
    escalated: bool = Field(default=False)


class NotificationChannel(BaseModel):
    """Notification channel configuration"""
    name: str
    type: NotificationType
    enabled: bool = True
    config: Dict[str, str] = Field(default_factory=dict)
    severity_filter: List[AlertSeverity] = Field(
        default_factory=lambda: [
            AlertSeverity.CRITICAL,
            AlertSeverity.HIGH,
            AlertSeverity.MEDIUM,
        ]
    )


class EmailNotificationConfig(BaseModel):
    """Email notification configuration"""
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    from_address: str
    to_addresses: List[str]
    use_tls: bool = True


class WebhookNotificationConfig(BaseModel):
    """Webhook notification configuration"""
    url: str
    method: str = "POST"
    headers: Dict[str, str] = Field(default_factory=dict)
    timeout_seconds: int = 30


class DashboardMetrics(BaseModel):
    """Real-time dashboard metrics"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    alerts_total: int = 0
    alerts_by_severity: Dict[str, int] = Field(default_factory=dict)
    alerts_by_status: Dict[str, int] = Field(default_factory=dict)
    events_processed_last_hour: int = 0
    events_processed_last_24h: int = 0
    top_indicators: List[Dict] = Field(default_factory=list)
    top_sources: List[Dict] = Field(default_factory=list)
    average_processing_time_ms: float = 0.0


class HealthCheck(BaseModel):
    """Health check status"""
    status: str = Field(description="overall, degraded, unhealthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    uptime_seconds: float = 0.0
