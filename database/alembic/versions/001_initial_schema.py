"""Initial audit schema with append-only guarantees

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create audit_events table with append-only design
    op.execute("""
        CREATE TABLE audit_events (
            id BIGSERIAL PRIMARY KEY,
            event_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
            timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            event_type VARCHAR(100) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            
            -- Source information
            source_service VARCHAR(200),
            source_host VARCHAR(255),
            source_ip INET,
            
            -- Actor information (for user actions)
            user_id VARCHAR(200),
            user_name VARCHAR(255),
            
            -- Action details
            action VARCHAR(200),
            resource VARCHAR(500),
            resource_type VARCHAR(100),
            result VARCHAR(50),
            
            -- Detection/Scan specific
            detection_type VARCHAR(100),
            scan_id VARCHAR(200),
            
            -- Metadata and context
            metadata JSONB,
            tags TEXT[],
            
            -- Tamper-evidence fields
            previous_hash VARCHAR(64),
            event_hash VARCHAR(64) NOT NULL,
            signature TEXT,
            
            -- Retention management
            retention_days INTEGER DEFAULT 2555,
            archived BOOLEAN DEFAULT FALSE,
            archive_location TEXT,
            
            -- Indexing
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create indexes for common query patterns
    op.execute("CREATE INDEX idx_audit_events_timestamp ON audit_events(timestamp DESC);")
    op.execute("CREATE INDEX idx_audit_events_event_type ON audit_events(event_type);")
    op.execute("CREATE INDEX idx_audit_events_severity ON audit_events(severity);")
    op.execute("CREATE INDEX idx_audit_events_user_id ON audit_events(user_id) WHERE user_id IS NOT NULL;")
    op.execute("CREATE INDEX idx_audit_events_action ON audit_events(action) WHERE action IS NOT NULL;")
    op.execute("CREATE INDEX idx_audit_events_detection_type ON audit_events(detection_type) WHERE detection_type IS NOT NULL;")
    op.execute("CREATE INDEX idx_audit_events_metadata ON audit_events USING GIN(metadata);")
    op.execute("CREATE INDEX idx_audit_events_tags ON audit_events USING GIN(tags);")
    op.execute("CREATE INDEX idx_audit_events_archived ON audit_events(archived, timestamp) WHERE NOT archived;")
    
    # Create trigger to prevent updates and deletes (WORM guarantee)
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                -- Only allow archival updates
                IF NEW.archived = TRUE AND OLD.archived = FALSE THEN
                    NEW.id := OLD.id;
                    NEW.event_id := OLD.event_id;
                    NEW.timestamp := OLD.timestamp;
                    NEW.event_type := OLD.event_type;
                    NEW.severity := OLD.severity;
                    NEW.source_service := OLD.source_service;
                    NEW.source_host := OLD.source_host;
                    NEW.source_ip := OLD.source_ip;
                    NEW.user_id := OLD.user_id;
                    NEW.user_name := OLD.user_name;
                    NEW.action := OLD.action;
                    NEW.resource := OLD.resource;
                    NEW.resource_type := OLD.resource_type;
                    NEW.result := OLD.result;
                    NEW.detection_type := OLD.detection_type;
                    NEW.scan_id := OLD.scan_id;
                    NEW.metadata := OLD.metadata;
                    NEW.tags := OLD.tags;
                    NEW.previous_hash := OLD.previous_hash;
                    NEW.event_hash := OLD.event_hash;
                    NEW.signature := OLD.signature;
                    NEW.retention_days := OLD.retention_days;
                    NEW.created_at := OLD.created_at;
                    RETURN NEW;
                ELSE
                    RAISE EXCEPTION 'Audit events cannot be modified (WORM protection)';
                END IF;
            ELSIF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'Audit events cannot be deleted (WORM protection)';
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER audit_events_immutable
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_modification();
    """)
    
    # Create retention policy table
    op.execute("""
        CREATE TABLE retention_policies (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(100) NOT NULL UNIQUE,
            retention_days INTEGER NOT NULL,
            archive_enabled BOOLEAN DEFAULT TRUE,
            archive_location TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Insert default retention policies
    op.execute("""
        INSERT INTO retention_policies (event_type, retention_days, archive_enabled) VALUES
        ('user_action', 2555, TRUE),      -- 7 years for user actions (compliance)
        ('detection', 1825, TRUE),         -- 5 years for detections
        ('scan', 365, TRUE),               -- 1 year for scans
        ('system_event', 730, TRUE),       -- 2 years for system events
        ('default', 2555, TRUE);           -- 7 years default
    """)
    
    # Create audit access log (meta-auditing)
    op.execute("""
        CREATE TABLE audit_access_log (
            id BIGSERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            accessor_id VARCHAR(200),
            accessor_ip INET,
            operation VARCHAR(50) NOT NULL,
            query_filters JSONB,
            records_accessed INTEGER,
            success BOOLEAN NOT NULL,
            error_message TEXT
        );
    """)
    
    op.execute("CREATE INDEX idx_audit_access_log_timestamp ON audit_access_log(timestamp DESC);")
    op.execute("CREATE INDEX idx_audit_access_log_accessor ON audit_access_log(accessor_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_access_log;")
    op.execute("DROP TABLE IF EXISTS retention_policies;")
    op.execute("DROP TRIGGER IF EXISTS audit_events_immutable ON audit_events;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_modification();")
    op.execute("DROP TABLE IF EXISTS audit_events;")
