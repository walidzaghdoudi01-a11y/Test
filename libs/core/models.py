"""Core domain models for threat intelligence."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SeverityLevel(str, Enum):
    """Threat severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IndicatorType(str, Enum):
    """Types of threat indicators."""

    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH = "file_hash"
    EMAIL = "email"
    CVE = "cve"
    MALWARE_FAMILY = "malware_family"
    OTHER = "other"


class AssetType(str, Enum):
    """Types of assets in the infrastructure."""

    SERVER = "server"
    WORKSTATION = "workstation"
    NETWORK_DEVICE = "network_device"
    APPLICATION = "application"
    DATABASE = "database"
    CONTAINER = "container"
    OTHER = "other"


class Asset(BaseModel):
    """Model representing an asset in the infrastructure."""

    model_config = ConfigDict(use_enum_values=False)

    id: str = Field(..., description="Unique identifier for the asset")
    name: str = Field(..., description="Human-readable name of the asset")
    asset_type: AssetType = Field(..., description="Type of the asset")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the asset"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when asset was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of last update"
    )


class Indicator(BaseModel):
    """Model representing a threat indicator."""

    model_config = ConfigDict(use_enum_values=False)

    id: str = Field(..., description="Unique identifier for the indicator")
    indicator_type: IndicatorType = Field(..., description="Type of the indicator")
    value: str = Field(..., description="The actual indicator value")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the indicator (0.0-1.0)",
    )
    source: str = Field(..., description="Source of the indicator")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the indicator"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when indicator was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of last update"
    )


class ThreatEvent(BaseModel):
    """Model representing a threat event or detection."""

    model_config = ConfigDict(use_enum_values=False)

    id: str = Field(..., description="Unique identifier for the threat event")
    title: str = Field(..., description="Title of the threat event")
    description: Optional[str] = Field(
        default=None, description="Detailed description of the threat"
    )
    severity: SeverityLevel = Field(..., description="Severity level of the threat")
    asset_ids: List[str] = Field(default_factory=list, description="List of affected asset IDs")
    indicator_ids: List[str] = Field(
        default_factory=list, description="List of related indicator IDs"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")
    detected_at: datetime = Field(..., description="Timestamp when threat was detected")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when event was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of last update"
    )
