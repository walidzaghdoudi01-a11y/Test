import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'audit-service'))

from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.db.database import get_db


@pytest.fixture
def api_client(clean_db):
    """Create test API client with database override."""
    def override_get_db():
        try:
            yield clean_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_health_check(api_client):
    """Test health check endpoint."""
    response = api_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert "version" in data


def test_create_user_action_event(api_client):
    """Test creating a user action event."""
    event_data = {
        "user_id": "user123",
        "action": "login",
        "resource": "api",
        "result": "success",
        "severity": "medium"
    }
    
    response = api_client.post("/api/v1/events/user-action", json=event_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "user_action"
    assert data["user_id"] == "user123"
    assert data["action"] == "login"
    assert "event_id" in data
    assert "event_hash" in data


def test_create_detection_event(api_client):
    """Test creating a detection event."""
    event_data = {
        "detection_type": "malware",
        "severity": "high",
        "source_service": "scanner-1",
        "metadata": {"file": "/tmp/suspicious.exe"}
    }
    
    response = api_client.post("/api/v1/events/detection", json=event_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "detection"
    assert data["detection_type"] == "malware"
    assert data["severity"] == "high"


def test_create_scan_event(api_client):
    """Test creating a scan event."""
    event_data = {
        "scan_id": "scan-123",
        "scan_type": "vulnerability",
        "result": "clean",
        "source_service": "scanner",
        "severity": "low"
    }
    
    response = api_client.post("/api/v1/events/scan", json=event_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "scan"
    assert data["scan_id"] == "scan-123"


def test_get_event_by_id(api_client):
    """Test retrieving an event by ID."""
    # Create an event
    event_data = {
        "user_id": "user123",
        "action": "login",
        "resource": "api",
        "result": "success",
        "severity": "medium"
    }
    
    create_response = api_client.post("/api/v1/events/user-action", json=event_data)
    event_id = create_response.json()["event_id"]
    
    # Retrieve the event
    response = api_client.get(f"/api/v1/events/{event_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == event_id
    assert data["user_id"] == "user123"


def test_get_nonexistent_event(api_client):
    """Test retrieving a non-existent event."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = api_client.get(f"/api/v1/events/{fake_uuid}")
    
    assert response.status_code == 404


def test_query_events(api_client):
    """Test querying events with filters."""
    # Create multiple events
    for i in range(5):
        event_data = {
            "user_id": f"user{i}",
            "action": "login",
            "resource": "api",
            "result": "success",
            "severity": "medium"
        }
        api_client.post("/api/v1/events/user-action", json=event_data)
    
    # Query events
    response = api_client.get("/api/v1/query?event_type=user_action&limit=3")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["events"]) == 3


def test_query_with_filters(api_client):
    """Test querying with multiple filters."""
    # Create events with different types
    api_client.post("/api/v1/events/user-action", json={
        "user_id": "user1",
        "action": "login",
        "resource": "api",
        "result": "success",
        "severity": "low"
    })
    
    api_client.post("/api/v1/events/detection", json={
        "detection_type": "malware",
        "severity": "high",
        "source_service": "scanner"
    })
    
    # Query only user actions
    response = api_client.get("/api/v1/query?event_type=user_action")
    data = response.json()
    assert data["total"] == 1
    assert all(e["event_type"] == "user_action" for e in data["events"])
    
    # Query only high severity
    response = api_client.get("/api/v1/query?severity=high")
    data = response.json()
    assert data["total"] == 1
    assert all(e["severity"] == "high" for e in data["events"])


def test_verify_integrity(api_client):
    """Test verifying chain integrity."""
    # Create multiple events
    for i in range(3):
        api_client.post("/api/v1/events/user-action", json={
            "user_id": f"user{i}",
            "action": "login",
            "resource": "api",
            "result": "success",
            "severity": "medium"
        })
    
    response = api_client.get("/api/v1/events/verify/integrity?limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["verified"] == 3
    assert len(data["errors"]) == 0


def test_get_retention_policy(api_client):
    """Test getting retention policy."""
    response = api_client.get("/api/v1/retention/policies/user_action")
    
    assert response.status_code == 200
    data = response.json()
    assert data["event_type"] == "user_action"
    assert data["retention_days"] == 2555


def test_update_retention_policy(api_client):
    """Test updating retention policy."""
    policy_data = {
        "event_type": "custom_event",
        "retention_days": 365,
        "archive_enabled": True,
        "archive_location": "s3://bucket/archive"
    }
    
    response = api_client.put(
        "/api/v1/retention/policies/custom_event",
        json=policy_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["retention_days"] == 365
    assert data["archive_enabled"] is True


def test_get_retention_statistics(api_client):
    """Test getting retention statistics."""
    # Create some events
    for i in range(3):
        api_client.post("/api/v1/events/user-action", json={
            "user_id": f"user{i}",
            "action": "login",
            "resource": "api",
            "result": "success",
            "severity": "medium"
        })
    
    response = api_client.get("/api/v1/retention/statistics")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] >= 3
    assert "archived_events" in data
    assert "active_events" in data
