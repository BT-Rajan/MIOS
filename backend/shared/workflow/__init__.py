"""
Reusable workflow state machine engine.

All modules must use this engine for state transitions.
No implicit transitions allowed.
"""

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship, Session, declarative_base

from core.exceptions import WorkflowError
from core.constants import WorkflowStatus


Base = declarative_base()


class WorkflowTransition(Base):
    """Defines allowed state transitions."""
    
    __tablename__ = "workflow_transitions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(100), nullable=False, index=True)
    from_state = Column(String(50), nullable=False)
    to_state = Column(String(50), nullable=False)
    requires_approval = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )


class WorkflowEngine:
    """
    Central workflow engine for managing state machines.
    
    This engine enforces explicit state transitions and prevents
    invalid workflow jumps.
    """
    
    def __init__(self, session: Session) -> None:
        self.session = session
        self._default_transitions: dict[str, list[tuple[str, str]]] = {
            "order": [
                (WorkflowStatus.DRAFT, WorkflowStatus.SUBMITTED),
                (WorkflowStatus.SUBMITTED, WorkflowStatus.APPROVED),
                (WorkflowStatus.SUBMITTED, WorkflowStatus.REJECTED),
                (WorkflowStatus.APPROVED, WorkflowStatus.SCHEDULED),
                (WorkflowStatus.SCHEDULED, WorkflowStatus.STARTED),
                (WorkflowStatus.STARTED, WorkflowStatus.COMPLETED),
                (WorkflowStatus.DRAFT, WorkflowStatus.CANCELLED),
                (WorkflowStatus.SUBMITTED, WorkflowStatus.CANCELLED),
                (WorkflowStatus.APPROVED, WorkflowStatus.CANCELLED),
                (WorkflowStatus.SCHEDULED, WorkflowStatus.CANCELLED),
                (WorkflowStatus.STARTED, WorkflowStatus.CANCELLED),
            ],
            "purchase_request": [
                (WorkflowStatus.DRAFT, WorkflowStatus.SUBMITTED),
                (WorkflowStatus.SUBMITTED, WorkflowStatus.APPROVED),
                (WorkflowStatus.SUBMITTED, WorkflowStatus.REJECTED),
                (WorkflowStatus.APPROVED, WorkflowStatus.COMPLETED),
                (WorkflowStatus.DRAFT, WorkflowStatus.CANCELLED),
            ],
            "production_order": [
                (WorkflowStatus.DRAFT, WorkflowStatus.SCHEDULED),
                (WorkflowStatus.SCHEDULED, WorkflowStatus.STARTED),
                (WorkflowStatus.STARTED, WorkflowStatus.COMPLETED),
                (WorkflowStatus.SCHEDULED, WorkflowStatus.CANCELLED),
                (WorkflowStatus.STARTED, WorkflowStatus.CANCELLED),
            ]
        }
    
    def register_transition(
        self,
        entity_type: str,
        from_state: str,
        to_state: str,
        requires_approval: bool = False
    ) -> WorkflowTransition:
        """Register a new allowed transition."""
        transition = WorkflowTransition(
            entity_type=entity_type,
            from_state=from_state,
            to_state=to_state,
            requires_approval=requires_approval
        )
        
        self.session.add(transition)
        return transition
    
    def can_transition(
        self,
        entity_type: str,
        from_state: str,
        to_state: str
    ) -> bool:
        """Check if transition is allowed."""
        # Check database transitions first
        db_transition = (
            self.session.query(WorkflowTransition)
            .filter(
                WorkflowTransition.entity_type == entity_type,
                WorkflowTransition.from_state == from_state,
                WorkflowTransition.to_state == to_state
            )
            .first()
        )
        
        if db_transition:
            return True
        
        # Check default transitions
        defaults = self._default_transitions.get(entity_type, [])
        return (from_state, to_state) in defaults
    
    def transition(
        self,
        entity_type: str,
        current_state: str,
        target_state: str,
        actor_id: int,
        reason: Optional[str] = None
    ) -> str:
        """
        Execute a state transition.
        
        Args:
            entity_type: Type of entity
            current_state: Current state value
            target_state: Desired target state
            actor_id: ID of user performing transition
            reason: Optional reason for transition
            
        Returns:
            New state value
            
        Raises:
            WorkflowError: If transition is not allowed
        """
        if not self.can_transition(entity_type, current_state, target_state):
            raise WorkflowError(
                entity_type=entity_type,
                from_state=current_state,
                to_state=target_state
            )
        
        return target_state
    
    def get_allowed_transitions(
        self,
        entity_type: str,
        current_state: str
    ) -> list[str]:
        """Get all allowed next states from current state."""
        allowed = []
        
        # From database
        db_transitions = (
            self.session.query(WorkflowTransition)
            .filter(
                WorkflowTransition.entity_type == entity_type,
                WorkflowTransition.from_state == current_state
            )
            .all()
        )
        
        for t in db_transitions:
            if t.to_state not in allowed:
                allowed.append(t.to_state)
        
        # From defaults
        defaults = self._default_transitions.get(entity_type, [])
        for from_state, to_state in defaults:
            if from_state == current_state and to_state not in allowed:
                allowed.append(to_state)
        
        return allowed
    
    def requires_approval(
        self,
        entity_type: str,
        from_state: str,
        to_state: str
    ) -> bool:
        """Check if transition requires approval."""
        transition = (
            self.session.query(WorkflowTransition)
            .filter(
                WorkflowTransition.entity_type == entity_type,
                WorkflowTransition.from_state == from_state,
                WorkflowTransition.to_state == to_state
            )
            .first()
        )
        
        if transition:
            return transition.requires_approval
        
        return False
