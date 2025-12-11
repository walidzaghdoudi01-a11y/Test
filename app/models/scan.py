from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class ScanType(str, Enum):
    DEPENDENCY = "dependency"
    CONTAINER = "container"
    MALWARE = "malware"
    CONFIGURATION = "configuration"

class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    severity: Severity
    location: str
    metadata: Dict[str, Any] = {}

class ScanRequest(BaseModel):
    scan_type: ScanType
    target: str
    parameters: Dict[str, Any] = {}

class ScanResult(BaseModel):
    scan_id: str
    scan_type: ScanType
    target: str
    status: ScanStatus
    findings: List[Finding] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
