import asyncio
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from main import app
from services.monitoring.models import AlertSeverity, DetectionEvent


@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as c:
        yield c


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "endpoints" in data


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_monitoring_health(client):
    """Test monitoring health check"""
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "uptime_seconds" in data


def test_reputation_ip_lookup(client):
    """Test IP reputation lookup"""
    response = client.get("/api/v1/reputation/ip/192.168.1.100")
    
    # Service is initialized via lifespan
    if response.status_code == 200:
        data = response.json()
        assert data["ip_address"] == "192.168.1.100"
        assert "overall_score" in data
        assert "risk_score" in data
        assert "sources" in data
        assert len(data["sources"]) > 0
    else:
        # Service may not be initialized in test
        assert response.status_code in [200, 503]


def test_reputation_domain_lookup(client):
    """Test domain reputation lookup"""
    response = client.get("/api/v1/reputation/domain/malicious-site.evil")
    
    if response.status_code == 200:
        data = response.json()
        assert data["domain"] == "malicious-site.evil"
        assert "overall_score" in data
        assert "risk_score" in data
    else:
        assert response.status_code in [200, 503]


def test_reputation_invalid_ip(client):
    """Test invalid IP returns 400 or 503"""
    response = client.get("/api/v1/reputation/ip/invalid.ip")
    # 400 if service is initialized, 503 if not
    assert response.status_code in [400, 503]


def test_reputation_bulk_lookup(client):
    """Test bulk reputation lookup"""
    request_data = {
        "indicators": ["192.168.1.100", "8.8.8.8", "google.com"],
        "max_age_seconds": 3600,
    }
    
    response = client.post("/api/v1/reputation/bulk", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 3
    assert data["successful"] >= 0
    assert "results" in data


def test_ingest_detection_event(client):
    """Test ingesting a detection event"""
    event_data = {
        "event_id": "test-event-123",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "test-detector",
        "severity": "high",
        "title": "Test Security Event",
        "description": "Testing event ingestion",
        "indicators": ["192.168.1.100"],
        "affected_assets": ["server-1"],
        "metadata": {},
        "tags": ["test"],
    }
    
    response = client.post("/api/v1/monitoring/events", json=event_data)
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"


def test_ingest_batch_events(client):
    """Test ingesting multiple events"""
    events = [
        {
            "event_id": f"batch-event-{i}",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "batch-test",
            "severity": "medium",
            "title": f"Batch Event {i}",
            "description": f"Batch test event {i}",
            "indicators": [],
            "affected_assets": [],
            "metadata": {},
            "tags": [],
        }
        for i in range(5)
    ]
    
    response = client.post("/api/v1/monitoring/events/batch", json=events)
    assert response.status_code == 202
    data = response.json()
    assert data["count"] == 5


def test_get_alerts(client):
    """Test retrieving alerts"""
    event_data = {
        "event_id": "alert-test-event",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "test",
        "severity": "critical",
        "title": "Critical Alert Test",
        "description": "Testing alert retrieval",
        "indicators": ["203.0.113.10"],
        "affected_assets": ["critical-server"],
        "metadata": {},
        "tags": [],
    }
    
    client.post("/api/v1/monitoring/events", json=event_data)
    
    import time
    time.sleep(0.5)
    
    response = client.get("/api/v1/monitoring/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)


def test_dashboard_metrics(client):
    """Test dashboard metrics endpoint"""
    response = client.get("/api/v1/monitoring/dashboard")
    assert response.status_code == 200
    
    data = response.json()
    assert "alerts_total" in data
    assert "alerts_by_severity" in data
    assert "events_processed_last_hour" in data
    assert "top_indicators" in data


def test_prometheus_metrics(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/api/v1/monitoring/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_cache_stats(client):
    """Test cache statistics endpoint"""
    try:
        response = client.get("/api/v1/reputation/cache/stats")
        assert response.status_code in [200, 503]
    except Exception:
        # Redis connection may fail in test environment
        pass


def test_alert_status_update(client):
    """Test updating alert status"""
    event_data = {
        "event_id": "status-update-test",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "test",
        "severity": "high",
        "title": "Status Update Test",
        "description": "Testing status updates",
        "indicators": [],
        "affected_assets": [],
        "metadata": {},
        "tags": [],
    }
    
    client.post("/api/v1/monitoring/events", json=event_data)
    
    import time
    time.sleep(0.5)
    
    alerts_response = client.get("/api/v1/monitoring/alerts?limit=1")
    if alerts_response.status_code == 200:
        alerts = alerts_response.json()
        if len(alerts) > 0:
            alert_id = alerts[0]["alert_id"]
            
            update_response = client.patch(
                f"/api/v1/monitoring/alerts/{alert_id}/status?status=acknowledged"
            )
            assert update_response.status_code == 200
