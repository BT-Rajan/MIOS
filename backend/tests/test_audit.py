"""
Test audit engine functionality.

Verifies immutable event logging works correctly.
"""

import pytest
from datetime import datetime, timezone


class TestAuditEngine:
    """Test audit engine for immutable event logging."""
    
    def test_record_event_creates_entry(self, audit_engine, db_session):
        """Should create audit record for event."""
        event = audit_engine.record_event(
            entity_type="order",
            entity_id=100,
            action="created",
            actor_id=1,
            old_state=None,
            new_state={"status": "draft"},
            reason="Initial creation"
        )
        
        assert event.id is not None
        assert event.entity_type == "order"
        assert event.entity_id == 100
        assert event.action == "created"
        assert event.actor_id == 1
    
    def test_record_event_generates_correlation_id(self, audit_engine):
        """Should generate correlation ID if not provided."""
        event = audit_engine.record_event(
            entity_type="product",
            entity_id=50,
            action="updated",
            actor_id=2
        )
        
        assert event.correlation_id is not None
        assert len(event.correlation_id) == 36  # UUID length
    
    def test_record_event_with_custom_correlation_id(self, audit_engine):
        """Should use provided correlation ID."""
        custom_id = "test-correlation-123"
        event = audit_engine.record_event(
            entity_type="inventory",
            entity_id=1,
            action="adjusted",
            actor_id=1,
            correlation_id=custom_id
        )
        
        assert event.correlation_id == custom_id
    
    def test_get_entity_history(self, audit_engine, db_session):
        """Should return complete history for entity."""
        # Record multiple events
        audit_engine.record_event(
            entity_type="order",
            entity_id=100,
            action="created",
            actor_id=1
        )
        
        audit_engine.record_event(
            entity_type="order",
            entity_id=100,
            action="submitted",
            actor_id=1
        )
        
        audit_engine.record_event(
            entity_type="order",
            entity_id=100,
            action="approved",
            actor_id=2
        )
        
        # Get history
        history = audit_engine.get_entity_history("order", 100)
        
        assert len(history) == 3
        assert history[0].action == "created"
        assert history[1].action == "submitted"
        assert history[2].action == "approved"
    
    def test_get_events_by_correlation(self, audit_engine):
        """Should find all related events by correlation ID."""
        correlation_id = "correlation-xyz-789"
        
        audit_engine.record_event(
            entity_type="order",
            entity_id=100,
            action="created",
            actor_id=1,
            correlation_id=correlation_id
        )
        
        audit_engine.record_event(
            entity_type="inventory",
            entity_id=50,
            action="reserved",
            actor_id=1,
            correlation_id=correlation_id
        )
        
        events = audit_engine.get_events_by_correlation(correlation_id)
        
        assert len(events) == 2
        assert all(e.correlation_id == correlation_id for e in events)
    
    def test_audit_record_is_immutable(self, audit_engine, db_session):
        """Should not allow updates to audit records."""
        event = audit_engine.record_event(
            entity_type="order",
            entity_id=100,
            action="created",
            actor_id=1
        )
        
        original_timestamp = event.timestamp
        
        # Try to modify (this should not affect the ledger)
        event.action = "modified"
        db_session.flush()
        
        # Reload from database
        db_session.refresh(event)
        assert event.action == "created"  # Should remain unchanged
