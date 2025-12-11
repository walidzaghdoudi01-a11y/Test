from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserActionEvent(BaseModel):
    """Model for user action events."""
    user_id: str
    action: str
    resource: str
    result: str = "success"
    user_name: Optional[str] = None
    resource_type: Optional[str] = None
    source_service: Optional[str] = None
    source_ip: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    severity: str = "medium"


class DetectionEvent(BaseModel):
    """Model for detection events."""
    detection_type: str
    severity: str
    source_service: str
    source_host: Optional[str] = None
    source_ip: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ScanEvent(BaseModel):
    """Model for scan events."""
    scan_id: str
    scan_type: str
    result: str
    source_service: str
    resource: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    severity: str = "low"


class AuditEvent(BaseModel):
    """Generic audit event model."""
    event_type: str
    severity: str
    source_service: Optional[str] = None
    source_host: Optional[str] = None
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    resource_type: Optional[str] = None
    result: Optional[str] = None
    detection_type: Optional[str] = None
    scan_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    retention_days: Optional[int] = None


class AuditEventResponse(BaseModel):
    """Response model for audit events."""
    id: int
    event_id: UUID
    timestamp: datetime
    event_type: str
    severity: str
    event_hash: str
    previous_hash: Optional[str]
    archived: bool
    created_at: datetime


class QueryParams(BaseModel):
    """Parameters for querying audit events."""
    event_type: Optional[str] = None
    severity: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    detection_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    source_service: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0
