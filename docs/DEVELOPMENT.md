# Development Guide

## Getting Started

### Prerequisites
- Python 3.9 or higher
- pip or poetry
- Git

### Setup Development Environment

1. Clone the repository
```bash
git clone <repo-url>
cd threat-intelligence-platform
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks
```bash
pre-commit install
```

### Running the API

```bash
python -m services.api.main
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Running Tests

```bash
pytest
```

With coverage report:
```bash
pytest --cov=libs --cov=services --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_health.py
```

Run with verbose output:
```bash
pytest -v
```

### Linting and Code Quality

Format code with black:
```bash
black libs services tests
```

Sort imports:
```bash
isort libs services tests
```

Check with flake8:
```bash
flake8 libs services tests
```

Type checking:
```bash
mypy libs services
```

All together:
```bash
black libs services tests && isort libs services tests && flake8 libs services tests && mypy libs services && pytest
```

## Project Structure

### Services
- `services/api/` - Main FastAPI application
  - `app.py` - Application factory
  - `main.py` - Entry point
  - `routes/` - API endpoint handlers

### Libraries
- `libs/core/` - Domain models
  - `models.py` - Core data classes
- `libs/config/` - Configuration management
  - `settings.py` - Application settings and registry

### Tests
- `tests/` - Test suite
  - `conftest.py` - Pytest fixtures and configuration
  - `test_*.py` - Test modules

## Adding New Endpoints

1. Create a new route file in `services/api/routes/`:
```python
# services/api/routes/my_resource.py
from fastapi import APIRouter

router = APIRouter(prefix="/my-resource")

@router.get("")
async def list_resources():
    return []

@router.post("", status_code=201)
async def create_resource(resource: MyResourceModel):
    return resource
```

2. Include the router in `services/api/app.py`:
```python
from services.api.routes import my_resource

application.include_router(
    my_resource.router,
    prefix=settings.api_prefix,
    tags=["my-resource"]
)
```

3. Add tests in `tests/test_my_resource.py`

## Adding New Models

1. Add the model to `libs/core/models.py`:
```python
from pydantic import BaseModel

class MyModel(BaseModel):
    id: str
    name: str
    # ... fields
```

2. Export from `libs/core/__init__.py`

3. Add unit tests in `tests/test_models.py`

## Configuration

### Environment Variables

Create a `.env` file in the project root:
```
DEBUG=true
LOG_LEVEL=DEBUG
API_PORT=8000
TIMESERIES_DB_URL=file:///tmp/timeseries
DOCUMENT_DB_URL=file:///tmp/documents
```

### Data Sources Configuration

Configure data sources via environment:
```
DATA_SOURCES__SOURCES__0__NAME=external-feed
DATA_SOURCES__SOURCES__0__TYPE=external
DATA_SOURCES__SOURCES__0__ENABLED=true
DATA_SOURCES__SOURCES__0__CONFIG__URL=https://example.com/feed
```

Access in code:
```python
from libs.config import get_settings

settings = get_settings()
sources = settings.data_sources.get_enabled_sources()
```

## Testing Best Practices

1. **Unit Tests**: Test isolated components
```python
def test_asset_creation():
    asset = Asset(id="1", name="Server", asset_type=AssetType.SERVER)
    assert asset.id == "1"
```

2. **Integration Tests**: Test component interactions
```python
def test_api_endpoint(client):
    response = client.get("/api/v1/assets")
    assert response.status_code == 200
```

3. **Fixtures**: Use pytest fixtures for setup
```python
@pytest.fixture
def sample_asset():
    return Asset(id="1", name="Server", asset_type=AssetType.SERVER)
```

4. **Mocking**: Mock external dependencies
```python
from unittest.mock import patch

@patch('services.api.routes.db.query')
def test_with_mock(mock_query):
    mock_query.return_value = []
    # test code
```

## Common Tasks

### Add a New Model Field

1. Update `libs/core/models.py`
2. Add validation rules if needed
3. Update existing tests
4. Add new tests for the field

### Create a Data Migration

Database migrations will be added as the data layer is implemented.

### Update Dependencies

```bash
pip install --upgrade <package-name>
```

Update `pyproject.toml` with new version constraints.

### Release a New Version

1. Update version in `pyproject.toml`
2. Create a git tag: `git tag v0.2.0`
3. Push: `git push origin v0.2.0`

## Troubleshooting

### Import Errors

Make sure the virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -e ".[dev]"
```

### Test Failures

Check that all dependencies are installed:
```bash
pip install -e ".[dev]"
```

Clear pytest cache:
```bash
pytest --cache-clear
```

### Type Checking Errors

Run mypy with verbose output:
```bash
mypy libs services --show-error-codes
```

## Documentation

- See `docs/ARCHITECTURE.md` for system design
- API documentation at `/docs` when running the server
- Inline code documentation via docstrings

## Contributing

1. Create a feature branch
2. Make changes and add tests
3. Ensure all tests pass and linting is clean
4. Submit a pull request

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [Python 3.9 Documentation](https://docs.python.org/3.9/)
