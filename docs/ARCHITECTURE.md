# Threat Intelligence Platform - Architecture Document

## Overview

The Threat Intelligence (TI) Platform is a modular, scalable system designed to aggregate, correlate, and manage threat data from multiple sources. The architecture follows a monorepo pattern with clear service boundaries, enabling independent scaling and evolution of different components.

## Monorepo Structure

```
threat-intelligence-platform/
├── services/                 # Microservices
│   └── api/                 # Main API service (FastAPI)
├── libs/                    # Shared libraries
│   ├── core/               # Core domain models
│   └── config/             # Configuration management
├── docs/                   # Documentation
├── tests/                  # Test suite
├── pyproject.toml         # Project configuration
└── .github/               # CI/CD workflows (future)
```

## Core Components

### 1. API Service (`services/api`)

**Purpose**: Primary REST API for threat intelligence operations.

**Framework**: FastAPI (Python 3.9+)

**Endpoints**:
- `/health` - Health check
- `/ready` - Readiness probe
- `/api/v1/assets` - Asset management
- `/api/v1/indicators` - Threat indicator management
- `/api/v1/events` - Threat event management

**Features**:
- Async request handling for high throughput
- Type-safe request/response validation using Pydantic
- Structured logging and error handling
- CORS and security middleware (ready for implementation)

### 2. Core Libraries (`libs/core`)

**Purpose**: Shared domain models and business logic.

**Models**:

#### Asset
Represents infrastructure components to be protected:
- **Fields**: id, name, asset_type, metadata, timestamps
- **Types**: SERVER, WORKSTATION, NETWORK_DEVICE, APPLICATION, DATABASE, CONTAINER
- **Usage**: Baseline for threat correlation and impact assessment

#### Indicator
Represents threat intelligence data (IOCs):
- **Fields**: id, indicator_type, value, confidence, source, metadata, timestamps
- **Types**: IP_ADDRESS, DOMAIN, URL, FILE_HASH, EMAIL, CVE, MALWARE_FAMILY
- **Confidence**: 0.0-1.0 scale for indicator reliability
- **Usage**: Detection rules, blocking lists, correlation with events

#### ThreatEvent
Represents detected or reported security incidents:
- **Fields**: id, title, description, severity, asset_ids, indicator_ids, metadata, timestamps
- **Severity**: CRITICAL, HIGH, MEDIUM, LOW, INFO
- **Relationships**: Links to affected assets and related indicators
- **Usage**: Timeline, alerting, incident tracking

### 3. Configuration Management (`libs/config`)

**Purpose**: Centralized configuration and data source registry.

**Features**:

#### Settings
- Environment-based configuration using Pydantic Settings
- Supports `.env` file loading
- Nested configuration via `__` delimiter (e.g., `DATA_SOURCES__SOURCES__0__NAME`)
- Override via environment variables

#### DataSourceRegistry
- Configuration-driven registry of data sources
- Enable/disable sources without code changes
- Metadata and custom configuration per source
- Methods:
  - `get_enabled_sources()` - Retrieve active sources
  - `get_source_by_name(name)` - Lookup specific source

**Configuration Keys**:
```
APP_NAME                  - Application name
DEBUG                     - Debug mode flag
LOG_LEVEL                 - Logging level
API_HOST                  - API bind address
API_PORT                  - API listen port
API_PREFIX                - API endpoint prefix
TIMESERIES_DB_URL         - Time-series database connection
DOCUMENT_DB_URL           - Document database connection
```

## Data Storage Architecture

### Time-Series Database (Events Storage)
**Purpose**: High-throughput event ingestion and time-based queries

**Use Cases**:
- Store threat events with timestamps
- Query events by time range
- Aggregation and trend analysis
- Retention policies and data archival

**Recommended Solutions**:
- InfluxDB - Purpose-built time-series database
- TimescaleDB - PostgreSQL extension for time-series
- Prometheus - Metrics and event aggregation

**Connection**: `TIMESERIES_DB_URL` configuration

### Document Database (Indicators Storage)
**Purpose**: Flexible schema for threat indicators and assets

**Use Cases**:
- Store and query indicators with complex metadata
- Asset inventory with variable attributes
- Source-specific metadata preservation
- Rich indexing and text search

**Recommended Solutions**:
- MongoDB - Document-oriented NoSQL database
- CouchDB - Document-centric with built-in replication
- Elasticsearch - Full-text search and analytics

**Connection**: `DOCUMENT_DB_URL` configuration

## Service Boundaries

### API Service Responsibilities
- Request validation and routing
- Authentication and authorization (future)
- Response formatting and versioning
- Error handling and logging
- Rate limiting (future)

### Data Access Layer (Future)
- Database connection pooling
- Query abstraction and optimization
- Migration management
- Transaction handling

### Business Logic Layer (Future)
- Indicator parsing and normalization
- Event correlation and enrichment
- Asset impact assessment
- Deduplication and merging

### Data Source Integration (Future)
- Source-specific connectors
- Data parsing and transformation
- Scheduling and polling
- Error recovery and retries

## Data Flows

### Threat Event Creation Flow
```
1. External system/API calls POST /api/v1/events
2. FastAPI validates request payload (Pydantic)
3. Service creates ThreatEvent model instance
4. Event is persisted to time-series database
5. Event is indexed and made searchable
6. Response returned with 201 status and event ID
```

### Indicator Enrichment Flow
```
1. Data source connector fetches indicators
2. Registry determines enabled sources
3. Indicator values are parsed and normalized
4. Confidence scores are calculated
5. Indicators are batch-upserted to document DB
6. Related events are updated with new indicators
7. Detection rules are notified of updates
```

### Asset Impact Assessment Flow
```
1. New threat event is detected
2. Service queries indicators related to event
3. Service queries assets that match indicators
4. Impact severity is calculated per asset
5. Notifications are sent to asset owners
6. Metrics are recorded for trend analysis
```

## Integration Points

### Detection System
- **Interface**: REST API endpoint or message queue
- **Format**: ThreatEvent model (JSON)
- **Frequency**: Real-time or batch
- **Example**: IDS/IPS systems, SIEM, custom detectors

### Scanning System
- **Interface**: Asset creation/update endpoints
- **Format**: Asset model (JSON)
- **Frequency**: Scheduled (daily/hourly)
- **Example**: Vulnerability scanners, asset discovery tools

### Logging System
- **Interface**: Standard Python logging
- **Format**: Structured logs (JSON)
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Aggregation**: ELK Stack, Splunk, CloudWatch (future)

### Monitoring System
- **Interface**: Prometheus metrics endpoint (future)
- **Metrics**: 
  - API request latency
  - Event ingestion rate
  - Database query performance
  - Data source sync status
- **Integration**: Grafana dashboards (future)

## Deployment Considerations

### Containerization
- Dockerfile for API service
- Docker Compose for local development
- Container health checks

### Environment Configuration
- Separate configurations for dev, staging, production
- Secrets management (environment variables, Vault)
- Database connection pooling

### Scaling Strategy
- Horizontal scaling via load balancer
- Database replication and sharding
- Message queue for asynchronous processing (future)
- Caching layer for hot data (future)

### High Availability
- Multiple API service replicas
- Database failover and backup
- Dead letter queues for failed events
- Circuit breakers for external dependencies (future)

## Security Considerations

### Authentication
- API key validation (future)
- OAuth2/JWT token support (future)
- Service-to-service authentication (future)

### Authorization
- Role-based access control (RBAC) (future)
- Resource-level permissions (future)
- Audit logging of access (future)

### Data Protection
- Encryption at rest (future)
- Encryption in transit (TLS) (future)
- Data anonymization for sensitive fields (future)

### Input Validation
- Pydantic schema validation
- Type checking and constraints
- SQL injection prevention (prepared statements)
- XSS prevention (output encoding)

## Testing Strategy

### Unit Tests
- Model validation tests
- Configuration management tests
- Business logic tests
- Coverage target: >80%

### Integration Tests
- API endpoint tests
- Database interaction tests
- Data source registry tests

### Load Tests
- Event ingestion throughput
- Query response times
- Concurrent connection handling

### Security Tests
- Input validation and sanitization
- Authentication/authorization flows
- Rate limiting and DDoS protection

## Future Enhancements

1. **Advanced Threat Correlation**: ML-based indicator correlation
2. **Automated Response**: Integration with SOAR platforms
3. **Threat Intelligence Sharing**: STIX/TAXII protocol support
4. **Real-time Streaming**: Kafka/Pub-Sub for event streaming
5. **Advanced Analytics**: Trend analysis and forecasting
6. **GraphQL API**: Alternative to REST for complex queries
7. **Caching Layer**: Redis for performance optimization
8. **Message Queue**: Asynchronous processing pipeline
9. **Multi-tenancy**: Support multiple security teams
10. **Mobile App**: Mobile threat intelligence access

## Technology Stack Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.9+ | Ecosystem, data science integration |
| Web Framework | FastAPI | Speed, async support, type safety |
| Data Validation | Pydantic | Type hints, validation, serialization |
| Configuration | Pydantic Settings | Unified config management |
| Testing | pytest | Comprehensive, async support |
| Time-Series DB | InfluxDB/TimescaleDB | Purpose-built, scalable |
| Document DB | MongoDB/CouchDB | Flexible schema, rich queries |
| Containerization | Docker | Portability, consistency |
| CI/CD | GitHub Actions | Integrated, event-driven |

## Conclusion

The Threat Intelligence Platform provides a solid foundation for building a comprehensive security operations capability. The modular architecture allows for independent evolution of components, while the configuration-driven approach enables flexible deployment and integration with existing security tools and processes.
