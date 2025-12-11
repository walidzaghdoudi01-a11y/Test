from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from .models import (
    AuditEvent,
    AuditEventResponse,
    DetectionEvent,
    QueryParams,
    ScanEvent,
    UserActionEvent,
)


class AuditClientError(Exception):
    """Base exception for audit client errors."""
    pass


class AuditClient:
    """Client library for interacting with the audit logging service."""
    
    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        api_key: Optional[str] = None
    ):
        """
        Initialize the audit client.
        
        Args:
            api_url: Base URL of the audit service API
            timeout: Request timeout in seconds
            api_key: Optional API key for authentication
        """
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to the audit service."""
        url = f"{self.api_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise AuditClientError(f"Request failed: {str(e)}")
    
    def log_event(self, event: AuditEvent) -> AuditEventResponse:
        """
        Log a generic audit event.
        
        Args:
            event: AuditEvent instance
            
        Returns:
            AuditEventResponse with created event details
        """
        data = event.model_dump(exclude_none=True)
        result = self._make_request("POST", "/api/v1/events", data=data)
        return AuditEventResponse(**result)
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str = "success",
        **kwargs
    ) -> AuditEventResponse:
        """
        Log a user action event.
        
        Args:
            user_id: User identifier
            action: Action performed (e.g., login, create, delete)
            resource: Resource affected
            result: Result of the action (success, failure, denied)
            **kwargs: Additional fields (user_name, source_service, metadata, etc.)
            
        Returns:
            AuditEventResponse with created event details
        """
        event = UserActionEvent(
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            **kwargs
        )
        data = event.model_dump(exclude_none=True)
        result = self._make_request("POST", "/api/v1/events/user-action", data=data)
        return AuditEventResponse(**result)
    
    def log_detection(
        self,
        detection_type: str,
        severity: str,
        source_service: str,
        **kwargs
    ) -> AuditEventResponse:
        """
        Log a detection event.
        
        Args:
            detection_type: Type of detection (e.g., malware, intrusion)
            severity: Severity level (low, medium, high, critical)
            source_service: Service that detected the event
            **kwargs: Additional fields (source_host, metadata, tags, etc.)
            
        Returns:
            AuditEventResponse with created event details
        """
        event = DetectionEvent(
            detection_type=detection_type,
            severity=severity,
            source_service=source_service,
            **kwargs
        )
        data = event.model_dump(exclude_none=True)
        result = self._make_request("POST", "/api/v1/events/detection", data=data)
        return AuditEventResponse(**result)
    
    def log_scan(
        self,
        scan_id: str,
        scan_type: str,
        result: str,
        source_service: str,
        **kwargs
    ) -> AuditEventResponse:
        """
        Log a scan event.
        
        Args:
            scan_id: Unique scan identifier
            scan_type: Type of scan
            result: Scan result
            source_service: Service that performed the scan
            **kwargs: Additional fields (resource, metadata, tags, etc.)
            
        Returns:
            AuditEventResponse with created event details
        """
        event = ScanEvent(
            scan_id=scan_id,
            scan_type=scan_type,
            result=result,
            source_service=source_service,
            **kwargs
        )
        data = event.model_dump(exclude_none=True)
        result = self._make_request("POST", "/api/v1/events/scan", data=data)
        return AuditEventResponse(**result)
    
    def get_event(self, event_id: UUID) -> AuditEventResponse:
        """
        Get a specific audit event by ID.
        
        Args:
            event_id: UUID of the event
            
        Returns:
            AuditEventResponse with event details
        """
        result = self._make_request("GET", f"/api/v1/events/{event_id}")
        return AuditEventResponse(**result)
    
    def query_events(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        detection_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        source_service: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Query audit events with filters.
        
        Args:
            event_type: Filter by event type
            severity: Filter by severity
            user_id: Filter by user ID
            action: Filter by action
            detection_type: Filter by detection type
            start_time: Filter by start time (ISO format)
            end_time: Filter by end time (ISO format)
            source_service: Filter by source service
            tags: Filter by tags
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Dictionary with total count and list of events
        """
        params = {
            k: v for k, v in {
                "event_type": event_type,
                "severity": severity,
                "user_id": user_id,
                "action": action,
                "detection_type": detection_type,
                "start_time": start_time,
                "end_time": end_time,
                "source_service": source_service,
                "limit": limit,
                "offset": offset,
            }.items() if v is not None
        }
        
        if tags:
            params["tags"] = tags
        
        return self._make_request("GET", "/api/v1/query", params=params)
    
    def verify_integrity(self, limit: int = 1000) -> Dict[str, Any]:
        """
        Verify the integrity of the audit log hash chain.
        
        Args:
            limit: Number of recent events to verify
            
        Returns:
            Dictionary with verification status and any errors
        """
        return self._make_request(
            "GET",
            "/api/v1/events/verify/integrity",
            params={"limit": limit}
        )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the audit service.
        
        Returns:
            Dictionary with service health status
        """
        return self._make_request("GET", "/health")
