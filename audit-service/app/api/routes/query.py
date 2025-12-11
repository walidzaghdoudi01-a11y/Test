from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import QueryParams, QueryResponse, RetentionPolicy
from app.services.audit_service import AuditService
from app.services.retention_service import RetentionService

router = APIRouter()


@router.get("/query", response_model=QueryResponse)
def query_events(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    detection_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    source_service: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Query audit events with filtering."""
    params = QueryParams(
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        action=action,
        detection_type=detection_type,
        start_time=start_time,
        end_time=end_time,
        source_service=source_service,
        tags=tags,
        limit=limit,
        offset=offset
    )
    
    service = AuditService(db)
    return service.query_events(params)


@router.get("/retention/policies/{event_type}", response_model=RetentionPolicy)
def get_retention_policy(
    event_type: str,
    db: Session = Depends(get_db)
):
    """Get retention policy for an event type."""
    service = RetentionService(db)
    policy = service.get_retention_policy(event_type)
    return RetentionPolicy(**policy)


@router.put("/retention/policies/{event_type}", response_model=RetentionPolicy)
def update_retention_policy(
    event_type: str,
    policy: RetentionPolicy,
    db: Session = Depends(get_db)
):
    """Update retention policy for an event type."""
    service = RetentionService(db)
    updated = service.update_retention_policy(
        event_type=event_type,
        retention_days=policy.retention_days,
        archive_enabled=policy.archive_enabled,
        archive_location=policy.archive_location
    )
    return RetentionPolicy(**updated)


@router.get("/retention/statistics")
def get_retention_statistics(db: Session = Depends(get_db)):
    """Get retention and archival statistics."""
    service = RetentionService(db)
    return service.get_retention_statistics()


@router.get("/retention/expired")
def get_expired_events(
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get events that have exceeded their retention period."""
    service = RetentionService(db)
    return service.get_expired_events(limit)


@router.post("/retention/archive")
def archive_expired_events(
    event_ids: List[int],
    archive_location: str,
    db: Session = Depends(get_db)
):
    """Archive events by marking them as archived."""
    service = RetentionService(db)
    count = service.archive_events(event_ids, archive_location)
    return {"archived_count": count, "archive_location": archive_location}
