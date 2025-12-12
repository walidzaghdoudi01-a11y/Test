from typing import Dict, Union

from fastapi import APIRouter, HTTPException, Query
from prometheus_client import Counter, Histogram

from services.reputation_lookup.models import (
    BulkLookupRequest,
    BulkLookupResponse,
    DomainReputationResponse,
    IPReputationResponse,
)
from services.reputation_lookup.service import ReputationLookupService

router = APIRouter(prefix="/api/v1/reputation", tags=["reputation"])

lookup_counter = Counter(
    "reputation_lookups_total",
    "Total number of reputation lookups",
    ["indicator_type", "cached"],
)
lookup_duration = Histogram(
    "reputation_lookup_duration_seconds",
    "Duration of reputation lookups",
    ["indicator_type"],
)

reputation_service: ReputationLookupService = None


def set_reputation_service(service: ReputationLookupService):
    """Set the reputation service instance"""
    global reputation_service
    reputation_service = service


@router.get("/ip/{ip_address}", response_model=IPReputationResponse)
async def lookup_ip(
    ip_address: str,
    use_cache: bool = Query(default=True, description="Use cached results if available"),
):
    """
    Lookup IP address reputation
    
    Returns reputation information from multiple threat intelligence feeds
    """
    if reputation_service is None:
        raise HTTPException(status_code=503, detail="Reputation service not initialized")
    
    try:
        with lookup_duration.labels(indicator_type="ip").time():
            result = await reputation_service.lookup_ip(ip_address, use_cache=use_cache)
        
        lookup_counter.labels(
            indicator_type="ip", 
            cached=str(result.cached)
        ).inc()
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/domain/{domain}", response_model=DomainReputationResponse)
async def lookup_domain(
    domain: str,
    use_cache: bool = Query(default=True, description="Use cached results if available"),
):
    """
    Lookup domain reputation
    
    Returns reputation information from multiple threat intelligence feeds
    """
    if reputation_service is None:
        raise HTTPException(status_code=503, detail="Reputation service not initialized")
    
    try:
        with lookup_duration.labels(indicator_type="domain").time():
            result = await reputation_service.lookup_domain(domain, use_cache=use_cache)
        
        lookup_counter.labels(
            indicator_type="domain", 
            cached=str(result.cached)
        ).inc()
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/bulk", response_model=BulkLookupResponse)
async def bulk_lookup(request: BulkLookupRequest):
    """
    Bulk lookup of multiple IPs or domains
    
    Efficiently lookup reputation for multiple indicators
    """
    results: Dict[str, Union[IPReputationResponse, DomainReputationResponse]] = {}
    successful = 0
    failed = 0
    cached_count = 0

    for indicator in request.indicators:
        try:
            if "." in indicator and indicator.replace(".", "").isdigit():
                result = await reputation_service.lookup_ip(indicator, use_cache=True)
            else:
                result = await reputation_service.lookup_domain(indicator, use_cache=True)
            
            results[indicator] = result
            successful += 1
            if result.cached:
                cached_count += 1
                
        except Exception:
            failed += 1
            continue

    return BulkLookupResponse(
        results=results,
        total=len(request.indicators),
        successful=successful,
        failed=failed,
        cached_count=cached_count,
    )


@router.post("/cache/invalidate/{indicator}")
async def invalidate_cache(indicator: str):
    """
    Invalidate cached reputation for an indicator
    
    Forces fresh lookup on next request
    """
    if reputation_service.cache:
        await reputation_service.cache.invalidate(indicator)
        return {"status": "success", "message": f"Cache invalidated for {indicator}"}
    else:
        raise HTTPException(status_code=503, detail="Cache not available")


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics
    
    Returns hit/miss rates and other cache metrics
    """
    if reputation_service.cache:
        stats = await reputation_service.cache.get_stats()
        return stats
    else:
        raise HTTPException(status_code=503, detail="Cache not available")
