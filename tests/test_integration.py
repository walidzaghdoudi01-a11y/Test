"""
Integration tests that verify the complete flow of the audit logging system.
These tests can run with or without a live database using mocks.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'audit-service'))

from app.core.security import compute_hash, sign_event, verify_signature, verify_chain


def test_hash_computation():
    """Test hash computation for tamper-evidence."""
    data1 = {
        "timestamp": "2024-01-01T00:00:00Z",
        "event_type": "user_action",
        "severity": "medium",
        "user_id": "user123",
        "action": "login",
        "resource": "api",
        "result": "success"
    }
    
    hash1 = compute_hash(data1, previous_hash=None)
    assert len(hash1) == 64  # SHA-256 produces 64 hex characters
    
    # Same data should produce same hash
    hash1_repeat = compute_hash(data1, previous_hash=None)
    assert hash1 == hash1_repeat
    
    # Different data should produce different hash
    data2 = data1.copy()
    data2["action"] = "logout"
    hash2 = compute_hash(data2, previous_hash=None)
    assert hash1 != hash2


def test_hash_chaining():
    """Test that hash chaining works correctly."""
    event1_data = {
        "timestamp": "2024-01-01T00:00:00Z",
        "event_type": "user_action",
        "severity": "medium",
        "user_id": "user1",
        "action": "login"
    }
    
    event2_data = {
        "timestamp": "2024-01-01T00:00:01Z",
        "event_type": "user_action",
        "severity": "medium",
        "user_id": "user2",
        "action": "logout"
    }
    
    # First event has no previous hash
    hash1 = compute_hash(event1_data, previous_hash=None)
    
    # Second event links to first
    hash2 = compute_hash(event2_data, previous_hash=hash1)
    
    # Verify chain
    assert verify_chain(hash2, event2_data, hash1)
    
    # Tampering with data should break chain
    tampered_data = event2_data.copy()
    tampered_data["action"] = "hack"
    assert not verify_chain(hash2, tampered_data, hash1)


def test_hmac_signature():
    """Test HMAC signature generation and verification."""
    data = {
        "timestamp": "2024-01-01T00:00:00Z",
        "event_type": "user_action",
        "user_id": "user123"
    }
    
    secret = "test-secret-key"
    
    # Generate signature
    signature = sign_event(data, secret)
    assert len(signature) == 64  # HMAC-SHA256
    
    # Verify signature
    assert verify_signature(data, signature, secret)
    
    # Wrong secret should fail
    assert not verify_signature(data, signature, "wrong-secret")
    
    # Tampered data should fail
    tampered_data = data.copy()
    tampered_data["user_id"] = "hacker"
    assert not verify_signature(tampered_data, signature, secret)


def test_event_schemas():
    """Test that event schemas validate correctly."""
    from app.models.schemas import (
        UserActionEvent, 
        DetectionEvent, 
        ScanEvent,
        AuditEventCreate
    )
    
    # Valid user action
    user_action = UserActionEvent(
        user_id="user123",
        action="login",
        resource="api",
        result="success"
    )
    assert user_action.user_id == "user123"
    assert user_action.severity == "medium"  # default
    
    # Valid detection
    detection = DetectionEvent(
        detection_type="malware",
        severity="high",
        source_service="scanner"
    )
    assert detection.detection_type == "malware"
    
    # Valid scan
    scan = ScanEvent(
        scan_id="scan-123",
        scan_type="vulnerability",
        result="clean",
        source_service="scanner"
    )
    assert scan.scan_id == "scan-123"
    
    # Generic audit event
    audit_event = AuditEventCreate(
        event_type="custom",
        severity="low",
        metadata={"custom": "data"}
    )
    assert audit_event.event_type == "custom"


def test_query_params_validation():
    """Test query parameter validation."""
    from app.models.schemas import QueryParams
    
    # Valid params
    params = QueryParams(
        event_type="user_action",
        severity="high",
        limit=100
    )
    assert params.limit == 100
    assert params.offset == 0  # default
    
    # Limit validation
    with pytest.raises(Exception):
        QueryParams(limit=10000)  # exceeds max


def test_end_to_end_flow():
    """Test the complete flow from event creation to verification."""
    from app.models.schemas import AuditEventCreate
    
    # Create events
    events_data = [
        {
            "event_type": "user_action",
            "severity": "medium",
            "user_id": f"user{i}",
            "action": "login",
            "resource": "api",
            "result": "success"
        }
        for i in range(5)
    ]
    
    # Simulate hash chaining
    hashes = []
    previous_hash = None
    
    for event_data in events_data:
        event_hash = compute_hash(event_data, previous_hash)
        hashes.append({
            "data": event_data,
            "hash": event_hash,
            "previous_hash": previous_hash
        })
        previous_hash = event_hash
    
    # Verify chain integrity
    for i in range(len(hashes)):
        expected_prev = hashes[i-1]["hash"] if i > 0 else None
        assert hashes[i]["previous_hash"] == expected_prev
        
        # Verify hash
        computed = compute_hash(hashes[i]["data"], expected_prev)
        assert computed == hashes[i]["hash"]


def test_retention_policy_defaults():
    """Test default retention policy values."""
    from app.core.config import settings
    
    assert settings.DEFAULT_RETENTION_DAYS == 2555  # 7 years
    assert settings.ARCHIVE_ENABLED is True


def test_client_library_models():
    """Test client library model validation."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'audit-client'))
    from audit_client.models import UserActionEvent, DetectionEvent, QueryParams
    
    # User action
    user_event = UserActionEvent(
        user_id="user123",
        action="login",
        resource="api",
        result="success",
        metadata={"ip": "192.168.1.1"}
    )
    assert user_event.user_id == "user123"
    
    # Detection
    detection = DetectionEvent(
        detection_type="malware",
        severity="high",
        source_service="scanner",
        tags=["security", "malware"]
    )
    assert "security" in detection.tags
    
    # Query params
    query = QueryParams(
        event_type="user_action",
        limit=50
    )
    assert query.limit == 50
