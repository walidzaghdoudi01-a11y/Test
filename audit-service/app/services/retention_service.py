from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session


class RetentionService:
    """Service for managing retention and archival policies."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_retention_policy(self, event_type: str) -> Dict[str, any]:
        """Get retention policy for an event type."""
        query = text("""
            SELECT event_type, retention_days, archive_enabled, archive_location
            FROM retention_policies
            WHERE event_type = :event_type
        """)
        
        result = self.db.execute(query, {"event_type": event_type}).fetchone()
        
        if not result:
            result = self.db.execute(
                query, {"event_type": "default"}
            ).fetchone()
        
        return {
            "event_type": result[0],
            "retention_days": result[1],
            "archive_enabled": result[2],
            "archive_location": result[3],
        }
    
    def update_retention_policy(
        self, 
        event_type: str, 
        retention_days: int, 
        archive_enabled: bool = True,
        archive_location: str = None
    ) -> Dict[str, any]:
        """Update or create retention policy."""
        query = text("""
            INSERT INTO retention_policies 
            (event_type, retention_days, archive_enabled, archive_location, updated_at)
            VALUES (:event_type, :retention_days, :archive_enabled, :archive_location, CURRENT_TIMESTAMP)
            ON CONFLICT (event_type) 
            DO UPDATE SET 
                retention_days = :retention_days,
                archive_enabled = :archive_enabled,
                archive_location = :archive_location,
                updated_at = CURRENT_TIMESTAMP
            RETURNING event_type, retention_days, archive_enabled, archive_location
        """)
        
        result = self.db.execute(
            query,
            {
                "event_type": event_type,
                "retention_days": retention_days,
                "archive_enabled": archive_enabled,
                "archive_location": archive_location,
            }
        ).fetchone()
        
        self.db.commit()
        
        return {
            "event_type": result[0],
            "retention_days": result[1],
            "archive_enabled": result[2],
            "archive_location": result[3],
        }
    
    def get_expired_events(self, limit: int = 1000) -> List[Dict[str, any]]:
        """Get events that have exceeded their retention period."""
        query = text("""
            SELECT id, event_id, event_type, timestamp, retention_days
            FROM audit_events
            WHERE NOT archived
            AND timestamp < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL
            ORDER BY timestamp ASC
            LIMIT :limit
        """)
        
        results = self.db.execute(query, {"limit": limit}).fetchall()
        
        return [
            {
                "id": row[0],
                "event_id": row[1],
                "event_type": row[2],
                "timestamp": row[3],
                "retention_days": row[4],
            }
            for row in results
        ]
    
    def archive_events(self, event_ids: List[int], archive_location: str) -> int:
        """Mark events as archived."""
        if not event_ids:
            return 0
        
        query = text("""
            UPDATE audit_events
            SET archived = TRUE, archive_location = :archive_location
            WHERE id = ANY(:event_ids)
            AND NOT archived
        """)
        
        result = self.db.execute(
            query,
            {
                "event_ids": event_ids,
                "archive_location": archive_location,
            }
        )
        
        self.db.commit()
        
        return result.rowcount
    
    def get_retention_statistics(self) -> Dict[str, any]:
        """Get statistics about retention and archival."""
        stats_query = text("""
            SELECT 
                COUNT(*) as total_events,
                COUNT(*) FILTER (WHERE archived) as archived_events,
                COUNT(*) FILTER (WHERE NOT archived) as active_events,
                COUNT(*) FILTER (
                    WHERE NOT archived 
                    AND timestamp < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL
                ) as expired_events,
                MIN(timestamp) as oldest_event,
                MAX(timestamp) as newest_event
            FROM audit_events
        """)
        
        result = self.db.execute(stats_query).fetchone()
        
        type_stats_query = text("""
            SELECT 
                event_type,
                COUNT(*) as count,
                COUNT(*) FILTER (WHERE archived) as archived_count
            FROM audit_events
            GROUP BY event_type
        """)
        
        type_results = self.db.execute(type_stats_query).fetchall()
        
        return {
            "total_events": result[0],
            "archived_events": result[1],
            "active_events": result[2],
            "expired_events": result[3],
            "oldest_event": result[4],
            "newest_event": result[5],
            "by_type": [
                {
                    "event_type": row[0],
                    "count": row[1],
                    "archived_count": row[2],
                }
                for row in type_results
            ],
        }
