# Retention and Archival Policies

## Overview

The audit logging system implements configurable retention policies to manage log lifecycle while maintaining compliance with regulatory requirements.

## Retention Periods

### Default Retention Policies

| Event Type | Retention Days | Archive Enabled | Compliance Standard |
|------------|----------------|-----------------|---------------------|
| `user_action` | 2555 (7 years) | Yes | SOX, GDPR, HIPAA |
| `detection` | 1825 (5 years) | Yes | PCI DSS, ISO 27001 |
| `scan` | 365 (1 year) | Yes | Standard practice |
| `system_event` | 730 (2 years) | Yes | Operational needs |
| `default` | 2555 (7 years) | Yes | Conservative default |

### Regulatory Compliance

The default retention periods are designed to meet common compliance requirements:

- **SOX (Sarbanes-Oxley)**: 7 years for financial audit trails
- **HIPAA**: 6 years minimum for healthcare records
- **PCI DSS**: 1 year minimum, 3+ years recommended
- **GDPR**: Varies by purpose, supports data minimization
- **ISO 27001**: Defined by organization, typically 1-7 years

## Retention Lifecycle

### 1. Active Storage

Events are stored in the primary PostgreSQL database with full WORM protection.

**Duration**: From creation until retention period expires

**Access**: Full query capabilities with sub-second response times

### 2. Archival

When events exceed their retention period, they are marked for archival.

**Process**:
1. Identify expired events: `GET /api/v1/retention/expired`
2. Export to archive storage (S3, Glacier, tape, etc.)
3. Mark as archived: `POST /api/v1/retention/archive`
4. Events remain in database but marked as `archived=TRUE`

**Access**: Limited query capabilities, primarily for compliance

### 3. Deletion (Optional)

Some organizations may choose to permanently delete archived events after an extended period.

**⚠️ Warning**: Deletion breaks the hash chain and should only be done for entire historical segments, never individual events.

## Managing Retention Policies

### Get Retention Policy

```bash
curl http://localhost:8000/api/v1/retention/policies/user_action
```

### Update Retention Policy

```bash
curl -X PUT http://localhost:8000/api/v1/retention/policies/custom_event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "custom_event",
    "retention_days": 365,
    "archive_enabled": true,
    "archive_location": "s3://my-bucket/audit-archive"
  }'
```

### Get Retention Statistics

```bash
curl http://localhost:8000/api/v1/retention/statistics
```

**Response**:
```json
{
  "total_events": 1000000,
  "archived_events": 50000,
  "active_events": 950000,
  "expired_events": 5000,
  "oldest_event": "2020-01-01T00:00:00Z",
  "newest_event": "2024-01-01T12:00:00Z",
  "by_type": [
    {
      "event_type": "user_action",
      "count": 500000,
      "archived_count": 25000
    }
  ]
}
```

## Archival Process

### Automated Archival Script

```python
from audit_client import AuditClient
import boto3

client = AuditClient(api_url="http://localhost:8000")
s3 = boto3.client('s3')

# Get expired events
response = client._make_request("GET", "/api/v1/retention/expired?limit=1000")
expired_events = response

if expired_events:
    # Export to S3
    archive_key = f"audit-archive/{datetime.now().strftime('%Y-%m-%d')}.json"
    s3.put_object(
        Bucket='my-audit-bucket',
        Key=archive_key,
        Body=json.dumps(expired_events),
        ServerSideEncryption='AES256'
    )
    
    # Mark as archived
    event_ids = [e['id'] for e in expired_events]
    client._make_request(
        "POST",
        "/api/v1/retention/archive",
        data={
            "event_ids": event_ids,
            "archive_location": f"s3://my-audit-bucket/{archive_key}"
        }
    )
```

### Schedule with Cron

```bash
# Run archival daily at 2 AM
0 2 * * * /usr/bin/python3 /opt/audit/archive_expired.py
```

## Archive Storage Options

### AWS S3 + Glacier

**Recommended for**: Cloud-based deployments

**Lifecycle**: 
- S3 Standard → S3 IA (30 days)
- S3 IA → Glacier (90 days)
- Glacier → Glacier Deep Archive (1 year)

**Benefits**:
- Cost-effective for long-term storage
- High durability (99.999999999%)
- Integrated with AWS compliance tools

### Azure Blob Storage

**Recommended for**: Azure-based deployments

**Tiers**: Hot → Cool → Archive

### Google Cloud Storage

**Recommended for**: GCP-based deployments

**Classes**: Standard → Nearline → Coldline → Archive

### On-Premises Options

- **NAS/SAN**: For regulated industries requiring on-site storage
- **Tape Backup**: For ultra-long-term archival (10+ years)
- **WORM Storage**: Hardware-enforced immutability

## Compliance Considerations

### Audit Trail Integrity

Even when archived, the hash chain must remain verifiable:

1. Include `event_hash` and `previous_hash` in archives
2. Store archives in immutable storage (S3 Object Lock, etc.)
3. Maintain archive metadata in database

### Data Retention Limits

Some regulations require deletion after maximum periods:

- **GDPR Right to Erasure**: May require deletion upon request
- **CCPA**: Similar to GDPR for California residents
- **Data Minimization**: Don't retain longer than necessary

⚠️ **Important**: Consult legal counsel before implementing deletion policies.

### Legal Holds

Implement legal hold functionality to prevent archival/deletion:

```sql
ALTER TABLE audit_events ADD COLUMN legal_hold BOOLEAN DEFAULT FALSE;

-- Prevent archival of events under legal hold
CREATE OR REPLACE FUNCTION check_legal_hold()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.archived = TRUE AND OLD.legal_hold = TRUE THEN
        RAISE EXCEPTION 'Cannot archive events under legal hold';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

## Monitoring and Alerting

### Key Metrics

1. **Archival Lag**: Time between expiration and actual archival
2. **Archive Failures**: Failed archival attempts
3. **Storage Growth**: Rate of active event accumulation
4. **Query Performance**: Ensure indexes remain effective

### Recommended Alerts

- Archival lag > 7 days
- Archive failure rate > 1%
- Active events > 90% of capacity
- Query latency > 1 second (p95)

## Best Practices

1. **Test Restoration**: Regularly test restoring from archives
2. **Encrypt Archives**: Use encryption at rest for archived data
3. **Version Archives**: Include schema version in archive format
4. **Document Location**: Maintain registry of all archive locations
5. **Access Logging**: Log all access to archived data
6. **Periodic Review**: Review retention policies annually
7. **Gradual Archival**: Archive in batches to avoid performance impact
8. **Verify Integrity**: Check hash chains before and after archival

## Future Enhancements

- Automated archive restoration on query
- Tiered storage integration (hot/warm/cold)
- Compression for archived events
- Multi-region archive replication
- Archive format conversion tools
