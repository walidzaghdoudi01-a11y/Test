from abc import ABC, abstractmethod
from app.models.scan import ScanResult

class BasePublisher(ABC):
    @abstractmethod
    async def publish(self, result: ScanResult):
        pass

class ConsolePublisher(BasePublisher):
    async def publish(self, result: ScanResult):
        # In a real scenario, this would send to Kafka, SQS, etc.
        print(f"[{result.completed_at}] Published Scan {result.scan_id}: {len(result.findings)} findings found.")

# Singleton for simple usage
publisher = ConsolePublisher()
