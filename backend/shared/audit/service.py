"""Audit service for recording immutable events."""

from sqlalchemy.orm import Session
from typing import Optional, Any

from backend.shared.audit import AuditEngine, EventLedger


class AuditService:
    """Service for audit logging operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.engine = AuditEngine(db)
    
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
        """Record an immutable audit event."""
        return self.engine.record_event(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            old_state=old_state,
            new_state=new_state,
            reason=reason,
            correlation_id=correlation_id
        )
    
    def get_entity_history(self, entity_type: str, entity_id: int) -> list[EventLedger]:
        """Get audit history for an entity."""
        return self.engine.get_entity_history(entity_type, entity_id)
    
    def get_user_actions(self, user_id: int, limit: int = 100) -> list[EventLedger]:
        """Get actions performed by a user."""
        return self.engine.get_user_actions(user_id, limit)
