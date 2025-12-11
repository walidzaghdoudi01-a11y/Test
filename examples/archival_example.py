#!/usr/bin/env python3
"""
Example of archival and retention management.
"""

import json
from audit_client import AuditClient
from datetime import datetime

def main():
    client = AuditClient(api_url="http://localhost:8000")
    
    print("=== Retention Management Example ===\n")
    
    # Get retention statistics
    print("1. Getting retention statistics...")
    stats_response = client._make_request("GET", "/api/v1/retention/statistics")
    print(f"Total events: {stats_response['total_events']}")
    print(f"Active events: {stats_response['active_events']}")
    print(f"Archived events: {stats_response['archived_events']}")
    print(f"Expired events: {stats_response['expired_events']}")
    print()
    
    # Get retention policy for user actions
    print("2. Checking retention policy for user_action events...")
    policy_response = client._make_request(
        "GET", 
        "/api/v1/retention/policies/user_action"
    )
    print(f"Retention days: {policy_response['retention_days']}")
    print(f"Archive enabled: {policy_response['archive_enabled']}")
    print()
    
    # Update retention policy for custom events
    print("3. Creating custom retention policy...")
    custom_policy = {
        "event_type": "custom_event",
        "retention_days": 365,
        "archive_enabled": True,
        "archive_location": "s3://my-bucket/audit-archive"
    }
    updated_policy = client._make_request(
        "PUT",
        "/api/v1/retention/policies/custom_event",
        data=custom_policy
    )
    print(f"Created policy for {updated_policy['event_type']}")
    print(f"Retention: {updated_policy['retention_days']} days")
    print()
    
    # Get expired events (events past retention period)
    print("4. Checking for expired events...")
    expired_response = client._make_request(
        "GET",
        "/api/v1/retention/expired",
        params={"limit": 10}
    )
    print(f"Found {len(expired_response)} expired events ready for archival")
    print()
    
    # Archive expired events (example)
    if expired_response:
        print("5. Archiving expired events...")
        event_ids = [event['id'] for event in expired_response[:5]]  # Archive first 5
        
        archive_response = client._make_request(
            "POST",
            "/api/v1/retention/archive",
            data={
                "event_ids": event_ids,
                "archive_location": f"s3://audit-archive/{datetime.now().date()}.json"
            }
        )
        print(f"Archived {archive_response['archived_count']} events")
        print(f"Location: {archive_response['archive_location']}")
        print()
    
    # Get updated statistics
    print("6. Getting updated statistics...")
    updated_stats = client._make_request("GET", "/api/v1/retention/statistics")
    print(f"Total events: {updated_stats['total_events']}")
    print(f"Active events: {updated_stats['active_events']}")
    print(f"Archived events: {updated_stats['archived_events']}")
    print()
    
    print("=== Archival Example Complete ===")

if __name__ == "__main__":
    main()
