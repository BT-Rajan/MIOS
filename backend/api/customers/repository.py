"""
Customer repository for database operations.

All customer data access goes through this repository.
"""

from typing import Optional, List

from sqlalchemy.orm import Session, Query

from shared.repositories import BaseRepository
from api.customers.models import Customer


class CustomerRepository(BaseRepository[Customer]):
    """
    Repository for customer entity operations.
    
    Provides centralized data access for all customer-related queries.
    """
    
    def __init__(self, session: Session) -> None:
        super().__init__(model=Customer, session=session)
    
    def get_by_code(self, code: str) -> Optional[Customer]:
        """Get customer by code."""
        return (
            self.session.query(Customer)
            .filter(Customer.code == code)
            .first()
        )
    
    def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email."""
        return (
            self.session.query(Customer)
            .filter(Customer.email == email)
            .first()
        )
    
    def search(
        self,
        query_string: str,
        limit: int = 20
    ) -> List[Customer]:
        """Search customers by name or code."""
        search_pattern = f"%{query_string}%"
        
        return (
            self.session.query(Customer)
            .filter(
                Customer.is_deleted == False,
                (Customer.name.ilike(search_pattern)) |
                (Customer.code.ilike(search_pattern))
            )
            .limit(limit)
            .all()
        )
    
    def get_active_customers(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Customer]:
        """Get all active customers."""
        return (
            self.session.query(Customer)
            .filter(
                Customer.is_active == True,
                Customer.is_deleted == False
            )
            .order_by(Customer.name)
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def get_with_outstanding_balance(
        self,
        limit: int = 50
    ) -> List[Customer]:
        """Get customers with outstanding orders."""
        from api.orders.models import Order
        
        return (
            self.session.query(Customer)
            .join(Order)
            .filter(
                Customer.is_active == True,
                Order.status.in_(["pending", "approved", "started"])
            )
            .distinct()
            .limit(limit)
            .all()
        )
    
    def exists_by_email(self, email: str) -> bool:
        """Check if customer exists by email."""
        return (
            self.session.query(Customer)
            .filter(Customer.email == email)
            .first() is not None
        )
    
    def exists_by_code(self, code: str) -> bool:
        """Check if customer exists by code."""
        return (
            self.session.query(Customer)
            .filter(Customer.code == code)
            .first() is not None
        )
