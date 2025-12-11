import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from audit_client import AuditClient, UserActionEvent, DetectionEvent, ScanEvent, AuditClientError


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for testing."""
    with patch("audit_client.client.httpx.Client") as mock_client:
        yield mock_client


def test_client_initialization():
    """Test audit client initialization."""
    client = AuditClient(
        api_url="http://example.com:8080",
        timeout=60.0,
        api_key="test-key"
    )
    
    assert client.api_url == "http://example.com:8080"
    assert client.timeout == 60.0
    assert client.api_key == "test-key"
    assert "Authorization" in client.headers


def test_log_user_action(mock_httpx_client):
    """Test logging user action events."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "id": 1,
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "user_action",
        "severity": "medium",
        "event_hash": "abc123",
        "previous_hash": None,
        "archived": False,
        "created_at": datetime.utcnow().isoformat()
    }
    mock_response.raise_for_status = Mock()
    
    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_context)
    mock_context.__exit__ = Mock(return_value=False)
    mock_context.request = Mock(return_value=mock_response)
    mock_httpx_client.return_value = mock_context
    
    client = AuditClient()
    result = client.log_user_action(
        user_id="user123",
        action="login",
        resource="api",
        result="success",
        metadata={"ip": "192.168.1.1"}
    )
    
    assert result.event_type == "user_action"
    assert result.severity == "medium"


def test_log_detection(mock_httpx_client):
    """Test logging detection events."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "id": 2,
        "event_id": "223e4567-e89b-12d3-a456-426614174001",
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "detection",
        "severity": "high",
        "event_hash": "def456",
        "previous_hash": "abc123",
        "archived": False,
        "created_at": datetime.utcnow().isoformat()
    }
    mock_response.raise_for_status = Mock()
    
    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_context)
    mock_context.__exit__ = Mock(return_value=False)
    mock_context.request = Mock(return_value=mock_response)
    mock_httpx_client.return_value = mock_context
    
    client = AuditClient()
    result = client.log_detection(
        detection_type="malware",
        severity="high",
        source_service="scanner-1",
        metadata={"file": "/tmp/suspicious.exe"}
    )
    
    assert result.event_type == "detection"
    assert result.severity == "high"


def test_log_scan(mock_httpx_client):
    """Test logging scan events."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "id": 3,
        "event_id": "323e4567-e89b-12d3-a456-426614174002",
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "scan",
        "severity": "low",
        "event_hash": "ghi789",
        "previous_hash": "def456",
        "archived": False,
        "created_at": datetime.utcnow().isoformat()
    }
    mock_response.raise_for_status = Mock()
    
    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_context)
    mock_context.__exit__ = Mock(return_value=False)
    mock_context.request = Mock(return_value=mock_response)
    mock_httpx_client.return_value = mock_context
    
    client = AuditClient()
    result = client.log_scan(
        scan_id="scan-123",
        scan_type="vulnerability",
        result="clean",
        source_service="scanner",
        resource="/app/server"
    )
    
    assert result.event_type == "scan"
    assert result.severity == "low"


def test_query_events(mock_httpx_client):
    """Test querying audit events."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "total": 10,
        "limit": 5,
        "offset": 0,
        "events": [
            {
                "id": i,
                "event_id": f"event-{i}",
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "user_action",
                "severity": "medium",
                "event_hash": f"hash-{i}",
                "previous_hash": None,
                "archived": False,
                "created_at": datetime.utcnow().isoformat()
            }
            for i in range(5)
        ]
    }
    mock_response.raise_for_status = Mock()
    
    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_context)
    mock_context.__exit__ = Mock(return_value=False)
    mock_context.request = Mock(return_value=mock_response)
    mock_httpx_client.return_value = mock_context
    
    client = AuditClient()
    result = client.query_events(
        event_type="user_action",
        severity="medium",
        limit=5
    )
    
    assert result["total"] == 10
    assert len(result["events"]) == 5


def test_verify_integrity(mock_httpx_client):
    """Test verifying chain integrity."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": "ok",
        "verified": 100,
        "total_checked": 100,
        "errors": []
    }
    mock_response.raise_for_status = Mock()
    
    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_context)
    mock_context.__exit__ = Mock(return_value=False)
    mock_context.request = Mock(return_value=mock_response)
    mock_httpx_client.return_value = mock_context
    
    client = AuditClient()
    result = client.verify_integrity(limit=100)
    
    assert result["status"] == "ok"
    assert result["verified"] == 100
    assert len(result["errors"]) == 0


def test_health_check(mock_httpx_client):
    """Test health check."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "status": "ok",
        "database": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
    mock_response.raise_for_status = Mock()
    
    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_context)
    mock_context.__exit__ = Mock(return_value=False)
    mock_context.request = Mock(return_value=mock_response)
    mock_httpx_client.return_value = mock_context
    
    client = AuditClient()
    result = client.health_check()
    
    assert result["status"] == "ok"
    assert result["database"] == "healthy"
