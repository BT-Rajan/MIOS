"""
Reusable notification engine.

Single engine for all module communications.
No duplicate notification code allowed.
"""

from typing import Optional, Any
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship, Session, declarative_base

from backend.core.constants import NotificationType


Base = declarative_base()


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class Notification(Base):
    """Notification model."""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    status = Column(String(20), default=NotificationStatus.PENDING)
    is_read = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)


class NotificationEngine:
    """
    Central notification engine for all communications.
    
    All modules must use this engine instead of implementing
    their own notification logic.
    """
    
    def __init__(self, session: Session) -> None:
        self.session = session
        self._handlers: dict[str, callable] = {}
    
    def register_handler(
        self,
        notification_type: str,
        handler: callable
    ) -> None:
        """Register a handler for notification type."""
        self._handlers[notification_type] = handler
    
    def send(
        self,
        user_id: int,
        notification_type: str,
        message: str,
        title: Optional[str] = None,
        data: Optional[dict[str, Any]] = None
    ) -> Notification:
        """
        Send a notification to a user.
        
        Args:
            user_id: ID of recipient user
            notification_type: Type of notification
            message: Notification message body
            title: Optional notification title
            data: Optional additional data payload
            
        Returns:
            Created Notification instance
        """
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title or "Notification",
            message=message,
            data=data
        )
        
        self.session.add(notification)
        self.session.flush()
        
        # Trigger registered handler if exists
        handler = self._handlers.get(notification_type)
        if handler:
            try:
                handler(notification)
            except Exception:
                # Log but don't fail notification creation
                pass
        
        return notification
    
    def send_info(
        self,
        user_id: int,
        message: str,
        title: Optional[str] = None,
        data: Optional[dict[str, Any]] = None
    ) -> Notification:
        """Send informational notification."""
        return self.send(
            user_id=user_id,
            notification_type=NotificationType.INFO.value,
            message=message,
            title=title,
            data=data
        )
    
    def send_warning(
        self,
        user_id: int,
        message: str,
        title: Optional[str] = None,
        data: Optional[dict[str, Any]] = None
    ) -> Notification:
        """Send warning notification."""
        return self.send(
            user_id=user_id,
            notification_type=NotificationType.WARNING.value,
            message=message,
            title=title or "Warning",
            data=data
        )
    
    def send_error(
        self,
        user_id: int,
        message: str,
        title: Optional[str] = None,
        data: Optional[dict[str, Any]] = None
    ) -> Notification:
        """Send error notification."""
        return self.send(
            user_id=user_id,
            notification_type=NotificationType.ERROR.value,
            message=message,
            title=title or "Error",
            data=data
        )
    
    def send_success(
        self,
        user_id: int,
        message: str,
        title: Optional[str] = None,
        data: Optional[dict[str, Any]] = None
    ) -> Notification:
        """Send success notification."""
        return self.send(
            user_id=user_id,
            notification_type=NotificationType.SUCCESS.value,
            message=message,
            title=title or "Success",
            data=data
        )
    
    def mark_as_read(self, notification_id: int) -> None:
        """Mark notification as read."""
        notification = (
            self.session.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )
        
        if notification:
            notification.is_read = True
    
    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        count = (
            self.session.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            .update({"is_read": True})
        )
        
        return count
    
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for user."""
        return (
            self.session.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            .count()
        )
    
    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[Notification]:
        """Get notifications for a user."""
        return (
            self.session.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
