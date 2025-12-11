from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import compute_hash, sign_event
from app.models.schemas import AuditEventCreate, QueryParams


class AuditService:
    """Service for managing audit events."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_last_event_hash(self) -> Optional[str]:
        """Get hash of the most recent event for chain integrity."""
        result = self.db.execute(
            text("SELECT event_hash FROM audit_events ORDER BY id DESC LIMIT 1")
        ).fetchone()
        return result[0] if result else None
    
    def create_event(self, event_data: AuditEventCreate) -> Dict[str, Any]:
        """Create a new audit event with tamper-evidence."""
        previous_hash = self._get_last_event_hash()
        
        event_dict = event_data.model_dump()
        event_dict["timestamp"] = datetime.utcnow()
        
        event_hash = compute_hash(event_dict, previous_hash)
        
        signature = None
        if settings.ENABLE_SIGNATURES:
            signature = sign_event(event_dict, settings.SIGNATURE_SECRET)
        
        insert_query = text("""
            INSERT INTO audit_events (
                event_type, severity, source_service, source_host, source_ip,
                user_id, user_name, action, resource, resource_type, result,
                detection_type, scan_id, metadata, tags, previous_hash, 
                event_hash, signature, retention_days
            ) VALUES (
                :event_type, :severity, :source_service, :source_host, :source_ip,
                :user_id, :user_name, :action, :resource, :resource_type, :result,
                :detection_type, :scan_id, :metadata, :tags, :previous_hash,
                :event_hash, :signature, :retention_days
            ) RETURNING id, event_id, timestamp, created_at
        """)
        
        result = self.db.execute(
            insert_query,
            {
                "event_type": event_data.event_type,
                "severity": event_data.severity,
                "source_service": event_data.source_service,
                "source_host": event_data.source_host,
                "source_ip": event_data.source_ip,
                "user_id": event_data.user_id,
                "user_name": event_data.user_name,
                "action": event_data.action,
                "resource": event_data.resource,
                "resource_type": event_data.resource_type,
                "result": event_data.result,
                "detection_type": event_data.detection_type,
                "scan_id": event_data.scan_id,
                "metadata": event_data.metadata,
                "tags": event_data.tags,
                "previous_hash": previous_hash,
                "event_hash": event_hash,
                "signature": signature,
                "retention_days": event_data.retention_days or settings.DEFAULT_RETENTION_DAYS,
            }
        ).fetchone()
        
        self.db.commit()
        
        return {
            "id": result[0],
            "event_id": result[1],
            "timestamp": result[2],
            "event_hash": event_hash,
            "previous_hash": previous_hash,
            "created_at": result[3],
        }
    
    def query_events(self, params: QueryParams) -> Dict[str, Any]:
        """Query audit events with filtering."""
        conditions = []
        query_params = {}
        
        if params.event_type:
            conditions.append("event_type = :event_type")
            query_params["event_type"] = params.event_type
        
        if params.severity:
            conditions.append("severity = :severity")
            query_params["severity"] = params.severity
        
        if params.user_id:
            conditions.append("user_id = :user_id")
            query_params["user_id"] = params.user_id
        
        if params.action:
            conditions.append("action = :action")
            query_params["action"] = params.action
        
        if params.detection_type:
            conditions.append("detection_type = :detection_type")
            query_params["detection_type"] = params.detection_type
        
        if params.start_time:
            conditions.append("timestamp >= :start_time")
            query_params["start_time"] = params.start_time
        
        if params.end_time:
            conditions.append("timestamp <= :end_time")
            query_params["end_time"] = params.end_time
        
        if params.source_service:
            conditions.append("source_service = :source_service")
            query_params["source_service"] = params.source_service
        
        if params.tags:
            conditions.append("tags && :tags")
            query_params["tags"] = params.tags
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        count_query = text(f"SELECT COUNT(*) FROM audit_events WHERE {where_clause}")
        total = self.db.execute(count_query, query_params).scalar()
        
        query_params["limit"] = params.limit
        query_params["offset"] = params.offset
        
        select_query = text(f"""
            SELECT * FROM audit_events 
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT :limit OFFSET :offset
        """)
        
        results = self.db.execute(select_query, query_params).fetchall()
        
        events = []
        for row in results:
            events.append({
                "id": row[0],
                "event_id": row[1],
                "timestamp": row[2],
                "event_type": row[3],
                "severity": row[4],
                "source_service": row[5],
                "source_host": row[6],
                "source_ip": row[7],
                "user_id": row[8],
                "user_name": row[9],
                "action": row[10],
                "resource": row[11],
                "resource_type": row[12],
                "result": row[13],
                "detection_type": row[14],
                "scan_id": row[15],
                "metadata": row[16],
                "tags": row[17],
                "previous_hash": row[18],
                "event_hash": row[19],
                "signature": row[20],
                "retention_days": row[21],
                "archived": row[22],
                "archive_location": row[23],
                "created_at": row[24],
            })
        
        self._log_access(params, len(events))
        
        return {
            "total": total,
            "limit": params.limit,
            "offset": params.offset,
            "events": events,
        }
    
    def get_event_by_id(self, event_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a specific event by its UUID."""
        query = text("SELECT * FROM audit_events WHERE event_id = :event_id")
        result = self.db.execute(query, {"event_id": str(event_id)}).fetchone()
        
        if not result:
            return None
        
        return {
            "id": result[0],
            "event_id": result[1],
            "timestamp": result[2],
            "event_type": result[3],
            "severity": result[4],
            "source_service": result[5],
            "source_host": result[6],
            "source_ip": result[7],
            "user_id": result[8],
            "user_name": result[9],
            "action": result[10],
            "resource": result[11],
            "resource_type": result[12],
            "result": result[13],
            "detection_type": result[14],
            "scan_id": result[15],
            "metadata": result[16],
            "tags": result[17],
            "previous_hash": result[18],
            "event_hash": result[19],
            "signature": result[20],
            "retention_days": result[21],
            "archived": result[22],
            "archive_location": result[23],
            "created_at": result[24],
        }
    
    def verify_chain_integrity(self, limit: int = 1000) -> Dict[str, Any]:
        """Verify the hash chain integrity of recent events."""
        query = text("""
            SELECT id, event_hash, previous_hash, timestamp, event_type, 
                   severity, source_service, user_id, action, resource, 
                   result, detection_type, metadata
            FROM audit_events
            ORDER BY id DESC
            LIMIT :limit
        """)
        
        results = self.db.execute(query, {"limit": limit}).fetchall()
        
        if not results:
            return {"status": "ok", "verified": 0, "errors": []}
        
        errors = []
        verified = 0
        
        for i in range(len(results) - 1, -1, -1):
            current = results[i]
            previous_hash = results[i + 1][1] if i < len(results) - 1 else None
            
            data = {
                "timestamp": current[3],
                "event_type": current[4],
                "severity": current[5],
                "source_service": current[6],
                "user_id": current[7],
                "action": current[8],
                "resource": current[9],
                "result": current[10],
                "detection_type": current[11],
                "metadata": current[12],
            }
            
            expected_hash = compute_hash(data, previous_hash)
            
            if expected_hash != current[1]:
                errors.append({
                    "event_id": current[0],
                    "expected_hash": expected_hash,
                    "actual_hash": current[1],
                })
            else:
                verified += 1
        
        status = "ok" if not errors else "integrity_violation"
        
        return {
            "status": status,
            "verified": verified,
            "total_checked": len(results),
            "errors": errors,
        }
    
    def _log_access(self, query_params: QueryParams, records_accessed: int):
        """Log access to audit events (meta-auditing)."""
        insert_query = text("""
            INSERT INTO audit_access_log (
                operation, query_filters, records_accessed, success
            ) VALUES (
                'query', :filters, :records_accessed, TRUE
            )
        """)
        
        self.db.execute(
            insert_query,
            {
                "filters": query_params.model_dump(),
                "records_accessed": records_accessed,
            }
        )
        self.db.commit()
