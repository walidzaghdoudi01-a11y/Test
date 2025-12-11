# Audit Event Schema Documentation

## Overview

The audit logging system uses a flexible schema to support various types of security events while maintaining tamper-evidence and immutability.

## Core Event Structure

### audit_events Table

| Column | Type | Description | Required |
|--------|------|-------------|----------|
| `id` | BIGSERIAL | Auto-incrementing primary key | Yes |
| `event_id` | UUID | Globally unique event identifier | Yes (auto-generated) |
| `timestamp` | TIMESTAMPTZ | Event timestamp | Yes (auto-generated) |
| `event_type` | VARCHAR(100) | Type of event | Yes |
| `severity` | VARCHAR(20) | Severity level | Yes |

### Event Types

1. **user_action** - User activities and access events
2. **detection** - Security detections (malware, intrusions, etc.)
3. **scan** - Security scan results
4. **system_event** - System-level events
5. **custom** - Custom event types

### Severity Levels

- `low` - Informational events
- `medium` - Standard operational events
- `high` - Important security events
- `critical` - Critical security incidents

## Source Information

| Column | Type | Description |
|--------|------|-------------|
| `source_service` | VARCHAR(200) | Service that generated the event |
| `source_host` | VARCHAR(255) | Hostname of the source |
| `source_ip` | INET | IP address of the source |

## Actor Information (User Actions)

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | VARCHAR(200) | User identifier |
| `user_name` | VARCHAR(255) | User display name |
| `action` | VARCHAR(200) | Action performed |
| `resource` | VARCHAR(500) | Resource affected |
| `resource_type` | VARCHAR(100) | Type of resource |
| `result` | VARCHAR(50) | Result: success, failure, denied |

## Detection/Scan Specific

| Column | Type | Description |
|--------|------|-------------|
| `detection_type` | VARCHAR(100) | Type of detection |
| `scan_id` | VARCHAR(200) | Unique scan identifier |

## Metadata and Context

| Column | Type | Description |
|--------|------|-------------|
| `metadata` | JSONB | Additional structured data |
| `tags` | TEXT[] | Tags for categorization |

## Tamper-Evidence Fields

| Column | Type | Description |
|--------|------|-------------|
| `previous_hash` | VARCHAR(64) | SHA-256 hash of previous event |
| `event_hash` | VARCHAR(64) | SHA-256 hash of this event |
| `signature` | TEXT | Optional HMAC signature |

### Hash Chaining

Events are linked via cryptographic hashing:

```
Event N: hash = SHA256(event_data + previous_hash)
Event N+1: hash = SHA256(event_data + Event_N.hash)
```

This creates an immutable chain where any tampering breaks the integrity.

## Retention Management

| Column | Type | Description |
|--------|------|-------------|
| `retention_days` | INTEGER | Days to retain (default: 2555) |
| `archived` | BOOLEAN | Whether event is archived |
| `archive_location` | TEXT | Location of archived data |

## Metadata Schema Examples

### User Action Metadata

```json
{
  "ip": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "session_id": "abc123",
  "request_id": "req-456",
  "changes": {
    "old_value": "...",
    "new_value": "..."
  }
}
```

### Detection Metadata

```json
{
  "file_path": "/tmp/suspicious.exe",
  "file_hash": "sha256:...",
  "signature_match": "Malware.Generic",
  "threat_level": 8,
  "quarantine_status": "quarantined"
}
```

### Scan Metadata

```json
{
  "scan_duration": 120,
  "items_scanned": 1000,
  "vulnerabilities_found": 3,
  "findings": [
    {
      "cve": "CVE-2024-1234",
      "severity": "high",
      "component": "library-1.2.3"
    }
  ]
}
```

## Indexes

The following indexes optimize common query patterns:

- `idx_audit_events_timestamp` - Time-based queries
- `idx_audit_events_event_type` - Filter by event type
- `idx_audit_events_severity` - Filter by severity
- `idx_audit_events_user_id` - User-specific queries
- `idx_audit_events_action` - Action-based queries
- `idx_audit_events_detection_type` - Detection queries
- `idx_audit_events_metadata` (GIN) - JSONB queries
- `idx_audit_events_tags` (GIN) - Tag-based queries
- `idx_audit_events_archived` - Retention queries

## Constraints and Triggers

### WORM Protection

A PostgreSQL trigger enforces Write-Once-Read-Many semantics:

- **UPDATE**: Only allows marking events as archived
- **DELETE**: Completely prevented

This guarantees immutability for compliance and forensics.

### Unique Constraints

- `event_id` - Ensures globally unique identifiers

## Related Tables

### retention_policies

Defines retention periods for different event types.

### audit_access_log

Meta-auditing: logs all access to the audit events table.

## Best Practices

1. **Always include metadata**: Use the metadata field for event-specific details
2. **Use appropriate severity**: Match severity to actual risk level
3. **Tag consistently**: Use standard tags for easier querying
4. **Include source info**: Always populate source_service at minimum
5. **Meaningful actions**: Use clear, consistent action names
6. **Resource identification**: Include full resource paths when possible

## Query Examples

See [Query Samples](../dashboards/query_samples.md) for practical examples.
