# Monitoring Integrations

## Overview

The Threat Intelligence Monitoring system provides real-time threat detection monitoring, alert processing, and reputation lookup capabilities. It consists of two main components:

1. **Streaming Processor**: Subscribes to detection/logging topics, processes events, generates alerts, and triggers notifications
2. **Reputation Lookup Service**: Provides IP/domain reputation checking with caching and multiple threat intelligence feed integration

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Detection Sources                         │
│  (Detection Engine, Scanners, IDS/IPS, SIEM, etc.)         │
└────────────────────┬────────────────────────────────────────┘
                     │ Detection Events
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Streaming Processor                             │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐  │
│  │Event Queue   │───▶│Alert Engine  │──▶│Notification  │  │
│  │              │    │              │   │Manager       │  │
│  └──────────────┘    └──────────────┘   └──────┬───────┘  │
│                                                  │           │
│  ┌──────────────────────────────────────────────┼─────┐    │
│  │Burst Detection | Metrics | Dashboard         │     │    │
│  └──────────────────────────────────────────────┼─────┘    │
└─────────────────────────────────────────────────┼──────────┘
                                                   │
                     ┌─────────────────────────────┴──────┐
                     │                                     │
                     ▼                                     ▼
            ┌────────────────┐                  ┌─────────────────┐
            │Email           │                  │Webhook          │
            │Notifications   │                  │Notifications    │
            └────────────────┘                  └─────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           Reputation Lookup Service                          │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐  │
│  │API Layer     │───▶│Service Logic │──▶│Feed          │  │
│  │              │    │              │   │Aggregator    │  │
│  └──────────────┘    └──────┬───────┘   └──────┬───────┘  │
│                             │                    │          │
│                             ▼                    ▼          │
│                      ┌──────────────┐   ┌──────────────┐  │
│                      │Redis Cache   │   │Multiple Feeds│  │
│                      └──────────────┘   │- VirusTotal  │  │
│                                         │- AbuseIPDB   │  │
│                                         │- Custom      │  │
│                                         └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Streaming Processor

- **Event Ingestion**: Accepts detection events from multiple sources
- **Real-time Processing**: Asynchronous event processing with queue management
- **Alert Generation**: Intelligent alert creation based on severity and patterns
- **Burst Detection**: Identifies abnormal event bursts and generates escalated alerts
- **Notification Routing**: Multi-channel notifications (email, webhook, Slack, PagerDuty)
- **Dashboard Metrics**: Real-time metrics for monitoring dashboards
- **Prometheus Integration**: Exposes metrics for Prometheus scraping

### Reputation Lookup Service

- **Multi-Feed Aggregation**: Queries multiple threat intelligence feeds
- **Intelligent Scoring**: Aggregates scores from multiple sources
- **Caching**: Redis-based caching to reduce external API calls
- **Bulk Lookups**: Efficient batch processing of multiple indicators
- **Validation**: Input validation for IPs and domains
- **Performance Metrics**: Prometheus metrics for lookup performance

## API Endpoints

### Monitoring APIs

#### Ingest Detection Event
```http
POST /api/v1/monitoring/events
Content-Type: application/json

{
  "event_id": "event-123",
  "timestamp": "2024-01-01T00:00:00Z",
  "source": "detection-engine",
  "severity": "high",
  "title": "Suspicious Activity Detected",
  "description": "Detected malicious IP connection",
  "indicators": ["192.168.1.100"],
  "affected_assets": ["server-1"],
  "metadata": {},
  "tags": ["malware"]
}
```

#### Batch Ingest Events
```http
POST /api/v1/monitoring/events/batch
Content-Type: application/json

[
  { "event_id": "e1", ... },
  { "event_id": "e2", ... }
]
```

#### Get Alerts
```http
GET /api/v1/monitoring/alerts?severity=high&status=new&limit=100
```

#### Update Alert Status
```http
PATCH /api/v1/monitoring/alerts/{alert_id}/status?status=acknowledged
```

#### Dashboard Metrics
```http
GET /api/v1/monitoring/dashboard
```

Response:
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "alerts_total": 150,
  "alerts_by_severity": {
    "critical": 10,
    "high": 45,
    "medium": 60,
    "low": 35
  },
  "events_processed_last_hour": 500,
  "events_processed_last_24h": 8000,
  "top_indicators": [
    {"indicator": "192.168.1.100", "count": 25}
  ],
  "top_sources": [
    {"source": "detection-engine", "count": 300}
  ],
  "average_processing_time_ms": 15.5
}
```

#### Health Check
```http
GET /api/v1/monitoring/health
```

#### Prometheus Metrics
```http
GET /api/v1/monitoring/metrics
```

### Reputation Lookup APIs

#### IP Reputation Lookup
```http
GET /api/v1/reputation/ip/192.168.1.100?use_cache=true
```

Response:
```json
{
  "ip_address": "192.168.1.100",
  "overall_score": "malicious",
  "risk_score": 95.5,
  "sources": [
    {
      "name": "VirusTotal",
      "score": "malicious",
      "categories": ["malware", "command_and_control"],
      "confidence": 0.98,
      "last_seen": "2024-01-01T00:00:00Z",
      "metadata": {"detections": "65/70"}
    }
  ],
  "categories": ["malware", "command_and_control"],
  "first_seen": "2023-12-01T00:00:00Z",
  "last_seen": "2024-01-01T00:00:00Z",
  "cached": false,
  "queried_at": "2024-01-01T00:00:00Z"
}
```

#### Domain Reputation Lookup
```http
GET /api/v1/reputation/domain/malicious-site.evil
```

#### Bulk Lookup
```http
POST /api/v1/reputation/bulk
Content-Type: application/json

{
  "indicators": ["192.168.1.100", "8.8.8.8", "example.com"],
  "max_age_seconds": 3600
}
```

#### Cache Invalidation
```http
POST /api/v1/reputation/cache/invalidate/192.168.1.100
```

#### Cache Statistics
```http
GET /api/v1/reputation/cache/stats
```

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_TTL_SECONDS=3600

# Notification Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=your-password
NOTIFICATION_FROM=alerts@example.com
NOTIFICATION_TO=security-team@example.com

# Webhook Configuration
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
WEBHOOK_TIMEOUT=30

# Alert Configuration
ALERT_THRESHOLD=10
BURST_THRESHOLD=100
BURST_WINDOW_SECONDS=60

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
```

### Notification Channels

Configure notification channels programmatically:

```python
from services.monitoring.notifier import (
    EmailNotifier,
    WebhookNotifier,
    NotificationManager,
    EmailNotificationConfig,
    WebhookNotificationConfig,
)

# Email channel
email_config = EmailNotificationConfig(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="alerts@example.com",
    smtp_password="your-password",
    from_address="alerts@example.com",
    to_addresses=["security@example.com"],
)
email_notifier = EmailNotifier(email_config)

# Webhook channel
webhook_config = WebhookNotificationConfig(
    url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    method="POST",
    headers={"Content-Type": "application/json"},
)
webhook_notifier = WebhookNotifier(webhook_config)

# Add to notification manager
notification_manager = NotificationManager()
notification_manager.add_notifier("email", email_notifier)
notification_manager.add_notifier("webhook", webhook_notifier)
```

## Alert Severity and Routing

### Severity Levels

- **CRITICAL**: Immediate action required, all channels notified
- **HIGH**: Urgent attention needed, all channels notified
- **MEDIUM**: Important but not urgent, webhook only
- **LOW**: Informational, logged but not notified
- **INFO**: Logging only

### Alert Routing Rules

```python
# Critical and High severity
- Email notifications
- Webhook notifications
- PagerDuty escalation (if configured)
- Immediate dashboard update

# Medium severity
- Webhook notifications
- Dashboard update
- Email digest (configurable)

# Low and Info
- Dashboard update only
- Logged for historical analysis
```

## SLA and Alert Thresholds

### Service Level Agreements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Event Processing Time | < 100ms | p95 |
| Alert Generation Time | < 500ms | p95 |
| Notification Delivery | < 5s | p95 |
| API Response Time | < 200ms | p95 |
| System Uptime | 99.9% | Monthly |
| Cache Hit Rate | > 80% | Daily average |

### Alert Thresholds

#### Burst Detection
- **Threshold**: 100 events in 60 seconds
- **Action**: Generate HIGH severity alert, escalate to all channels
- **Cooldown**: 5 minutes before next burst alert

#### Repeated Indicators
- **Threshold**: 3+ occurrences of same indicator in 1 hour
- **Action**: Generate MEDIUM severity alert

#### Processing Queue Depth
- **Warning**: Queue depth > 1000
- **Critical**: Queue depth > 5000
- **Action**: Generate system health alert

#### Cache Performance
- **Warning**: Hit rate < 70%
- **Critical**: Hit rate < 50%
- **Action**: Investigate cache configuration

## Health Checks

### Liveness Probe
```http
GET /health
```
Returns 200 if service is running.

### Readiness Probe
```http
GET /api/v1/monitoring/health
```
Returns detailed health status of all components:
- Streaming processor status
- Notification manager status
- Cache connectivity
- Queue depth

### Component Health Checks

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "components": {
    "streaming_processor": {
      "status": "healthy",
      "queue_size": "5"
    },
    "notification_manager": {
      "status": "healthy",
      "channels": "2"
    },
    "cache": {
      "status": "healthy",
      "connected": "true"
    }
  },
  "uptime_seconds": 86400.5
}
```

## Prometheus Metrics

### Exposed Metrics

```prometheus
# Event Processing
detection_events_total{source,severity}
event_processing_duration_seconds

# Alerts
alerts_generated_total{severity,source}
active_alerts{severity}

# Notifications
notifications_sent_total{channel,success}

# Reputation Lookups
reputation_lookups_total{indicator_type,cached}
reputation_lookup_duration_seconds{indicator_type}

# System Health
up
process_cpu_seconds_total
process_resident_memory_bytes
```

### Grafana Dashboard Queries

**Active Alerts by Severity**
```promql
sum(active_alerts) by (severity)
```

**Event Processing Rate**
```promql
rate(detection_events_total[5m])
```

**Notification Success Rate**
```promql
sum(rate(notifications_sent_total{success="true"}[5m])) 
/ 
sum(rate(notifications_sent_total[5m]))
```

**Reputation Lookup Cache Hit Rate**
```promql
sum(rate(reputation_lookups_total{cached="true"}[5m])) 
/ 
sum(rate(reputation_lookups_total[5m]))
```

## Integration Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Redis (Optional)

```bash
docker run -d -p 6379:6379 redis:latest
```

### 3. Start the Service

```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. Integrate Detection Sources

Send detection events from your detection systems:

```python
import httpx

event = {
    "event_id": "unique-id",
    "timestamp": "2024-01-01T00:00:00Z",
    "source": "my-detector",
    "severity": "high",
    "title": "Threat Detected",
    "description": "Detailed description",
    "indicators": ["192.168.1.100"],
    "affected_assets": ["server-1"],
}

response = httpx.post(
    "http://localhost:8000/api/v1/monitoring/events",
    json=event,
)
```

### 5. Query Reputation Data

```python
response = httpx.get(
    "http://localhost:8000/api/v1/reputation/ip/192.168.1.100"
)
reputation = response.json()
```

### 6. Set Up Monitoring

Configure Prometheus to scrape metrics:

```yaml
scrape_configs:
  - job_name: 'threat-monitoring'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/monitoring/metrics'
    scrape_interval: 15s
```

## Testing

### Run Unit Tests

```bash
pytest tests/unit/ -v
```

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

### Simulate Alert Burst

```python
import asyncio
from services.monitoring.models import DetectionEvent, AlertSeverity

async def simulate_burst():
    for i in range(150):
        event = DetectionEvent(
            event_id=f"burst-{i}",
            source="simulator",
            severity=AlertSeverity.MEDIUM,
            title=f"Burst Event {i}",
            description="Testing burst detection",
            indicators=[f"10.0.0.{i % 256}"],
        )
        # Send to API
        await send_event(event)
```

## Best Practices

1. **Rate Limiting**: Implement rate limiting for event ingestion
2. **Backpressure**: Monitor queue depth and implement backpressure
3. **Idempotency**: Use unique event IDs to prevent duplicate processing
4. **Monitoring**: Set up alerts on key metrics (queue depth, processing time)
5. **Caching**: Use Redis cache to reduce load on external feeds
6. **Batch Operations**: Use bulk APIs for multiple lookups
7. **Error Handling**: Implement retry logic for failed notifications
8. **Security**: Use TLS for webhook notifications and authentication

## Troubleshooting

### High Queue Depth
- Increase worker concurrency
- Optimize event processing logic
- Scale horizontally

### Low Cache Hit Rate
- Increase TTL if indicators are stable
- Verify Redis connectivity
- Check cache key patterns

### Failed Notifications
- Verify SMTP/webhook credentials
- Check network connectivity
- Review notification logs
- Implement retry logic

### Slow Reputation Lookups
- Increase cache TTL
- Use bulk lookup APIs
- Consider feed aggregation optimization
- Monitor external API rate limits
