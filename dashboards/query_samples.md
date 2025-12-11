# Query Samples and Dashboard Examples

## Overview

This document provides practical examples for querying audit events and building compliance dashboards.

## API Query Examples

### Basic Queries

#### Get Recent Events

```bash
# Last 100 events
curl "http://localhost:8000/api/v1/query?limit=100"

# Last 24 hours
START_TIME=$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
curl "http://localhost:8000/api/v1/query?start_time=$START_TIME"
```

#### Filter by Event Type

```bash
# User actions only
curl "http://localhost:8000/api/v1/query?event_type=user_action"

# Security detections only
curl "http://localhost:8000/api/v1/query?event_type=detection"

# Scan results only
curl "http://localhost:8000/api/v1/query?event_type=scan"
```

#### Filter by Severity

```bash
# Critical events only
curl "http://localhost:8000/api/v1/query?severity=critical"

# High and critical events
curl "http://localhost:8000/api/v1/query?severity=high"
curl "http://localhost:8000/api/v1/query?severity=critical"
```

### User Activity Queries

#### All Actions by User

```bash
curl "http://localhost:8000/api/v1/query?user_id=user123&limit=1000"
```

#### Failed Login Attempts

```bash
curl "http://localhost:8000/api/v1/query?event_type=user_action&action=login&result=failure"
```

#### Privileged Operations

```bash
curl "http://localhost:8000/api/v1/query?event_type=user_action&action=admin_action&severity=high"
```

#### Data Access by User

```bash
curl "http://localhost:8000/api/v1/query?user_id=user123&action=read&resource_type=sensitive_data"
```

### Security Detection Queries

#### Malware Detections

```bash
curl "http://localhost:8000/api/v1/query?event_type=detection&detection_type=malware"
```

#### High-Severity Detections

```bash
curl "http://localhost:8000/api/v1/query?event_type=detection&severity=high"
```

#### Detections by Source

```bash
curl "http://localhost:8000/api/v1/query?event_type=detection&source_service=scanner-1"
```

### Time-Based Queries

#### Events in Date Range

```bash
START="2024-01-01T00:00:00Z"
END="2024-01-31T23:59:59Z"
curl "http://localhost:8000/api/v1/query?start_time=$START&end_time=$END"
```

#### Last Hour Activity

```bash
START_TIME=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)
curl "http://localhost:8000/api/v1/query?start_time=$START_TIME"
```

## Python Client Examples

### Security Dashboard

```python
from audit_client import AuditClient
from datetime import datetime, timedelta

client = AuditClient(api_url="http://localhost:8000")

def security_dashboard():
    """Generate security overview dashboard."""
    now = datetime.utcnow()
    day_ago = (now - timedelta(days=1)).isoformat()
    
    # Failed logins in last 24h
    failed_logins = client.query_events(
        event_type="user_action",
        action="login",
        result="failure",
        start_time=day_ago
    )
    
    # High-severity detections
    detections = client.query_events(
        event_type="detection",
        severity="high",
        start_time=day_ago
    )
    
    # Critical events
    critical = client.query_events(
        severity="critical",
        start_time=day_ago
    )
    
    return {
        "failed_logins": failed_logins['total'],
        "high_severity_detections": detections['total'],
        "critical_events": critical['total'],
        "period": "24 hours"
    }

print(security_dashboard())
```

### User Activity Report

```python
def user_activity_report(user_id, days=7):
    """Generate user activity report."""
    start_time = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    events = client.query_events(
        user_id=user_id,
        start_time=start_time,
        limit=1000
    )
    
    # Aggregate by action
    actions = {}
    for event in events['events']:
        action = event.get('action', 'unknown')
        actions[action] = actions.get(action, 0) + 1
    
    return {
        "user_id": user_id,
        "period_days": days,
        "total_actions": events['total'],
        "actions_breakdown": actions
    }
```

### Compliance Audit Report

```python
def compliance_audit_report(start_date, end_date):
    """Generate compliance audit report."""
    
    # Get all events in period
    all_events = client.query_events(
        start_time=start_date,
        end_time=end_date,
        limit=10000
    )
    
    # Categorize events
    report = {
        "period": f"{start_date} to {end_date}",
        "total_events": all_events['total'],
        "by_type": {},
        "by_severity": {},
        "security_incidents": 0
    }
    
    for event in all_events['events']:
        # By type
        event_type = event['event_type']
        report['by_type'][event_type] = report['by_type'].get(event_type, 0) + 1
        
        # By severity
        severity = event['severity']
        report['by_severity'][severity] = report['by_severity'].get(severity, 0) + 1
        
        # Count security incidents
        if event['event_type'] == 'detection' and event['severity'] in ['high', 'critical']:
            report['security_incidents'] += 1
    
    return report
```

### Anomaly Detection

```python
def detect_anomalies(user_id, threshold=10):
    """Detect unusual activity patterns."""
    
    # Get last 24h of activity
    recent = client.query_events(
        user_id=user_id,
        start_time=(datetime.utcnow() - timedelta(days=1)).isoformat(),
        limit=1000
    )
    
    # Get last 30d baseline
    baseline = client.query_events(
        user_id=user_id,
        start_time=(datetime.utcnow() - timedelta(days=30)).isoformat(),
        limit=10000
    )
    
    # Calculate normal activity rate
    normal_rate = baseline['total'] / 30  # Events per day
    recent_rate = recent['total']
    
    if recent_rate > normal_rate * threshold:
        return {
            "anomaly_detected": True,
            "normal_rate": normal_rate,
            "recent_rate": recent_rate,
            "deviation": f"{(recent_rate / normal_rate) * 100:.1f}%"
        }
    
    return {"anomaly_detected": False}
```

## SQL Direct Queries

For advanced analytics, query PostgreSQL directly:

### Top Active Users

```sql
SELECT 
    user_id,
    user_name,
    COUNT(*) as action_count,
    COUNT(DISTINCT action) as unique_actions,
    MAX(timestamp) as last_activity
FROM audit_events
WHERE event_type = 'user_action'
    AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY user_id, user_name
ORDER BY action_count DESC
LIMIT 20;
```

### Failed Operations Analysis

```sql
SELECT 
    action,
    resource_type,
    COUNT(*) as failure_count,
    COUNT(DISTINCT user_id) as affected_users
FROM audit_events
WHERE result = 'failure'
    AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY action, resource_type
ORDER BY failure_count DESC;
```

### Security Incident Timeline

```sql
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    detection_type,
    severity,
    COUNT(*) as count
FROM audit_events
WHERE event_type = 'detection'
    AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY hour, detection_type, severity
ORDER BY hour DESC, count DESC;
```

### Most Accessed Resources

```sql
SELECT 
    resource,
    resource_type,
    COUNT(*) as access_count,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) FILTER (WHERE result = 'denied') as denied_count
FROM audit_events
WHERE action IN ('read', 'access', 'view')
    AND timestamp > NOW() - INTERVAL '30 days'
GROUP BY resource, resource_type
ORDER BY access_count DESC
LIMIT 50;
```

### Hourly Activity Pattern

```sql
SELECT 
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as active_users
FROM audit_events
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY hour_of_day
ORDER BY hour_of_day;
```

### Metadata Analysis

```sql
-- Events with specific metadata
SELECT 
    event_id,
    timestamp,
    user_id,
    action,
    metadata->>'ip' as ip_address,
    metadata->>'user_agent' as user_agent
FROM audit_events
WHERE event_type = 'user_action'
    AND metadata ? 'ip'
    AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
```

### Tag-Based Queries

```sql
-- Events with specific tags
SELECT 
    event_type,
    severity,
    COUNT(*) as count
FROM audit_events
WHERE tags && ARRAY['pci', 'cardholder_data']
    AND timestamp > NOW() - INTERVAL '90 days'
GROUP BY event_type, severity;
```

## Dashboard Visualizations

### Grafana Dashboard (JSON)

```json
{
  "dashboard": {
    "title": "Audit Events Dashboard",
    "panels": [
      {
        "title": "Events Over Time",
        "type": "graph",
        "targets": [
          {
            "rawSql": "SELECT timestamp, COUNT(*) FROM audit_events WHERE $__timeFilter(timestamp) GROUP BY timestamp ORDER BY timestamp"
          }
        ]
      },
      {
        "title": "Events by Severity",
        "type": "piechart",
        "targets": [
          {
            "rawSql": "SELECT severity, COUNT(*) as count FROM audit_events WHERE $__timeFilter(timestamp) GROUP BY severity"
          }
        ]
      },
      {
        "title": "Failed Operations",
        "type": "table",
        "targets": [
          {
            "rawSql": "SELECT user_id, action, resource, timestamp FROM audit_events WHERE result = 'failure' AND $__timeFilter(timestamp) ORDER BY timestamp DESC LIMIT 100"
          }
        ]
      }
    ]
  }
}
```

### Elasticsearch/Kibana Integration

```python
# Export to Elasticsearch for visualization
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])

def export_to_elasticsearch():
    """Export audit events to Elasticsearch."""
    events = client.query_events(limit=1000)
    
    for event in events['events']:
        es.index(
            index='audit-events',
            document={
                "timestamp": event['timestamp'],
                "event_type": event['event_type'],
                "severity": event['severity'],
                "user_id": event.get('user_id'),
                "action": event.get('action'),
                "resource": event.get('resource'),
                "result": event.get('result'),
                "metadata": event.get('metadata')
            }
        )
```

## Alerting Examples

### Critical Event Alert

```python
import smtplib
from email.mime.text import MIMEText

def check_critical_events():
    """Check for critical events and send alert."""
    recent = datetime.utcnow() - timedelta(minutes=5)
    
    events = client.query_events(
        severity="critical",
        start_time=recent.isoformat()
    )
    
    if events['total'] > 0:
        send_alert(f"Critical events detected: {events['total']}")

def send_alert(message):
    msg = MIMEText(message)
    msg['Subject'] = 'Security Alert: Critical Events'
    msg['From'] = 'audit@example.com'
    msg['To'] = 'security@example.com'
    
    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)
```

### Failed Login Detection

```python
def check_brute_force(threshold=5):
    """Detect potential brute force attacks."""
    recent = datetime.utcnow() - timedelta(minutes=10)
    
    failed = client.query_events(
        event_type="user_action",
        action="login",
        result="failure",
        start_time=recent.isoformat(),
        limit=1000
    )
    
    # Group by user_id
    users = {}
    for event in failed['events']:
        user_id = event.get('user_id', 'unknown')
        users[user_id] = users.get(user_id, 0) + 1
    
    # Alert on threshold
    for user_id, count in users.items():
        if count >= threshold:
            send_alert(f"Possible brute force: {user_id} - {count} failed logins")
```

## Best Practices

1. **Use appropriate time ranges**: Start with narrow ranges and expand as needed
2. **Leverage indexes**: Query by indexed fields (event_type, severity, user_id, etc.)
3. **Paginate large results**: Use limit and offset for large datasets
4. **Cache dashboard data**: Refresh periodically rather than real-time for performance
5. **Use metadata effectively**: Store searchable data in top-level fields, details in metadata
6. **Tag consistently**: Standardize tags across your organization
7. **Monitor query performance**: Set up alerts for slow queries
8. **Export for long-term analysis**: Consider data warehouse integration for historical analysis

## Additional Resources

- [Schema Documentation](../docs/schema.md)
- [API Documentation](http://localhost:8000/docs)
- [Retention Policies](../docs/retention.md)
- [Compliance Guide](../docs/compliance.md)
