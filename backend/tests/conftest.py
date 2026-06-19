"""
Pytest configuration for MIOS.

Test settings and fixtures.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db_session():
    """Create in-memory database session for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    from shared.models.base import Base
    Base.metadata.create_all(bind=engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()


@pytest.fixture
def audit_engine(db_session):
    """Create audit engine with test session."""
    from shared.audit import AuditEngine
    return AuditEngine(db_session)


@pytest.fixture
def workflow_engine(db_session):
    """Create workflow engine with test session."""
    from shared.workflow import WorkflowEngine
    return WorkflowEngine(db_session)


@pytest.fixture
def permission_engine(db_session):
    """Create permission engine with test session."""
    from shared.permissions import PermissionEngine
    return PermissionEngine(db_session)


@pytest.fixture
def notification_engine(db_session):
    """Create notification engine with test session."""
    from shared.notifications import NotificationEngine
    return NotificationEngine(db_session)


@pytest.fixture
def validation_engine():
    """Get validation engine (stateless)."""
    from shared.validation import ValidationEngine
    return ValidationEngine()


@pytest.fixture
def event_bus():
    """Get fresh event bus instance."""
    from shared.events import EventBus
    EventBus._instance = None
    EventBus._initialized = False
    return EventBus.get_instance()
