import asyncio
from typing import List
from datetime import datetime
from app.scanners.base import BaseScanner
from app.models.scan import ScanRequest, ScanResult, ScanStatus, Finding, Severity, ScanType

class DependencyScanner(BaseScanner):
    async def scan(self, request: ScanRequest, scan_id: str) -> ScanResult:
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Mocked logic: check if target contains "vulnerable"
        findings = []
        if "vulnerable" in request.target:
            findings.append(Finding(
                title="Critical CVE-2023-1234",
                description="Remote Code Execution vulnerability in library X",
                severity=Severity.CRITICAL,
                location="package-lock.json: lib-x@1.0.0",
                metadata={"cve": "CVE-2023-1234", "cvss": 9.8}
            ))
        
        return ScanResult(
            scan_id=scan_id,
            scan_type=ScanType.DEPENDENCY,
            target=request.target,
            status=ScanStatus.COMPLETED,
            findings=findings,
            completed_at=datetime.utcnow()
        )

class ContainerScanner(BaseScanner):
    async def scan(self, request: ScanRequest, scan_id: str) -> ScanResult:
        await asyncio.sleep(2)
        
        findings = []
        if "old" in request.target:
            findings.append(Finding(
                title="Outdated Base Image",
                description="The base image alpine:3.10 is end of life",
                severity=Severity.HIGH,
                location="Dockerfile: FROM alpine:3.10",
                metadata={"base_image": "alpine:3.10"}
            ))
            
        return ScanResult(
            scan_id=scan_id,
            scan_type=ScanType.CONTAINER,
            target=request.target,
            status=ScanStatus.COMPLETED,
            findings=findings,
            completed_at=datetime.utcnow()
        )

class MalwareScanner(BaseScanner):
    async def scan(self, request: ScanRequest, scan_id: str) -> ScanResult:
        await asyncio.sleep(1)
        
        findings = []
        # specific hash for testing
        if request.target == "eicar.com" or "malware" in request.target:
            findings.append(Finding(
                title="EICAR Test File",
                description="EICAR Standard Anti-Virus Test File detected",
                severity=Severity.CRITICAL,
                location="/tmp/uploaded_file",
                metadata={"signature": "EICAR-Test-Signature"}
            ))

        return ScanResult(
            scan_id=scan_id,
            scan_type=ScanType.MALWARE,
            target=request.target,
            status=ScanStatus.COMPLETED,
            findings=findings,
            completed_at=datetime.utcnow()
        )

class ConfigurationScanner(BaseScanner):
    async def scan(self, request: ScanRequest, scan_id: str) -> ScanResult:
        await asyncio.sleep(1)
        
        findings = []
        if "public" in request.target:
             findings.append(Finding(
                title="Public S3 Bucket",
                description="S3 bucket is configured to allow public read access",
                severity=Severity.HIGH,
                location="aws_s3_bucket.example",
                metadata={"compliance": "CIS-AWS-1.2"}
            ))
            
        return ScanResult(
            scan_id=scan_id,
            scan_type=ScanType.CONFIGURATION,
            target=request.target,
            status=ScanStatus.COMPLETED,
            findings=findings,
            completed_at=datetime.utcnow()
        )
