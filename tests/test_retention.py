from datetime import datetime, timedelta

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'audit-service'))

from sqlalchemy import text

from app.models.schemas import AuditEventCreate
from app.services.audit_service import AuditService
from app.services.retention_service import RetentionService


def test_get_retention_policy(clean_db):
    """Test getting retention policy for event types."""
    service = RetentionService(clean_db)
    
    policy = service.get_retention_policy("user_action")
    
    assert policy["event_type"] == "user_action"
    assert policy["retention_days"] == 2555
    assert policy["archive_enabled"] is True


def test_get_default_retention_policy(clean_db):
    """Test getting default retention policy for unknown event types."""
    service = RetentionService(clean_db)
    
    policy = service.get_retention_policy("unknown_type")
    
    assert policy["event_type"] == "default"
    assert policy["retention_days"] == 2555


def test_update_retention_policy(clean_db):
    """Test updating retention policy."""
    service = RetentionService(clean_db)
    
    updated = service.update_retention_policy(
        event_type="custom_event",
        retention_days=365,
        archive_enabled=True,
        archive_location="s3://bucket/archive"
    )
    
    assert updated["event_type"] == "custom_event"
    assert updated["retention_days"] == 365
    assert updated["archive_enabled"] is True
    assert updated["archive_location"] == "s3://bucket/archive"


def test_identify_expired_events(clean_db):
    """Test identifying events that have exceeded retention period."""
    audit_service = AuditService(clean_db)
    retention_service = RetentionService(clean_db)
    
    # Create event with short retention
    event = AuditEventCreate(
        event_type="scan",
        severity="low",
        scan_id="scan123",
        source_service="scanner",
        result="clean",
        retention_days=1
    )
    result = audit_service.create_event(event)
    
    # Manually set timestamp to past
    clean_db.execute(
        text("""
            UPDATE audit_events 
            SET timestamp = timestamp - INTERVAL '2 days'
            WHERE id = :id
        """),
        {"id": result["id"]}
    )
    clean_db.commit()
    
    expired = retention_service.get_expired_events()
    
    assert len(expired) > 0
    assert any(e["id"] == result["id"] for e in expired)


def test_archive_events(clean_db):
    """Test archiving events."""
    audit_service = AuditService(clean_db)
    retention_service = RetentionService(clean_db)
    
    # Create multiple events
    event_ids = []
    for i in range(3):
        event = AuditEventCreate(
            event_type="scan",
            severity="low",
            scan_id=f"scan{i}",
            source_service="scanner",
            result="clean"
        )
        result = audit_service.create_event(event)
        event_ids.append(result["id"])
    
    # Archive events
    archive_location = "s3://bucket/archive/2024-01-01"
    count = retention_service.archive_events(event_ids, archive_location)
    
    assert count == 3
    
    # Verify events are marked as archived
    for event_id in event_ids:
        archived = clean_db.execute(
            text("SELECT archived, archive_location FROM audit_events WHERE id = :id"),
            {"id": event_id}
        ).fetchone()
        
        assert archived[0] is True
        assert archived[1] == archive_location


def test_retention_statistics(clean_db):
    """Test getting retention statistics."""
    audit_service = AuditService(clean_db)
    retention_service = RetentionService(clean_db)
    
    # Create various events
    events = [
        AuditEventCreate(
            event_type="user_action",
            severity="medium",
            user_id="user1",
            action="login",
            resource="api",
            result="success"
        ),
        AuditEventCreate(
            event_type="detection",
            severity="high",
            detection_type="malware",
            source_service="scanner"
        ),
        AuditEventCreate(
            event_type="scan",
            severity="low",
            scan_id="scan1",
            source_service="scanner",
            result="clean"
        ),
    ]
    
    for event in events:
        audit_service.create_event(event)
    
    # Archive one event
    archived_event = AuditEventCreate(
        event_type="scan",
        severity="low",
        scan_id="scan2",
        source_service="scanner",
        result="clean"
    )
    result = audit_service.create_event(archived_event)
    retention_service.archive_events([result["id"]], "s3://bucket/archive")
    
    stats = retention_service.get_retention_statistics()
    
    assert stats["total_events"] == 4
    assert stats["archived_events"] == 1
    assert stats["active_events"] == 3
    assert len(stats["by_type"]) > 0


def test_archived_events_not_in_expired_list(clean_db):
    """Test that archived events are not included in expired events list."""
    audit_service = AuditService(clean_db)
    retention_service = RetentionService(clean_db)
    
    # Create and immediately archive an event with short retention
    event = AuditEventCreate(
        event_type="scan",
        severity="low",
        scan_id="scan123",
        source_service="scanner",
        result="clean",
        retention_days=1
    )
    result = audit_service.create_event(event)
    
    # Set timestamp to past
    clean_db.execute(
        text("UPDATE audit_events SET timestamp = timestamp - INTERVAL '2 days' WHERE id = :id"),
        {"id": result["id"]}
    )
    clean_db.commit()
    
    # Archive the event
    retention_service.archive_events([result["id"]], "s3://bucket/archive")
    
    # Should not appear in expired list
    expired = retention_service.get_expired_events()
    
    assert not any(e["id"] == result["id"] for e in expired)
