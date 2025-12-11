"""Asset management endpoints."""

from typing import List

from fastapi import APIRouter

from libs.core.models import Asset

router = APIRouter(prefix="/assets")


@router.get("", response_model=List[Asset])
async def list_assets() -> List[Asset]:
    """List all assets."""
    return []


@router.post("", response_model=Asset, status_code=201)
async def create_asset(asset: Asset) -> Asset:
    """Create a new asset."""
    return asset


@router.get("/{asset_id}", response_model=Asset)
async def get_asset(asset_id: str) -> Asset:
    """Get an asset by ID."""
    raise NotImplementedError


@router.put("/{asset_id}", response_model=Asset)
async def update_asset(asset_id: str, asset: Asset) -> Asset:
    """Update an asset."""
    raise NotImplementedError


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(asset_id: str) -> None:
    """Delete an asset."""
    raise NotImplementedError
