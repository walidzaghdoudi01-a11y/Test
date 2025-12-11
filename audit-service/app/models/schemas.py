from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AuditEventBase(BaseModel):
    event_type: str = Field(..., description="Type of event: user_action, detection, scan, system_event")
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    source_service: Optional[str] = Field(None, description="Service that generated the event")
    source_host: Optional[str] = Field(None, description="Host that generated the event")
    source_ip: Optional[str] = Field(None, description="IP address of the source")
    user_id: Optional[str] = Field(None, description="User identifier")
    user_name: Optional[str] = Field(None, description="User name")
    action: Optional[str] = Field(None, description="Action performed")
    resource: Optional[str] = Field(None, description="Resource affected")
    resource_type: Optional[str] = Field(None, description="Type of resource")
    result: Optional[str] = Field(None, description="Result: success, failure, denied")
    detection_type: Optional[str] = Field(None, description="Type of detection")
    scan_id: Optional[str] = Field(None, description="Scan identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    retention_days: Optional[int] = Field(None, description="Retention period in days")


class AuditEventCreate(AuditEventBase):
    """Schema for creating audit events."""
    pass


class AuditEventResponse(AuditEventBase):
    """Schema for audit event responses."""
    id: int
    event_id: UUID
    timestamp: datetime
    previous_hash: Optional[str]
    event_hash: str
    signature: Optional[str]
    archived: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserActionEvent(BaseModel):
    """Specific schema for user action events."""
    user_id: str
    user_name: Optional[str] = None
    action: str
    resource: str
    resource_type: Optional[str] = None
    result: str = "success"
    source_service: Optional[str] = None
    source_ip: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    severity: str = "medium"


class DetectionEvent(BaseModel):
    """Specific schema for detection events."""
    detection_type: str
    severity: str
    source_service: str
    source_host: Optional[str] = None
    source_ip: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ScanEvent(BaseModel):
    """Specific schema for scan events."""
    scan_id: str
    scan_type: str
    result: str
    source_service: str
    resource: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    severity: str = "low"


class QueryParams(BaseModel):
    """Schema for querying audit events."""
    event_type: Optional[str] = None
    severity: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    detection_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    source_service: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(100, le=1000)
    offset: int = 0


class QueryResponse(BaseModel):
    """Schema for query responses."""
    total: int
    limit: int
    offset: int
    events: List[AuditEventResponse]


class RetentionPolicy(BaseModel):
    """Schema for retention policies."""
    event_type: str
    retention_days: int
    archive_enabled: bool
    archive_location: Optional[str] = None


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    database: str
    version: str
    timestamp: datetime
