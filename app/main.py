from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import List
from contextlib import asynccontextmanager
from app.models.scan import ScanRequest, ScanResult, ScanType
from app.services.scan_service import scan_service
from app.core.scheduler import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(title="Security Scanning Service", lifespan=lifespan)

@app.post("/scans", response_model=ScanResult, status_code=202)
async def trigger_scan(request: ScanRequest):
    """
    Trigger an on-demand scan.
    """
    return await scan_service.start_scan(request)

@app.get("/scans/{scan_id}", response_model=ScanResult)
async def get_scan_status(scan_id: str):
    """
    Get the status and results of a scan.
    """
    result = scan_service.get_scan(scan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scan not found")
    return result

@app.get("/scans", response_model=List[ScanResult])
async def list_scans():
    """
    List all scans.
    """
    return scan_service.list_scans()

@app.post("/schedules")
async def schedule_scan(request: ScanRequest, interval_seconds: int = 3600):
    """
    Schedule a periodic scan.
    """
    job_id = scheduler.add_scheduled_scan(request, interval_seconds)
    return {"message": "Scan scheduled", "job_id": job_id, "interval_seconds": interval_seconds}

@app.get("/")
async def root():
    return {"message": "Security Scanning Service Operational"}
