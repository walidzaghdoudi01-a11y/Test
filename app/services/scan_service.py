import uuid
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from app.models.scan import ScanRequest, ScanResult, ScanStatus, ScanType, Finding
from app.scanners.base import BaseScanner
from app.scanners.implementations import DependencyScanner, ContainerScanner, MalwareScanner, ConfigurationScanner
from app.core.publisher import publisher

class ScanService:
    def __init__(self):
        self._scans: Dict[str, ScanResult] = {}
        self._scanners: Dict[ScanType, BaseScanner] = {
            ScanType.DEPENDENCY: DependencyScanner(),
            ScanType.CONTAINER: ContainerScanner(),
            ScanType.MALWARE: MalwareScanner(),
            ScanType.CONFIGURATION: ConfigurationScanner(),
        }

    async def start_scan(self, request: ScanRequest) -> ScanResult:
        scan_id = str(uuid.uuid4())
        initial_result = ScanResult(
            scan_id=scan_id,
            scan_type=request.scan_type,
            target=request.target,
            status=ScanStatus.PENDING,
            created_at=datetime.utcnow()
        )
        self._scans[scan_id] = initial_result
        
        # Fire and forget (or await if we want synchronous for API, but background is better)
        # For this implementation, I will run it in the background using asyncio.create_task
        asyncio.create_task(self._run_scan(request, scan_id))
        
        return initial_result

    async def _run_scan(self, request: ScanRequest, scan_id: str):
        self._scans[scan_id].status = ScanStatus.RUNNING
        scanner = self._scanners.get(request.scan_type)
        
        if not scanner:
            self._scans[scan_id].status = ScanStatus.FAILED
            self._scans[scan_id].error = f"No scanner found for type {request.scan_type}"
            self._scans[scan_id].completed_at = datetime.utcnow()
            return

        try:
            result = await scanner.scan(request, scan_id)
            self._scans[scan_id] = result
            # Publish to shared datastore/queue
            await publisher.publish(result)
        except Exception as e:
            self._scans[scan_id].status = ScanStatus.FAILED
            self._scans[scan_id].error = str(e)
            self._scans[scan_id].completed_at = datetime.utcnow()

    def get_scan(self, scan_id: str) -> Optional[ScanResult]:
        return self._scans.get(scan_id)

    def list_scans(self) -> List[ScanResult]:
        return list(self._scans.values())

# Singleton instance
scan_service = ScanService()
