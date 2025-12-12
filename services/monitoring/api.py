import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from services.monitoring.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    DashboardMetrics,
    DetectionEvent,
    HealthCheck,
)
from services.monitoring.processor import StreamingProcessor

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

streaming_processor: StreamingProcessor = None


def set_streaming_processor(processor: StreamingProcessor):
    """Set the streaming processor instance"""
    global streaming_processor
    streaming_processor = processor


@router.post("/events", status_code=202)
async def ingest_event(event: DetectionEvent):
    """
    Ingest a detection event for processing
    
    Events are queued and processed asynchronously
    """
    await streaming_processor.ingest_event(event)
    return {"status": "accepted", "event_id": event.event_id}


@router.post("/events/batch", status_code=202)
async def ingest_events_batch(events: List[DetectionEvent]):
    """
    Ingest multiple detection events
    
    Efficiently ingest a batch of events
    """
    for event in events:
        await streaming_processor.ingest_event(event)
    
    return {
        "status": "accepted",
        "count": len(events),
        "event_ids": [e.event_id for e in events],
    }


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    severity: Optional[AlertSeverity] = Query(default=None),
    status: Optional[AlertStatus] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    Get alerts with optional filters
    
    Filter by severity, status, and limit results
    """
    alerts = streaming_processor.get_alerts(severity=severity, status=status, limit=limit)
    return alerts


@router.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert(alert_id: str):
    """
    Get a specific alert by ID
    """
    alert = streaming_processor.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert


@router.patch("/alerts/{alert_id}/status")
async def update_alert_status(alert_id: str, status: AlertStatus):
    """
    Update alert status
    
    Status transitions: NEW -> ACKNOWLEDGED -> IN_PROGRESS -> RESOLVED -> CLOSED
    """
    success = await streaming_processor.update_alert_status(alert_id, status)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    return {"status": "success", "alert_id": alert_id, "new_status": status.value}


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """
    Get real-time dashboard metrics
    
    Returns aggregated metrics for monitoring dashboards
    """
    return streaming_processor.get_dashboard_metrics()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint
    
    Returns health status of monitoring components
    """
    uptime = time.time() - streaming_processor.start_time
    
    components = {
        "streaming_processor": {
            "status": "healthy" if streaming_processor.running else "unhealthy",
            "queue_size": str(streaming_processor.event_queue.qsize()),
        },
        "notification_manager": {
            "status": "healthy",
            "channels": str(len(streaming_processor.notification_manager.notifiers)),
        },
    }
    
    overall_status = "healthy" if all(
        c["status"] == "healthy" for c in components.values()
    ) else "unhealthy"
    
    return HealthCheck(
        status=overall_status,
        components=components,
        uptime_seconds=uptime,
    )


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Exposes metrics for Prometheus scraping
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
