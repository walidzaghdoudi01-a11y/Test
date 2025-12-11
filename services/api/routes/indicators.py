"""Indicator management endpoints."""

from typing import List

from fastapi import APIRouter

from libs.core.models import Indicator

router = APIRouter(prefix="/indicators")


@router.get("", response_model=List[Indicator])
async def list_indicators() -> List[Indicator]:
    """List all indicators."""
    return []


@router.post("", response_model=Indicator, status_code=201)
async def create_indicator(indicator: Indicator) -> Indicator:
    """Create a new indicator."""
    return indicator


@router.get("/{indicator_id}", response_model=Indicator)
async def get_indicator(indicator_id: str) -> Indicator:
    """Get an indicator by ID."""
    raise NotImplementedError


@router.put("/{indicator_id}", response_model=Indicator)
async def update_indicator(indicator_id: str, indicator: Indicator) -> Indicator:
    """Update an indicator."""
    raise NotImplementedError


@router.delete("/{indicator_id}", status_code=204)
async def delete_indicator(indicator_id: str) -> None:
    """Delete an indicator."""
    raise NotImplementedError
