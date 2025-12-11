"""Threat event management endpoints."""

from typing import List

from fastapi import APIRouter

from libs.core.models import ThreatEvent

router = APIRouter(prefix="/events")


@router.get("", response_model=List[ThreatEvent])
async def list_events() -> List[ThreatEvent]:
    """List all threat events."""
    return []


@router.post("", response_model=ThreatEvent, status_code=201)
async def create_event(event: ThreatEvent) -> ThreatEvent:
    """Create a new threat event."""
    return event


@router.get("/{event_id}", response_model=ThreatEvent)
async def get_event(event_id: str) -> ThreatEvent:
    """Get a threat event by ID."""
    raise NotImplementedError


@router.put("/{event_id}", response_model=ThreatEvent)
async def update_event(event_id: str, event: ThreatEvent) -> ThreatEvent:
    """Update a threat event."""
    raise NotImplementedError


@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: str) -> None:
    """Delete a threat event."""
    raise NotImplementedError
