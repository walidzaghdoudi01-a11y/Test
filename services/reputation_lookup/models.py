from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ReputationScore(str, Enum):
    """Reputation score categories"""
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    UNKNOWN = "unknown"


class ThreatCategory(str, Enum):
    """Threat category types"""
    MALWARE = "malware"
    PHISHING = "phishing"
    BOTNET = "botnet"
    SPAM = "spam"
    C2 = "command_and_control"
    SCANNING = "scanning"
    DGA = "domain_generation_algorithm"
    CRYPTOCURRENCY = "cryptocurrency"
    OTHER = "other"


class ReputationSource(BaseModel):
    """External reputation feed source"""
    name: str = Field(description="Name of the reputation source")
    score: ReputationScore = Field(description="Reputation score from this source")
    categories: List[ThreatCategory] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    last_seen: Optional[datetime] = Field(default=None)
    metadata: Dict[str, str] = Field(default_factory=dict)


class IPReputationResponse(BaseModel):
    """IP address reputation lookup response"""
    ip_address: str = Field(description="IP address queried")
    overall_score: ReputationScore = Field(description="Aggregated reputation score")
    risk_score: float = Field(ge=0.0, le=100.0, description="Risk score 0-100")
    sources: List[ReputationSource] = Field(description="Individual source results")
    categories: List[ThreatCategory] = Field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    cached: bool = Field(default=False, description="Whether result is from cache")
    queried_at: datetime = Field(default_factory=datetime.utcnow)


class DomainReputationResponse(BaseModel):
    """Domain reputation lookup response"""
    domain: str = Field(description="Domain queried")
    overall_score: ReputationScore = Field(description="Aggregated reputation score")
    risk_score: float = Field(ge=0.0, le=100.0, description="Risk score 0-100")
    sources: List[ReputationSource] = Field(description="Individual source results")
    categories: List[ThreatCategory] = Field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    whois_info: Optional[Dict[str, str]] = None
    dns_records: Optional[Dict[str, List[str]]] = None
    cached: bool = Field(default=False, description="Whether result is from cache")
    queried_at: datetime = Field(default_factory=datetime.utcnow)


class BulkLookupRequest(BaseModel):
    """Bulk lookup request"""
    indicators: List[str] = Field(description="List of IPs or domains to lookup")
    max_age_seconds: Optional[int] = Field(
        default=3600, description="Max age of cached results in seconds"
    )


class BulkLookupResponse(BaseModel):
    """Bulk lookup response"""
    results: Dict[str, IPReputationResponse | DomainReputationResponse]
    total: int
    successful: int
    failed: int
    cached_count: int
