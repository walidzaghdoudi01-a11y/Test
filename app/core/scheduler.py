from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.scan_service import scan_service
from app.models.scan import ScanRequest, ScanType
import asyncio

class ScanScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown()

    def add_scheduled_scan(self, request: ScanRequest, interval_seconds: int):
        # We need to wrap the async call
        def job_function():
            asyncio.create_task(scan_service.start_scan(request))

        job_id = self.scheduler.add_job(
            job_function,
            IntervalTrigger(seconds=interval_seconds),
            id=f"{request.scan_type}-{request.target}",
            replace_existing=True
        ).id
        return job_id

scheduler = ScanScheduler()
