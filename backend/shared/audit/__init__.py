"""
Shared audit engine for immutable event logging.

This is a core reusable engine used by ALL modules.
"""

from datetime import datetime, timezone
from typing import Optional, Any
from uuid import uuid4

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship, Session, declarative_base

from backend.core.exceptions import AuditError


Base = declarative_base()


class EventLedger(Base):
    """Immutable audit event ledger."""
    
    __tablename__ = "event_ledger"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    correlation_id = Column(String(36), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    old_state_json = Column(JSON, nullable=True)
    new_state_json = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "correlation_id": self.correlation_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "actor_id": self.actor_id,
            "old_state": self.old_state_json,
            "new_state": self.new_state_json,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class AuditEngine:
    """
    Central audit engine for recording immutable events.
    
    This engine is used by all modules to ensure complete traceability.
    All state changes MUST be recorded through this engine.
    """
    
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def record_event(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        actor_id: int,
        old_state: Optional[dict[str, Any]] = None,
        new_state: Optional[dict[str, Any]] = None,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> EventLedger:
        """
        Record an immutable audit event.
        
        Args:
            entity_type: Type of entity (e.g., 'order', 'inventory')
            entity_id: ID of the entity
            action: Action performed (e.g., 'approved', 'updated')
            actor_id: ID of user who performed action
            old_state: Previous state as dictionary
            new_state: New state as dictionary
            reason: Optional reason for the action
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Created EventLedger instance
            
        Raises:
            AuditError: If recording fails
        """
        try:
            event = EventLedger(
                correlation_id=correlation_id or str(uuid4()),
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                actor_id=actor_id,
                old_state_json=old_state,
                new_state_json=new_state,
                reason=reason
            )
            
            self.session.add(event)
            self.session.flush()
            
            return event
            
        except Exception as e:
            raise AuditError(f"Failed to record audit event: {str(e)}")
    
    def get_entity_history(
        self,
        entity_type: str,
        entity_id: int
    ) -> list[EventLedger]:
        """
        Get complete audit history for an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            
        Returns:
            List of audit events ordered by timestamp
        """
        return (
            self.session.query(EventLedger)
            .filter(
                EventLedger.entity_type == entity_type,
                EventLedger.entity_id == entity_id
            )
            .order_by(EventLedger.timestamp.asc())
            .all()
        )
    
    def get_events_by_correlation(
        self,
        correlation_id: str
    ) -> list[EventLedger]:
        """
        Get all events with same correlation ID.
        
        Useful for tracing related operations across modules.
        """
        return (
            self.session.query(EventLedger)
            .filter(EventLedger.correlation_id == correlation_id)
            .order_by(EventLedger.timestamp.asc())
            .all()
        )
