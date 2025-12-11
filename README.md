# Threat Intelligence Platform

A foundational threat intelligence platform for aggregating, correlating, and managing threat data from multiple sources.

## Features

- **Core Domain Models**: Threat events, assets, and threat indicators
- **REST API**: FastAPI-based service with async support
- **Configuration-Driven**: Data source registry for flexible integration
- **Dual Storage**: Time-series database for events, document database for indicators
- **Type-Safe**: Pydantic validation for all data models
- **Well-Tested**: Comprehensive unit and integration tests
- **CI/CD Ready**: GitHub Actions workflow for automated testing and linting

## Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd threat-intelligence-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Running the API

```bash
python -m services.api.main
```

API will be available at: `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

### Running Tests

```bash
pytest
```

View coverage report:
```bash
pytest --cov=libs --cov=services
```

### Code Quality

Format, lint, and type-check:
```bash
black libs services tests
isort libs services tests
flake8 libs services tests
mypy libs services
```

## Architecture

The platform uses a monorepo structure with clear separation of concerns:

```
threat-intelligence-platform/
├── services/          # Microservices
│   └── api/          # Main FastAPI service
├── libs/             # Shared libraries
│   ├── core/         # Domain models
│   └── config/       # Configuration management
├── tests/            # Test suite
├── docs/             # Documentation
│   ├── ARCHITECTURE.md
│   └── DEVELOPMENT.md
└── README.md
```

For detailed architecture information, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /ready` - Readiness probe

### Assets
- `GET /api/v1/assets` - List all assets
- `POST /api/v1/assets` - Create new asset
- `GET /api/v1/assets/{asset_id}` - Get asset details
- `PUT /api/v1/assets/{asset_id}` - Update asset
- `DELETE /api/v1/assets/{asset_id}` - Delete asset

### Indicators
- `GET /api/v1/indicators` - List all indicators
- `POST /api/v1/indicators` - Create new indicator
- `GET /api/v1/indicators/{indicator_id}` - Get indicator details
- `PUT /api/v1/indicators/{indicator_id}` - Update indicator
- `DELETE /api/v1/indicators/{indicator_id}` - Delete indicator

### Threat Events
- `GET /api/v1/events` - List all threat events
- `POST /api/v1/events` - Create new threat event
- `GET /api/v1/events/{event_id}` - Get event details
- `PUT /api/v1/events/{event_id}` - Update event
- `DELETE /api/v1/events/{event_id}` - Delete event

## Core Models

### Asset
Represents infrastructure components:
```python
Asset(
    id="asset-1",
    name="Production Server 1",
    asset_type=AssetType.SERVER,
    metadata={"ip": "192.168.1.1", "os": "Linux"}
)
```

### Indicator
Represents threat intelligence data (IOCs):
```python
Indicator(
    id="ind-1",
    indicator_type=IndicatorType.IP_ADDRESS,
    value="192.168.1.100",
    confidence=0.95,
    source="external-feed"
)
```

### ThreatEvent
Represents detected security incidents:
```python
ThreatEvent(
    id="event-1",
    title="Suspicious Activity Detected",
    severity=SeverityLevel.HIGH,
    asset_ids=["asset-1"],
    indicator_ids=["ind-1"],
    detected_at=datetime.utcnow()
)
```

## Configuration

### Environment Variables

Create a `.env` file:
```
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
TIMESERIES_DB_URL=file:///var/lib/ti-platform/timeseries
DOCUMENT_DB_URL=file:///var/lib/ti-platform/documents
```

### Data Sources

Configure data sources via environment:
```
DATA_SOURCES__SOURCES__0__NAME=external-feed-1
DATA_SOURCES__SOURCES__0__TYPE=external
DATA_SOURCES__SOURCES__0__ENABLED=true
DATA_SOURCES__SOURCES__0__CONFIG__URL=https://example.com/feed
```

## Development

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development instructions.

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=libs --cov=services

# Specific test file
pytest tests/test_models.py

# Verbose output
pytest -v
```

### Code Quality Tools

```bash
# Format code
black libs services tests

# Sort imports
isort libs services tests

# Lint
flake8 libs services tests

# Type check
mypy libs services
```

## CI/CD

The project includes GitHub Actions workflows for:
- Running tests across Python 3.9, 3.10, 3.11
- Code linting and formatting checks
- Type checking with mypy
- Code coverage reporting
- Artifact building

See [.github/workflows/ci.yml](.github/workflows/ci.yml) for details.

## Storage Architecture

### Time-Series Database
Used for high-throughput event ingestion and time-based queries.

**Recommended**:
- InfluxDB
- TimescaleDB
- Prometheus

### Document Database
Used for indicators, assets, and flexible-schema data.

**Recommended**:
- MongoDB
- CouchDB
- Elasticsearch

Configuration via `TIMESERIES_DB_URL` and `DOCUMENT_DB_URL` environment variables.

## Integration Points

The platform integrates with:
- **Detection Systems**: IDS/IPS, SIEM, custom detectors
- **Scanning Systems**: Vulnerability scanners, asset discovery tools
- **Logging Systems**: ELK Stack, Splunk, CloudWatch
- **Monitoring Systems**: Prometheus, Grafana

## Future Enhancements

- Advanced threat correlation with ML models
- SOAR platform integration for automated response
- STIX/TAXII protocol support for threat sharing
- Real-time streaming with Kafka/Pub-Sub
- GraphQL API for complex queries
- Redis caching layer
- Multi-tenancy support
- Mobile app for threat intelligence access

## Contributing

1. Create a feature branch from `main`
2. Make your changes and add tests
3. Ensure all tests pass and code quality checks pass
4. Submit a pull request

## Testing Requirements

- Minimum 80% code coverage
- All tests must pass
- Code must pass linting and type checking

## License

[Add your license here]

## Support

For issues, questions, or contributions, please open an issue or contact the development team.

## Technology Stack

- **Language**: Python 3.9+
- **Web Framework**: FastAPI
- **Data Validation**: Pydantic
- **Testing**: pytest
- **Code Quality**: black, isort, flake8, mypy
- **CI/CD**: GitHub Actions
- **Time-Series DB**: InfluxDB / TimescaleDB (recommended)
- **Document DB**: MongoDB / CouchDB (recommended)

## Project Status

This is the initial scaffold of the Threat Intelligence Platform with foundational structure, core models, and basic API endpoints. Full functionality will be implemented in subsequent phases.
