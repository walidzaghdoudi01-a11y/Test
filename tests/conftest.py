import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Use test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://audituser:auditpass@localhost:5432/auditdb_test"
)


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a new database session for a test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def clean_db(db_session):
    """Clean database tables before each test."""
    db_session.execute(text("TRUNCATE TABLE audit_events, audit_access_log, retention_policies CASCADE"))
    
    db_session.execute(text("""
        INSERT INTO retention_policies (event_type, retention_days, archive_enabled) VALUES
        ('user_action', 2555, TRUE),
        ('detection', 1825, TRUE),
        ('scan', 365, TRUE),
        ('system_event', 730, TRUE),
        ('default', 2555, TRUE)
    """))
    db_session.commit()
    
    yield db_session
