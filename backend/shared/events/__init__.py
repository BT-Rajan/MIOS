"""
Central event bus for inter-module communication.

Modules publish events and other modules can react.
Loose coupling through event-driven architecture.
"""

from typing import Callable, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

from core.constants import EventType


@dataclass
class Event:
    """Event message structure."""
    
    event_type: str
    payload: dict[str, Any]
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id
        }


class EventBus:
    """
    Central event bus for module communication.
    
    Enables loose coupling between modules through
    publish-subscribe pattern.
    """
    
    _instance: Optional["EventBus"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "EventBus":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if not self._initialized:
            self._subscribers: dict[str, list[Callable]] = {}
            self._event_history: list[Event] = []
            self._initialized = True
    
    @classmethod
    def get_instance(cls) -> "EventBus":
        """Get singleton instance."""
        return cls()
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None]
    ) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
    
    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None]
    ) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type]
                if h != handler
            ]
    
    def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Event:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of event
            payload: Event data payload
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            Published Event instance
        """
        event = Event(
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id
        )
        
        # Store in history (limited)
        self._event_history.append(event)
        if len(self._event_history) > 1000:
            self._event_history = self._event_history[-500:]
        
        # Notify subscribers
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Log but don't fail publishing
                pass
        
        # Also notify wildcard subscribers
        wildcard_handlers = self._subscribers.get("*", [])
        for handler in wildcard_handlers:
            try:
                handler(event)
            except Exception:
                pass
        
        return event
    
    def publish_entity_event(
        self,
        action: str,
        entity_type: str,
        entity_id: int,
        data: Optional[dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> Event:
        """Publish standard entity event."""
        event_type_map = {
            "created": EventType.ENTITY_CREATED.value,
            "updated": EventType.ENTITY_UPDATED.value,
            "deleted": EventType.ENTITY_DELETED.value
        }
        
        base_type = event_type_map.get(action, "entity.action")
        event_type = f"{base_type}.{entity_type}"
        
        payload = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            **(data or {})
        }
        
        return self.publish(
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id
        )
    
    def get_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> list[Event]:
        """Get recent event history."""
        if event_type:
            filtered = [
                e for e in self._event_history
                if e.event_type == event_type
            ]
            return filtered[-limit:]
        
        return self._event_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history = []
