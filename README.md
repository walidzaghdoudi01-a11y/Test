# Security Scanning Service

A comprehensive security scanning service that performs scheduled vulnerability scans (dependency, container, configuration) and on-demand malware analysis.

## Features

-   **Multi-modal Scanning**: Supports Dependency, Container, Malware, and Configuration scans.
-   **Scheduling**: Built-in scheduler for periodic scans.
-   **API-Driven**: RESTful API for triggering scans and retrieving results.
-   **Extensible**: Easy to add new scanners and integrations.

## Architecture

The service is built with Python and FastAPI. It follows a modular architecture:

-   `app/api`: API endpoints.
-   `app/core`: Core components like Scheduler.
-   `app/models`: Data models.
-   `app/scanners`: Scanner interfaces and implementations.
-   `app/services`: Business logic and orchestration.

## Getting Started

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Service**:
    ```bash
    uvicorn app.main:app --reload
    ```

3.  **Run Tests**:
    ```bash
    pytest
    ```

## API Documentation

Once the service is running, visit `http://localhost:8000/docs` for the interactive Swagger UI.

### Key Endpoints

-   `POST /scans`: Trigger a new scan.
-   `GET /scans/{scan_id}`: Get scan status and results.
-   `POST /schedules`: Schedule a periodic scan.

## Extending the Service

### Adding a New Scanner

1.  Create a new class inheriting from `app.scanners.base.BaseScanner`.
2.  Implement the `scan` method.
3.  Register the new scanner in `app/services/scan_service.py` inside the `_scanners` dictionary.

Example:

```python
from app.scanners.base import BaseScanner
from app.models.scan import ScanRequest, ScanResult

class MyCustomScanner(BaseScanner):
    async def scan(self, request: ScanRequest, scan_id: str) -> ScanResult:
        # Implementation here
        pass
```

### Routing Results (Publishing)

Currently, results are stored in-memory. To route results to a datastore or queue (e.g., Kafka, SQS, Elasticsearch):

1.  Modify `app/services/scan_service.py`.
2.  In the `_run_scan` method, after getting the result, call your publisher service.

```python
# app/services/scan_service.py

async def _run_scan(self, request: ScanRequest, scan_id: str):
    # ...
    result = await scanner.scan(request, scan_id)
    self._scans[scan_id] = result
    
    # ADDED: Publish result
    await self.publisher.publish(result)
```
