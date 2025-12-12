# Threat Intelligence Monitoring & Reputation Service

A comprehensive real-time threat monitoring and reputation lookup service with streaming event processing, multi-channel alerting, and intelligence feed aggregation.

## Features

### 🚨 Streaming Processor
- **Real-time Event Processing**: Asynchronous processing of detection events from multiple sources
- **Intelligent Alert Generation**: Context-aware alert creation based on severity and patterns
- **Burst Detection**: Automatic identification of abnormal event spikes
- **Multi-Channel Notifications**: Email, webhook, Slack, and PagerDuty integrations
- **Dashboard Metrics**: Real-time metrics and statistics for monitoring

### 🔍 Reputation Lookup Service
- **Multi-Feed Aggregation**: Queries multiple threat intelligence feeds (VirusTotal, AbuseIPDB, custom feeds)
- **Intelligent Scoring**: Aggregates reputation scores from multiple sources
- **High-Performance Caching**: Redis-based caching to minimize external API calls
- **Bulk Operations**: Efficient batch processing for multiple lookups
- **Validation**: Comprehensive input validation for IPs and domains

### 📊 Monitoring & Observability
- **Prometheus Metrics**: Comprehensive metrics exposure for monitoring
- **Health Checks**: Detailed component health status
- **Performance Tracking**: Request latency and throughput metrics
- **Dashboard Support**: Pre-configured Grafana dashboards

## Quick Start

### Prerequisites
- Python 3.9+
- Redis (optional, for caching)
- Docker & Docker Compose (for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd threat-intelligence-monitoring
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start Redis (optional):
```bash
docker run -d -p 6379:6379 redis:latest
```

4. Run the service:
```bash
python main.py
```

The service will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Docker Deployment

```bash
cd infrastructure
docker-compose up -d
```

This starts:
- Monitoring service on port 8000
- Redis cache on port 6379
- Prometheus on port 9090
- Grafana on port 3000 (admin/admin)

## API Usage

### Ingest Detection Event

```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-001",
    "source": "detection-engine",
    "severity": "high",
    "title": "Suspicious Activity Detected",
    "description": "Malicious IP connection attempt",
    "indicators": ["192.168.1.100"],
    "affected_assets": ["server-1"]
  }'
```

### Lookup IP Reputation

```bash
curl "http://localhost:8000/api/v1/reputation/ip/192.168.1.100"
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
      "confidence": 0.98
    }
  ],
  "categories": ["malware", "command_and_control"],
  "cached": false
}
```

### Get Dashboard Metrics

```bash
curl "http://localhost:8000/api/v1/monitoring/dashboard"
```

### Get Alerts

```bash
curl "http://localhost:8000/api/v1/monitoring/alerts?severity=high&limit=50"
```

## Architecture

```
Detection Sources → Streaming Processor → Alert Engine → Notifications
                         ↓                                  ↓
                    Event Queue                      Email/Webhook
                         ↓
                  Metrics & Dashboard

Reputation Requests → API Layer → Service Logic → Feed Aggregator
                                        ↓              ↓
                                   Redis Cache    Multiple Feeds
```

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_TTL_SECONDS=3600

# Alert Configuration
ALERT_THRESHOLD=10
BURST_THRESHOLD=100
BURST_WINDOW_SECONDS=60

# Notification Configuration (for production)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=your-password
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## Testing

### Run All Tests

```bash
pytest
```

### Run Unit Tests

```bash
pytest tests/unit/ -v
```

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

### Test Coverage

```bash
pytest --cov=services --cov-report=html
```

### Simulate Alert Burst

```python
import asyncio
import httpx
from datetime import datetime

async def simulate_burst():
    async with httpx.AsyncClient() as client:
        for i in range(150):
            event = {
                "event_id": f"burst-{i}",
                "timestamp": datetime.utcnow().isoformat(),
                "source": "simulator",
                "severity": "medium",
                "title": f"Burst Event {i}",
                "description": "Testing burst detection",
                "indicators": [f"10.0.0.{i % 256}"],
            }
            await client.post(
                "http://localhost:8000/api/v1/monitoring/events",
                json=event,
            )

asyncio.run(simulate_burst())
```

## Deployment

### Kubernetes

```bash
kubectl apply -f infrastructure/kubernetes-deployment.yaml
```

### AWS ECS (Terraform)

```bash
cd infrastructure/terraform
terraform init
terraform plan -var="environment=production"
terraform apply
```

### Monitoring Stack

The complete monitoring stack includes:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and notification
- **Redis**: High-performance caching

Access Grafana at `http://localhost:3000` (admin/admin)

## SLA and Thresholds

| Metric | Target | Measurement |
|--------|--------|-------------|
| Event Processing Time | < 100ms | p95 |
| Alert Generation | < 500ms | p95 |
| Notification Delivery | < 5s | p95 |
| API Response Time | < 200ms | p95 |
| System Uptime | 99.9% | Monthly |
| Cache Hit Rate | > 80% | Daily |

### Alert Thresholds

- **Burst Detection**: 100 events in 60 seconds
- **Repeated Indicators**: 3+ occurrences in 1 hour
- **Queue Depth Warning**: > 1000 events
- **Queue Depth Critical**: > 5000 events

## Documentation

- [Monitoring Integration Guide](docs/MONITORING_INTEGRATION.md) - Comprehensive integration documentation
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Infrastructure as Code](infrastructure/) - Deployment examples

## Metrics

### Prometheus Metrics

```prometheus
# Event metrics
detection_events_total{source,severity}
event_processing_duration_seconds

# Alert metrics
alerts_generated_total{severity,source}
active_alerts{severity}

# Notification metrics
notifications_sent_total{channel,success}

# Reputation lookup metrics
reputation_lookups_total{indicator_type,cached}
reputation_lookup_duration_seconds{indicator_type}
```

### Grafana Queries

**Alert Rate by Severity**
```promql
sum(rate(alerts_generated_total[5m])) by (severity)
```

**Cache Hit Rate**
```promql
sum(rate(reputation_lookups_total{cached="true"}[5m])) 
/ 
sum(rate(reputation_lookups_total[5m]))
```

## Integration Examples

### Python

```python
import httpx
from datetime import datetime

async def send_detection_event():
    async with httpx.AsyncClient() as client:
        event = {
            "event_id": "unique-id",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "my-detector",
            "severity": "high",
            "title": "Threat Detected",
            "description": "Description here",
            "indicators": ["192.168.1.100"],
            "affected_assets": ["server-1"],
        }
        response = await client.post(
            "http://localhost:8000/api/v1/monitoring/events",
            json=event,
        )
        return response.json()
```

### Go

```go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

type DetectionEvent struct {
    EventID         string   `json:"event_id"`
    Source          string   `json:"source"`
    Severity        string   `json:"severity"`
    Title           string   `json:"title"`
    Description     string   `json:"description"`
    Indicators      []string `json:"indicators"`
    AffectedAssets  []string `json:"affected_assets"`
}

func sendEvent(event DetectionEvent) error {
    data, _ := json.Marshal(event)
    resp, err := http.Post(
        "http://localhost:8000/api/v1/monitoring/events",
        "application/json",
        bytes.NewBuffer(data),
    )
    return err
}
```

## Troubleshooting

### High Queue Depth
- Increase worker concurrency
- Scale horizontally with more instances
- Optimize event processing logic

### Low Cache Hit Rate
- Increase Redis TTL
- Verify Redis connectivity
- Check cache configuration

### Failed Notifications
- Verify SMTP/webhook credentials
- Check network connectivity
- Review notification logs

### Slow Reputation Lookups
- Enable caching
- Use bulk lookup APIs
- Monitor external API rate limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- Open an issue on GitHub
- Contact: security-team@example.com
