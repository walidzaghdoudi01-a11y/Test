# Security Audit Logging System

A centralized, tamper-evident audit logging system with append-only storage, retention policies, and compliance guarantees.

## Features

- **Append-Only Storage**: PostgreSQL with WORM guarantees
- **Tamper-Evidence**: SHA-256 chaining for log integrity
- **Structured Events**: Support for detections, scans, user actions, and custom events
- **Retention Policies**: Automated log rotation and archival
- **Query API**: Filter and search audit events
- **Client Library**: Easy integration for services
- **Compliance**: Immutability guarantees for regulatory requirements

## Architecture

```
audit-logging-system/
├── audit-service/      # Main API service (FastAPI)
├── audit-client/       # Shared client library
├── database/           # Schema and migrations
├── tests/              # Comprehensive test suite
├── docs/               # Documentation
├── dashboards/         # Query samples and analytics
└── docker/             # Docker configuration
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Docker & Docker Compose (optional)

### Installation

1. **Clone and setup**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Database setup**:
```bash
# Using Docker
docker-compose up -d postgres

# Or configure PostgreSQL connection
export DATABASE_URL="postgresql://audituser:auditpass@localhost:5432/auditdb"
```

3. **Run migrations**:
```bash
cd database
alembic upgrade head
```

4. **Start the audit service**:
```bash
cd audit-service
uvicorn app.main:app --reload
```

### Using the Client Library

```python
from audit_client import AuditClient

# Initialize client
client = AuditClient(api_url="http://localhost:8000")

# Log a user action
client.log_user_action(
    user_id="user123",
    action="login",
    resource="api",
    result="success",
    metadata={"ip": "192.168.1.1"}
)

# Log a detection event
client.log_detection(
    detection_type="malware",
    severity="high",
    source="scanner-1",
    details={"file": "/tmp/suspicious.exe"}
)

# Query events
events = client.query_events(
    event_type="user_action",
    start_time="2024-01-01T00:00:00Z",
    limit=100
)
```

## API Documentation

Once running, visit:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=audit_service --cov=audit_client --cov-report=html

# Run specific test suites
pytest tests/test_immutability.py
pytest tests/test_retention.py
```

## Documentation

See [docs/](./docs/) for detailed documentation:
- [Schema Documentation](./docs/schema.md)
- [Retention Policies](./docs/retention.md)
- [Compliance Requirements](./docs/compliance.md)
- [Query Examples](./dashboards/query_samples.md)

## Security & Compliance

- **Immutability**: Database triggers prevent updates/deletes
- **Tamper-Evidence**: Each log entry contains hash of previous entry
- **Audit Trail**: All access to audit logs is itself logged
- **Retention**: Configurable retention with automated archival
- **Encryption**: TLS for transport, optional encryption at rest

## License

MIT License
