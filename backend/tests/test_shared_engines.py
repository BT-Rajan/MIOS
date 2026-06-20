"""
Comprehensive test suite for MIOS shared engines.

Tests audit, workflow, validation, permissions, and event systems.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from backend.shared.validation import ValidationEngine
from backend.shared.events import EventBus, Event
from backend.core.exceptions import ValidationError, WorkflowError


class TestValidationEngine:
    """Test validation engine functionality."""
    
    def test_validate_positive_number_success(self):
        """Should accept positive numbers."""
        ValidationEngine.validate_positive_number(10, "amount")
        ValidationEngine.validate_positive_number(0.5, "rate")
    
    def test_validate_positive_number_failure(self):
        """Should reject non-positive numbers."""
        with pytest.raises(ValidationError):
            ValidationEngine.validate_positive_number(0, "amount")
        
        with pytest.raises(ValidationError):
            ValidationEngine.validate_positive_number(-5, "amount")
    
    def test_validate_required_field_success(self):
        """Should accept non-empty values."""
        ValidationEngine.validate_required_field("value", "field")
        ValidationEngine.validate_required_field(123, "field")
    
    def test_validate_required_field_failure(self):
        """Should reject empty values."""
        with pytest.raises(ValidationError):
            ValidationEngine.validate_required_field(None, "field")
        
        with pytest.raises(ValidationError):
            ValidationEngine.validate_required_field("", "field")
        
        with pytest.raises(ValidationError):
            ValidationEngine.validate_required_field("   ", "field")
    
    def test_validate_percentage(self):
        """Should validate percentage range."""
        ValidationEngine.validate_percentage(50, "discount")
        ValidationEngine.validate_percentage(0, "discount")
        ValidationEngine.validate_percentage(100, "discount")
        
        with pytest.raises(ValidationError):
            ValidationEngine.validate_percentage(-1, "discount")
        
        with pytest.raises(ValidationError):
            ValidationEngine.validate_percentage(101, "discount")


class TestEventBus:
    """Test event bus functionality."""
    
    def setup_method(self):
        """Reset event bus before each test."""
        EventBus._instance = None
        EventBus._initialized = False
    
    def test_publish_and_subscribe(self):
        """Should notify subscribers on publish."""
        bus = EventBus.get_instance()
        received_events = []
        
        def handler(event: Event):
            received_events.append(event)
        
        bus.subscribe("test.event", handler)
        bus.publish("test.event", {"data": "value"})
        
        assert len(received_events) == 1
        assert received_events[0].payload == {"data": "value"}
    
    def test_multiple_subscribers(self):
        """Should notify all subscribers."""
        bus = EventBus.get_instance()
        received_count = [0]
        
        def handler1(event: Event):
            received_count[0] += 1
        
        def handler2(event: Event):
            received_count[0] += 1
        
        bus.subscribe("multi.event", handler1)
        bus.subscribe("multi.event", handler2)
        bus.publish("multi.event", {})
        
        assert received_count[0] == 2
    
    def test_unsubscribe(self):
        """Should stop notifying unsubscribed handlers."""
        bus = EventBus.get_instance()
        received = []
        
        def handler(event: Event):
            received.append(event)
        
        bus.subscribe("unsub.event", handler)
        bus.unsubscribe("unsub.event", handler)
        bus.publish("unsub.event", {})
        
        assert len(received) == 0
    
    def test_event_history(self):
        """Should maintain event history."""
        bus = EventBus.get_instance()
        
        bus.publish("history.event", {"seq": 1})
        bus.publish("history.event", {"seq": 2})
        bus.publish("other.event", {"seq": 3})
        
        all_events = bus.get_history(limit=10)
        assert len(all_events) == 3
        
        filtered = bus.get_history(event_type="history.event")
        assert len(filtered) == 2


class TestWorkflowTransitions:
    """Test workflow transition logic."""
    
    def test_default_order_transitions(self):
        """Should allow standard order workflow."""
        from shared.workflow import WorkflowEngine
        from core.constants import WorkflowStatus
        
        # Mock session
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        engine = WorkflowEngine(mock_session)
        
        # Valid transitions
        assert engine.can_transition("order", WorkflowStatus.DRAFT, WorkflowStatus.SUBMITTED)
        assert engine.can_transition("order", WorkflowStatus.SUBMITTED, WorkflowStatus.APPROVED)
        assert engine.can_transition("order", WorkflowStatus.APPROVED, WorkflowStatus.SCHEDULED)
        
        # Invalid transitions
        assert not engine.can_transition("order", WorkflowStatus.DRAFT, WorkflowStatus.COMPLETED)
        assert not engine.can_transition("order", WorkflowStatus.SUBMITTED, WorkflowStatus.STARTED)
    
    def test_get_allowed_transitions(self):
        """Should return valid next states."""
        from shared.workflow import WorkflowEngine
        from core.constants import WorkflowStatus
        
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        engine = WorkflowEngine(mock_session)
        allowed = engine.get_allowed_transitions("order", WorkflowStatus.DRAFT)
        
        assert WorkflowStatus.SUBMITTED in allowed
        assert WorkflowStatus.CANCELLED in allowed
        assert WorkflowStatus.COMPLETED not in allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
