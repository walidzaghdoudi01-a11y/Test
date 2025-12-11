# Contributing to Audit Logging System

Thank you for your interest in contributing to the Audit Logging System!

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd audit-logging-system
   ```

2. **Run setup script**
   ```bash
   ./setup.sh
   ```

3. **Start development environment**
   ```bash
   docker-compose up -d postgres
   make migrate
   make start
   ```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the code style guidelines below
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests**
   ```bash
   make test
   make test-cov
   ```

4. **Format and lint**
   ```bash
   make format
   make lint
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style Guidelines

### Python Code Style

- **Formatting**: Use Black with line length 100
  ```bash
  black audit-service/ audit-client/ --line-length=100
  ```

- **Imports**: Use isort for import sorting
  ```bash
  isort audit-service/ audit-client/
  ```

- **Type Hints**: Use type hints for function parameters and returns
  ```python
  def create_event(event_data: AuditEventCreate) -> Dict[str, Any]:
      ...
  ```

- **Docstrings**: Use clear docstrings for public functions
  ```python
  def compute_hash(data: Dict[str, Any], previous_hash: Optional[str] = None) -> str:
      """Compute SHA-256 hash for tamper-evidence.
      
      Args:
          data: Event data to hash
          previous_hash: Hash of previous event for chaining
          
      Returns:
          64-character hexadecimal hash string
      """
      ...
  ```

### API Design

- Use RESTful conventions
- Version APIs: `/api/v1/...`
- Use appropriate HTTP status codes
- Include comprehensive error messages
- Document all endpoints with OpenAPI

### Database

- Never modify audit_events directly (WORM protected)
- Use Alembic for all schema changes
- Include both upgrade and downgrade migrations
- Test migrations on sample data

### Testing

- Write tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names: `test_<what>_<condition>`
- Group related tests in classes when appropriate
- Mock external dependencies

### Security

- Never log sensitive data (passwords, tokens, etc.)
- Use metadata field for PII (encrypt when necessary)
- Follow principle of least privilege
- Validate all inputs
- Use parameterized queries (SQLAlchemy handles this)

## Project Structure

```
audit-logging-system/
├── audit-service/          # Main API service
│   └── app/
│       ├── api/routes/     # API endpoints
│       ├── core/           # Core functionality
│       ├── db/             # Database setup
│       ├── models/         # Data models
│       └── services/       # Business logic
├── audit-client/           # Client library
│   └── audit_client/
│       ├── client.py       # Main client class
│       └── models.py       # Client models
├── database/               # Migrations
│   └── alembic/versions/   # Migration files
├── tests/                  # Test suite
├── docs/                   # Documentation
├── dashboards/             # Query examples
└── examples/               # Usage examples
```

## Adding New Features

### Adding a New Event Type

1. Update schema documentation (`docs/schema.md`)
2. Add event model in `audit-service/app/models/schemas.py`
3. Add API endpoint in `audit-service/app/api/routes/events.py`
4. Update client library in `audit-client/audit_client/client.py`
5. Add tests
6. Update examples

### Adding a New API Endpoint

1. Define route in appropriate file in `audit-service/app/api/routes/`
2. Use Pydantic models for request/response validation
3. Implement business logic in service layer
4. Add OpenAPI documentation
5. Write API tests
6. Update API documentation

### Adding a New Query Filter

1. Update `QueryParams` schema
2. Modify `query_events` in `AuditService`
3. Add database index if needed (via migration)
4. Add tests
5. Update query samples documentation

## Testing Guidelines

### Unit Tests

Test individual functions in isolation:

```python
def test_hash_computation():
    """Test hash computation for tamper-evidence."""
    data = {"event_type": "user_action", ...}
    hash1 = compute_hash(data, previous_hash=None)
    assert len(hash1) == 64
```

### Integration Tests

Test component interactions:

```python
def test_create_and_query_event(clean_db):
    """Test creating event and querying it back."""
    service = AuditService(clean_db)
    result = service.create_event(event_data)
    queried = service.get_event_by_id(result["event_id"])
    assert queried["event_id"] == result["event_id"]
```

### API Tests

Test HTTP endpoints:

```python
def test_create_user_action_event(api_client):
    """Test POST /api/v1/events/user-action endpoint."""
    response = api_client.post("/api/v1/events/user-action", json=data)
    assert response.status_code == 201
```

## Documentation

### Update Documentation When:

- Adding new features
- Changing API endpoints
- Modifying database schema
- Updating retention policies
- Adding compliance features

### Documentation Files

- `README.md` - Overview and quick start
- `docs/schema.md` - Database schema details
- `docs/retention.md` - Retention policies
- `docs/compliance.md` - Compliance requirements
- `dashboards/query_samples.md` - Query examples

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
feat: Add support for custom event types
fix: Correct hash chain verification logic
docs: Update retention policy documentation
test: Add tests for detection events
refactor: Simplify query parameter handling
```

Prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

## Review Process

1. All changes require tests
2. Code must pass linting and formatting checks
3. Tests must pass with >80% coverage
4. Documentation must be updated
5. Security implications must be considered
6. Breaking changes require major version bump

## Questions?

- Check existing documentation
- Review examples in `examples/`
- Look at existing tests for patterns
- Open an issue for clarification

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
