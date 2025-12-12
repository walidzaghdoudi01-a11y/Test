# Testing Guide

## Overview

The project uses pytest for comprehensive testing including unit tests, integration tests, and performance tests.

## Running Tests

### All Tests

```bash
pytest
```

### Unit Tests Only

```bash
pytest tests/unit/ -v
```

### Integration Tests Only

```bash
pytest tests/integration/ -v
```

### With Coverage Report

```bash
pytest --cov=services --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

### Specific Test File

```bash
pytest tests/unit/test_reputation_service.py -v
```

### Specific Test Function

```bash
pytest tests/unit/test_reputation_service.py::test_lookup_malicious_ip -v
```

## Test Structure

```
tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_reputation_service.py
│   └── test_streaming_processor.py
└── integration/
├── __init__.py
    └── test_api.py
```

## Unit Tests

### Reputation Service Tests

Located in `tests/unit/test_reputation_service.py`:

- IP reputation lookups (malicious, clean, invalid)
- Domain reputation lookups
- Input validation
- Risk score calculation
- Multi-source aggregation

### Streaming Processor Tests

Located in `tests/unit/test_streaming_processor.py`:

- Event ingestion
- Alert generation
- Notification delivery
- Burst detection
- Dashboard metrics
- High volume processing
- Indicator tracking

## Integration Tests

Located in `tests/integration/test_api.py`:

- API endpoint testing
- Health checks
- Event ingestion via API
- Reputation lookups via API
- Dashboard metrics
- Prometheus metrics
- Alert status updates

## Running Service for Manual Testing

### Start the Service

```bash
# In terminal 1
python main.py
```

### Test with curl

```bash
# Health check
curl http://localhost:8000/health

# Ingest event
curl -X POST http://localhost:8000/api/v1/monitoring/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test-1",
    "source": "manual-test",
    "severity": "high",
    "title": "Test Event",
    "description": "Manual testing",
    "indicators": ["192.168.1.100"],
    "affected_assets": ["server-1"]
  }'

# Get alerts
curl http://localhost:8000/api/v1/monitoring/alerts

# Lookup IP reputation
curl http://localhost:8000/api/v1/reputation/ip/192.168.1.100
```

### Test with Python Script

```bash
python test_service.py
```

## Test Fixtures

### Async Fixtures

```python
@pytest.fixture
async def processor():
    """Create streaming processor for testing"""
    notification_manager = NotificationManager()
    processor = StreamingProcessor(notification_manager)
    
    task = asyncio.create_task(processor.start())
    yield processor
    
    await processor.stop()
    task.cancel()
```

### Service Fixtures

```python
@pytest.fixture
def reputation_service():
    """Create reputation service for testing"""
    feeds = [MockThreatFeed(latency_ms=10)]
    aggregator = FeedAggregator(feeds)
    return ReputationLookupService(feed_aggregator=aggregator)
```

## Mocking

### Mock Notifiers

```python
email_notifier = MockEmailNotifier()
webhook_notifier = MockWebhookNotifier()

# Check sent alerts
assert len(email_notifier.sent_alerts) > 0
```

### Mock Feeds

```python
mock_feed = MockThreatFeed(name="TestFeed", latency_ms=10)
result = await mock_feed.lookup_ip("192.168.1.100")
```

## Performance Testing

### Simulate Alert Burst

```python
async def test_high_volume():
    for i in range(1000):
        event = DetectionEvent(
            event_id=f"perf-{i}",
            source="perf-test",
            severity=AlertSeverity.MEDIUM,
            title=f"Performance Test {i}",
            indicators=[f"10.0.{i//256}.{i%256}"],
        )
        await processor.ingest_event(event)
    
    await asyncio.sleep(2.0)
    metrics = processor.get_dashboard_metrics()
    assert metrics.events_processed_last_hour >= 1000
```

### Load Testing

Use locust or similar tools:

```python
from locust import HttpUser, task, between

class MonitoringUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    @task
    def ingest_event(self):
        self.client.post("/api/v1/monitoring/events", json={
            "event_id": f"load-{self.environment.runner.user_count}",
            "source": "load-test",
            "severity": "medium",
            "title": "Load Test",
            "description": "Performance testing",
        })
```

Run:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

## Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
addopts = 
    -v
    --cov=services
    --cov-report=html
    --asyncio-mode=auto
asyncio_mode = auto
timeout = 300
```

### Test Markers

```python
# Mark slow tests
@pytest.mark.slow
async def test_extensive_processing():
    pass

# Run only fast tests
pytest -m "not slow"

# Run only slow tests
pytest -m slow
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=services --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Troubleshooting

### Redis Connection Errors

If integration tests fail due to Redis:

```bash
# Start Redis
docker run -d -p 6379:6379 redis:latest

# Or skip cache tests
pytest -k "not cache"
```

### Async Test Issues

Ensure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

Configure in pytest.ini:
```ini
asyncio_mode = auto
```

### Test Timeout

Increase timeout for slow tests:
```python
@pytest.mark.timeout(600)
async def test_long_running():
    pass
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Fast**: Unit tests should run quickly (< 1s each)
3. **Clear Names**: Test names should describe what they test
4. **Single Assertion**: Focus on one thing per test
5. **Fixtures**: Use fixtures for common setup
6. **Cleanup**: Always clean up resources (use yield fixtures)
7. **Async**: Use async fixtures for async code
8. **Mocking**: Mock external dependencies (feeds, SMTP, etc.)

## Coverage Goals

- **Overall**: > 70%
- **Critical Paths**: > 90%
- **Models**: 100%
- **Utilities**: > 85%

## Writing New Tests

### Template for Unit Tests

```python
import pytest
from services.myservice import MyService

@pytest.fixture
def my_service():
    return MyService()

@pytest.mark.asyncio
async def test_my_feature(my_service):
    """Test description"""
    # Arrange
    input_data = "test"
    
    # Act
    result = await my_service.process(input_data)
    
    # Assert
    assert result is not None
    assert result.status == "success"
```

### Template for Integration Tests

```python
def test_api_endpoint(client):
    """Test API endpoint"""
    response = client.post("/api/v1/endpoint", json={"data": "test"})
    
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
```

## Continuous Testing

### Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw -- --tb=short
```

### Pre-commit Hook

Install pre-commit hook:
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/unit/ -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```
