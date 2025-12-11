import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.scan import ScanType, ScanStatus

@pytest.mark.asyncio
async def test_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Security Scanning Service Operational"}

@pytest.mark.asyncio
async def test_trigger_scan():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "scan_type": "dependency",
            "target": "vulnerable-project"
        }
        response = await ac.post("/scans", json=payload)
    
    assert response.status_code == 202
    data = response.json()
    assert data["scan_type"] == "dependency"
    assert data["target"] == "vulnerable-project"
    assert data["status"] == "pending"
    assert "scan_id" in data

@pytest.mark.asyncio
async def test_scan_execution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "scan_type": "dependency",
            "target": "vulnerable-project"
        }
        response = await ac.post("/scans", json=payload)
        scan_id = response.json()["scan_id"]
        
        # Wait for scan to complete (mock scanner waits 1s)
        import asyncio
        await asyncio.sleep(1.5)
        
        response = await ac.get(f"/scans/{scan_id}")
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["findings"]) > 0
        assert data["findings"][0]["severity"] == "critical"

@pytest.mark.asyncio
async def test_malware_scan():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "scan_type": "malware",
            "target": "eicar.com"
        }
        response = await ac.post("/scans", json=payload)
        scan_id = response.json()["scan_id"]
        
        import asyncio
        await asyncio.sleep(1.5)
        
        response = await ac.get(f"/scans/{scan_id}")
        data = response.json()
        assert data["status"] == "completed"
        assert data["findings"][0]["title"] == "EICAR Test File"

@pytest.mark.asyncio
async def test_schedule_scan():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "request": {
                "scan_type": "configuration",
                "target": "public-bucket"
            },
            "interval_seconds": 1
        }
        
        response = await ac.post("/schedules?interval_seconds=1", json=payload["request"])
        assert response.status_code == 200
        assert "job_id" in response.json()
