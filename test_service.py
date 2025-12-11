#!/usr/bin/env python
"""Quick test to verify the service can start and respond to requests"""
import asyncio
import sys

import httpx


async def test_service():
    """Test the service"""
    base_url = "http://localhost:8000"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Test health
            response = await client.get(f"{base_url}/health")
            print(f"Health check: {response.status_code} - {response.json()}")
            
            # Test monitoring health
            response = await client.get(f"{base_url}/api/v1/monitoring/health")
            print(f"Monitoring health: {response.status_code}")
            
            # Test reputation lookup (will work if Redis is available)
            response = await client.get(f"{base_url}/api/v1/reputation/ip/192.168.1.100")
            print(f"Reputation lookup: {response.status_code}")
            
            # Test event ingestion
            event = {
                "event_id": "test-1",
                "source": "test",
                "severity": "high",
                "title": "Test Event",
                "description": "Test",
                "indicators": [],
                "affected_assets": [],
            }
            response = await client.post(f"{base_url}/api/v1/monitoring/events", json=event)
            print(f"Event ingestion: {response.status_code} - {response.json()}")
            
            print("\n✅ Service is running correctly!")
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the service is running: python main.py")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_service())
    sys.exit(0 if result else 1)
