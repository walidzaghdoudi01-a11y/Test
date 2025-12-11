import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'audit-service'))

from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from app.models.schemas import AuditEventCreate
from app.services.audit_service import AuditService


def test_cannot_update_audit_event(clean_db):
    """Test that audit events cannot be updated (WORM guarantee)."""
    service = AuditService(clean_db)
    
    event = AuditEventCreate(
        event_type="user_action",
        severity="medium",
        user_id="user123",
        action="login",
        resource="api",
        result="success"
    )
    
    result = service.create_event(event)
    event_id = result["id"]
    
    with pytest.raises(DatabaseError, match="Audit events cannot be modified"):
        clean_db.execute(
            text("UPDATE audit_events SET severity = 'high' WHERE id = :id"),
            {"id": event_id}
        )
        clean_db.commit()


def test_cannot_delete_audit_event(clean_db):
    """Test that audit events cannot be deleted (WORM guarantee)."""
    service = AuditService(clean_db)
    
    event = AuditEventCreate(
        event_type="detection",
        severity="high",
        detection_type="malware",
        source_service="scanner"
    )
    
    result = service.create_event(event)
    event_id = result["id"]
    
    with pytest.raises(DatabaseError, match="Audit events cannot be deleted"):
        clean_db.execute(
            text("DELETE FROM audit_events WHERE id = :id"),
            {"id": event_id}
        )
        clean_db.commit()


def test_can_archive_event(clean_db):
    """Test that events can be marked as archived (allowed update)."""
    service = AuditService(clean_db)
    
    event = AuditEventCreate(
        event_type="scan",
        severity="low",
        scan_id="scan123",
        source_service="scanner",
        result="clean"
    )
    
    result = service.create_event(event)
    event_id = result["id"]
    
    clean_db.execute(
        text("""
            UPDATE audit_events 
            SET archived = TRUE, archive_location = 's3://bucket/archive'
            WHERE id = :id
        """),
        {"id": event_id}
    )
    clean_db.commit()
    
    archived = clean_db.execute(
        text("SELECT archived, archive_location FROM audit_events WHERE id = :id"),
        {"id": event_id}
    ).fetchone()
    
    assert archived[0] is True
    assert archived[1] == "s3://bucket/archive"


def test_hash_chain_integrity(clean_db):
    """Test that hash chain is maintained correctly."""
    service = AuditService(clean_db)
    
    events = [
        AuditEventCreate(
            event_type="user_action",
            severity="low",
            user_id=f"user{i}",
            action="action",
            resource="resource",
            result="success"
        )
        for i in range(5)
    ]
    
    for event in events:
        service.create_event(event)
    
    integrity = service.verify_chain_integrity(limit=5)
    
    assert integrity["status"] == "ok"
    assert integrity["verified"] == 5
    assert len(integrity["errors"]) == 0


def test_tampered_hash_detected(clean_db):
    """Test that tampering with hash is detected."""
    service = AuditService(clean_db)
    
    event = AuditEventCreate(
        event_type="user_action",
        severity="medium",
        user_id="user123",
        action="login",
        resource="api",
        result="success"
    )
    
    result = service.create_event(event)
    
    # Temporarily disable trigger to simulate tampering
    clean_db.execute(text("ALTER TABLE audit_events DISABLE TRIGGER audit_events_immutable"))
    clean_db.execute(
        text("UPDATE audit_events SET event_hash = 'tampered_hash' WHERE id = :id"),
        {"id": result["id"]}
    )
    clean_db.commit()
    clean_db.execute(text("ALTER TABLE audit_events ENABLE TRIGGER audit_events_immutable"))
    
    integrity = service.verify_chain_integrity(limit=1)
    
    assert integrity["status"] == "integrity_violation"
    assert len(integrity["errors"]) > 0


def test_sequential_hash_linking(clean_db):
    """Test that events are properly linked via hash chain."""
    service = AuditService(clean_db)
    
    event1 = AuditEventCreate(
        event_type="user_action",
        severity="low",
        user_id="user1",
        action="login",
        resource="api",
        result="success"
    )
    result1 = service.create_event(event1)
    
    event2 = AuditEventCreate(
        event_type="user_action",
        severity="low",
        user_id="user2",
        action="logout",
        resource="api",
        result="success"
    )
    result2 = service.create_event(event2)
    
    # Second event's previous_hash should match first event's hash
    event2_data = service.get_event_by_id(result2["event_id"])
    event1_data = service.get_event_by_id(result1["event_id"])
    
    assert event2_data["previous_hash"] == event1_data["event_hash"]
    assert event1_data["previous_hash"] is None  # First event has no previous
