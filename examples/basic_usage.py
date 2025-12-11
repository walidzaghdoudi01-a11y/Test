#!/usr/bin/env python3
"""
Basic usage examples for the audit logging client library.
"""

from audit_client import AuditClient
from datetime import datetime, timedelta

def main():
    # Initialize the client
    client = AuditClient(api_url="http://localhost:8000")
    
    # Check service health
    print("=== Health Check ===")
    health = client.health_check()
    print(f"Status: {health['status']}")
    print(f"Database: {health['database']}")
    print()
    
    # Log a user action event
    print("=== Logging User Action ===")
    user_event = client.log_user_action(
        user_id="user123",
        action="login",
        resource="web-app",
        result="success",
        user_name="John Doe",
        source_ip="192.168.1.100",
        metadata={
            "user_agent": "Mozilla/5.0...",
            "session_id": "abc-def-123"
        },
        tags=["authentication", "web"]
    )
    print(f"Created event: {user_event.event_id}")
    print(f"Event hash: {user_event.event_hash}")
    print()
    
    # Log a detection event
    print("=== Logging Detection ===")
    detection_event = client.log_detection(
        detection_type="malware",
        severity="high",
        source_service="antivirus-scanner",
        source_host="scanner-01",
        metadata={
            "file_path": "/tmp/suspicious.exe",
            "malware_family": "Trojan.Generic",
            "action_taken": "quarantined"
        },
        tags=["malware", "quarantine"]
    )
    print(f"Created detection: {detection_event.event_id}")
    print()
    
    # Log a scan event
    print("=== Logging Scan ===")
    scan_event = client.log_scan(
        scan_id="scan-20240101-001",
        scan_type="vulnerability",
        result="completed",
        source_service="vulnerability-scanner",
        resource="/app/production",
        metadata={
            "duration_seconds": 120,
            "vulnerabilities_found": 3,
            "severity_breakdown": {
                "high": 1,
                "medium": 2,
                "low": 0
            }
        },
        tags=["vulnerability", "production"]
    )
    print(f"Created scan: {scan_event.event_id}")
    print()
    
    # Query recent user actions
    print("=== Querying User Actions ===")
    recent_actions = client.query_events(
        event_type="user_action",
        limit=5
    )
    print(f"Total user actions: {recent_actions['total']}")
    print(f"Retrieved: {len(recent_actions['events'])} events")
    for event in recent_actions['events']:
        print(f"  - {event['user_id']} {event['action']} {event['resource']}")
    print()
    
    # Query high-severity events
    print("=== Querying High-Severity Events ===")
    high_severity = client.query_events(
        severity="high",
        limit=10
    )
    print(f"High-severity events: {high_severity['total']}")
    print()
    
    # Query events by time range
    print("=== Querying Recent Events (Last Hour) ===")
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    recent_events = client.query_events(
        start_time=one_hour_ago,
        limit=10
    )
    print(f"Events in last hour: {recent_events['total']}")
    print()
    
    # Verify integrity
    print("=== Verifying Chain Integrity ===")
    integrity = client.verify_integrity(limit=100)
    print(f"Status: {integrity['status']}")
    print(f"Verified: {integrity['verified']} events")
    print(f"Errors: {len(integrity['errors'])}")
    print()
    
    # Get specific event
    print("=== Retrieving Specific Event ===")
    event = client.get_event(user_event.event_id)
    print(f"Event ID: {event.event_id}")
    print(f"Type: {event.event_type}")
    print(f"Timestamp: {event.timestamp}")
    print(f"Hash: {event.event_hash}")
    print(f"Previous Hash: {event.previous_hash}")
    print()
    
    print("=== Example Complete ===")

if __name__ == "__main__":
    main()
