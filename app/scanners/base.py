from abc import ABC, abstractmethod
from app.models.scan import ScanResult, ScanRequest

class BaseScanner(ABC):
    @abstractmethod
    async def scan(self, request: ScanRequest, scan_id: str) -> ScanResult:
        pass
