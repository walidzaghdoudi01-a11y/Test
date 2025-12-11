# Compliance and Security Requirements

## Overview

This audit logging system is designed to meet stringent compliance and security requirements for regulated industries including finance, healthcare, and government sectors.

## Immutability Guarantees

### Write-Once-Read-Many (WORM)

The system enforces WORM semantics at multiple levels:

#### Database Level
- PostgreSQL triggers prevent UPDATE and DELETE operations
- Only archival status can be modified (one-way transition)
- Attempts to modify or delete audit events result in exceptions

#### Application Level
- No API endpoints for updating or deleting events
- Service layer enforces append-only operations
- Client library provides only write and read methods

#### Verification
```bash
# Test immutability
curl -X PUT http://localhost:8000/api/v1/events/{event_id} \
  -d '{"severity": "high"}'
# Expected: 405 Method Not Allowed

# Verify chain integrity
curl http://localhost:8000/api/v1/events/verify/integrity?limit=1000
```

## Tamper Evidence

### Cryptographic Hash Chaining

Each event contains:
1. **event_hash**: SHA-256 hash of current event data
2. **previous_hash**: Hash of the previous event in the chain

This creates a blockchain-like structure where:
- Any modification breaks the chain
- Tampering is immediately detectable
- Original order is preserved

### Hash Computation

```python
hash_input = {
    "timestamp": event.timestamp,
    "event_type": event.event_type,
    "severity": event.severity,
    "source_service": event.source_service,
    "user_id": event.user_id,
    "action": event.action,
    "resource": event.resource,
    "result": event.result,
    "detection_type": event.detection_type,
    "metadata": event.metadata,
    "previous_hash": previous_event.event_hash
}

event_hash = SHA256(JSON.stringify(hash_input, sorted_keys=True))
```

### Optional HMAC Signatures

For additional security, enable HMAC signatures:

```bash
export ENABLE_SIGNATURES=true
export SIGNATURE_SECRET="your-secret-key-here"
```

Each event is signed with HMAC-SHA256 using the secret key.

## Compliance Mappings

### SOX (Sarbanes-Oxley Act)

**Requirements Met**:
- ✅ Immutable audit trails for financial transactions
- ✅ 7-year retention for user actions
- ✅ Access logging (who accessed what, when)
- ✅ Tamper-evident records
- ✅ Segregation of duties (separate write/read permissions)

**Recommended Configuration**:
```json
{
  "retention_policies": {
    "financial_transaction": {
      "retention_days": 2555,
      "archive_enabled": true
    }
  }
}
```

### HIPAA (Health Insurance Portability and Accountability Act)

**Requirements Met**:
- ✅ Audit controls (§164.312(b))
- ✅ Access logging and monitoring
- ✅ Integrity controls (§164.312(c)(1))
- ✅ Authentication tracking
- ✅ 6-year minimum retention

**Recommended Configuration**:
- Log all PHI access as `user_action` events
- Include patient ID in metadata (encrypted)
- Tag with `["phi", "hipaa"]`
- Set severity to "high" for sensitive operations

### PCI DSS (Payment Card Industry Data Security Standard)

**Requirements Met**:
- ✅ Requirement 10.1: Audit trails for system components
- ✅ Requirement 10.2: Automated audit trails for user actions
- ✅ Requirement 10.3: Record required audit trail entries
- ✅ Requirement 10.5: Secure audit trails from alteration
- ✅ Requirement 10.6: Review logs daily
- ✅ Requirement 10.7: Retain audit trail history for 1+ year

**Recommended Configuration**:
- Log all cardholder data access
- Include truncated PAN in metadata (last 4 digits only)
- Tag with `["pci", "cardholder_data"]`
- Retention: 365 days minimum, 1095 days recommended

### GDPR (General Data Protection Regulation)

**Requirements Met**:
- ✅ Article 32: Security of processing
- ✅ Article 33: Breach notification (via detection logs)
- ✅ Article 30: Records of processing activities
- ✅ Integrity and confidentiality guarantees

**GDPR-Specific Considerations**:
- **Right to Erasure**: May require special handling
- **Data Minimization**: Configure appropriate retention periods
- **Purpose Limitation**: Tag events with processing purpose

**Handling Right to Erasure**:
```python
# Pseudonymization approach
def handle_erasure_request(user_id):
    # Don't delete events (breaks immutability)
    # Instead, pseudonymize in metadata
    client.log_user_action(
        user_id="pseudonymized",
        action="data_erasure",
        resource=f"user:{user_id}",
        result="success",
        metadata={
            "reason": "gdpr_right_to_erasure",
            "original_user_hash": hash(user_id)
        },
        tags=["gdpr", "erasure"]
    )
```

### ISO 27001 (Information Security Management)

**Requirements Met**:
- ✅ A.12.4.1: Event logging
- ✅ A.12.4.2: Protection of log information
- ✅ A.12.4.3: Administrator and operator logs
- ✅ A.12.4.4: Clock synchronization

**Recommended Configuration**:
- Log all security-relevant events
- Include system events for infrastructure changes
- Maintain NTP synchronization for accurate timestamps

### NIST 800-53

**Controls Addressed**:
- **AU-2**: Audit Events
- **AU-3**: Content of Audit Records
- **AU-4**: Audit Storage Capacity
- **AU-6**: Audit Review, Analysis, and Reporting
- **AU-7**: Audit Reduction and Report Generation
- **AU-8**: Time Stamps
- **AU-9**: Protection of Audit Information
- **AU-10**: Non-repudiation
- **AU-11**: Audit Record Retention

## Security Features

### Transport Security

All API communications should use TLS 1.2+:

```nginx
# Nginx configuration
server {
    listen 443 ssl http2;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://audit-service:8000;
    }
}
```

### Authentication and Authorization

Implement API authentication:

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if not verify_key(x_api_key):
        raise HTTPException(status_code=401)
    return x_api_key
```

### Network Segmentation

Deploy audit service in isolated network:
- Separate VPC/VLAN for audit infrastructure
- Firewall rules limiting access
- No direct internet exposure

### Encryption at Rest

Enable PostgreSQL encryption:

```bash
# PostgreSQL configuration
encrypt = on
ssl = on
ssl_cert_file = '/path/to/cert.pem'
ssl_key_file = '/path/to/key.pem'
```

### Rate Limiting

Protect against DoS attacks:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/events")
@limiter.limit("100/minute")
async def create_event(request: Request, event: AuditEventCreate):
    ...
```

## Audit Access Logging (Meta-Auditing)

All queries to audit events are themselves logged:

```sql
SELECT * FROM audit_access_log
ORDER BY timestamp DESC
LIMIT 10;
```

**Columns**:
- `timestamp`: When the access occurred
- `accessor_id`: Who accessed the logs
- `accessor_ip`: From which IP
- `operation`: Type of operation (query, verify, etc.)
- `query_filters`: What filters were used
- `records_accessed`: How many records were returned

## Compliance Checklist

### Implementation
- [x] Append-only storage with database triggers
- [x] Cryptographic hash chaining
- [x] Optional HMAC signatures
- [x] Configurable retention policies
- [x] Archival support
- [x] Metadata for context
- [x] Structured event types
- [x] Query API with filtering
- [x] Meta-auditing (access logs)
- [x] Integrity verification

### Operations
- [ ] Enable TLS for all connections
- [ ] Configure authentication/authorization
- [ ] Set up network segmentation
- [ ] Enable encryption at rest
- [ ] Configure backup and recovery
- [ ] Set up monitoring and alerting
- [ ] Document incident response procedures
- [ ] Establish log review procedures
- [ ] Train staff on audit logging

### Compliance
- [ ] Document retention policies
- [ ] Map events to compliance requirements
- [ ] Establish archival procedures
- [ ] Configure legal hold process
- [ ] Document access controls
- [ ] Perform regular integrity checks
- [ ] Conduct compliance audits
- [ ] Maintain audit trail documentation

## Testing Compliance

### Immutability Test

```python
def test_immutability():
    # Create event
    event = client.log_user_action(...)
    
    # Attempt modification (should fail)
    try:
        db.execute(f"UPDATE audit_events SET severity='high' WHERE id={event.id}")
        assert False, "Modification should be prevented"
    except Exception as e:
        assert "WORM protection" in str(e)
```

### Integrity Test

```python
def test_integrity():
    # Create multiple events
    for i in range(100):
        client.log_user_action(...)
    
    # Verify chain
    result = client.verify_integrity(limit=100)
    assert result['status'] == 'ok'
    assert result['verified'] == 100
```

### Retention Test

```python
def test_retention():
    # Check retention policies
    policy = client._make_request("GET", "/api/v1/retention/policies/user_action")
    assert policy['retention_days'] >= 2555  # 7 years for SOX
```

## Reporting and Dashboards

See [Query Samples](../dashboards/query_samples.md) for compliance reporting examples:
- Access reports (who accessed what)
- Security incident timelines
- User activity summaries
- Detection analytics
- Compliance audit reports

## Support and Documentation

For compliance questions or certification support:
- Review this documentation
- Consult your legal/compliance team
- Consider third-party audit of implementation
- Maintain documentation of configuration and procedures

## References

- [SOX Compliance Guide](https://www.sec.gov/spotlight/sarbanes-oxley.htm)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/)
- [PCI DSS v4.0](https://www.pcisecuritystandards.org/)
- [GDPR Official Text](https://gdpr-info.eu/)
- [ISO 27001:2013](https://www.iso.org/standard/54534.html)
- [NIST 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
