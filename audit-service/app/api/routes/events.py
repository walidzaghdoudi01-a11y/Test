from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import (
    AuditEventCreate, 
    AuditEventResponse,
    DetectionEvent,
    ScanEvent,
    UserActionEvent
)
from app.services.audit_service import AuditService

router = APIRouter()


@router.post("/events", response_model=AuditEventResponse, status_code=status.HTTP_201_CREATED)
def create_audit_event(
    event: AuditEventCreate,
    db: Session = Depends(get_db)
):
    """Create a new audit event."""
    service = AuditService(db)
    result = service.create_event(event)
    
    full_event = service.get_event_by_id(result["event_id"])
    return AuditEventResponse(**full_event)


@router.post("/events/user-action", response_model=AuditEventResponse, status_code=status.HTTP_201_CREATED)
def create_user_action_event(
    event: UserActionEvent,
    db: Session = Depends(get_db)
):
    """Create a user action audit event."""
    audit_event = AuditEventCreate(
        event_type="user_action",
        severity=event.severity,
        source_service=event.source_service,
        source_ip=event.source_ip,
        user_id=event.user_id,
        user_name=event.user_name,
        action=event.action,
        resource=event.resource,
        resource_type=event.resource_type,
        result=event.result,
        metadata=event.metadata,
        tags=event.tags,
    )
    
    service = AuditService(db)
    result = service.create_event(audit_event)
    
    full_event = service.get_event_by_id(result["event_id"])
    return AuditEventResponse(**full_event)


@router.post("/events/detection", response_model=AuditEventResponse, status_code=status.HTTP_201_CREATED)
def create_detection_event(
    event: DetectionEvent,
    db: Session = Depends(get_db)
):
    """Create a detection audit event."""
    audit_event = AuditEventCreate(
        event_type="detection",
        severity=event.severity,
        source_service=event.source_service,
        source_host=event.source_host,
        source_ip=event.source_ip,
        detection_type=event.detection_type,
        metadata=event.metadata,
        tags=event.tags,
    )
    
    service = AuditService(db)
    result = service.create_event(audit_event)
    
    full_event = service.get_event_by_id(result["event_id"])
    return AuditEventResponse(**full_event)


@router.post("/events/scan", response_model=AuditEventResponse, status_code=status.HTTP_201_CREATED)
def create_scan_event(
    event: ScanEvent,
    db: Session = Depends(get_db)
):
    """Create a scan audit event."""
    audit_event = AuditEventCreate(
        event_type="scan",
        severity=event.severity,
        source_service=event.source_service,
        scan_id=event.scan_id,
        resource=event.resource,
        result=event.result,
        metadata=event.metadata,
        tags=event.tags,
    )
    
    service = AuditService(db)
    result = service.create_event(audit_event)
    
    full_event = service.get_event_by_id(result["event_id"])
    return AuditEventResponse(**full_event)


@router.get("/events/{event_id}", response_model=AuditEventResponse)
def get_event(
    event_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific audit event by ID."""
    service = AuditService(db)
    event = service.get_event_by_id(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    
    return AuditEventResponse(**event)


@router.get("/events/verify/integrity")
def verify_integrity(
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """Verify hash chain integrity of audit events."""
    service = AuditService(db)
    result = service.verify_chain_integrity(limit)
    return result
