"""
Customer service layer for business logic.

All customer operations go through this service.
Uses shared engines for audit, validation, and workflow.
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from backend.core.exceptions import ValidationError, NotFoundError, ConflictError
from backend.shared.audit import AuditEngine
from backend.shared.validation import ValidationEngine
from backend.api.customers.models import Customer
from backend.api.customers.repository import CustomerRepository
from backend.api.customers.schemas import CustomerCreate, CustomerUpdate


class CustomerService:
    """
    Service for customer business logic.
    
    This is the only entry point for customer operations.
    All business rules are enforced here.
    """
    
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = CustomerRepository(session)
        self.audit = AuditEngine(session)
    
    def create_customer(
        self,
        data: CustomerCreate,
        actor_id: int
    ) -> Customer:
        """
        Create a new customer.
        
        Args:
            data: Customer creation data
            actor_id: ID of user creating customer
            
        Returns:
            Created Customer instance
            
        Raises:
            ConflictError: If email already exists
        """
        # Validate required fields
        ValidationEngine.validate_required_field(data.name, "name")
        ValidationEngine.validate_required_field(data.email, "email")
        
        # Check uniqueness
        if self.repository.exists_by_email(data.email):
            raise ConflictError("Customer with this email already exists")
        
        # Generate code
        next_id = self.repository.count() + 1
        code = Customer.generate_code(next_id)
        
        # Create customer
        customer_data = data.model_dump()
        customer_data["code"] = code
        
        customer = self.repository.create(customer_data)
        
        # Audit
        self.audit.record_event(
            entity_type="customer",
            entity_id=customer.id,
            action="created",
            actor_id=actor_id,
            new_state={"code": code, "name": customer.name}
        )
        
        return customer
    
    def get_customer(self, customer_id: int) -> Customer:
        """
        Get customer by ID.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer instance
            
        Raises:
            NotFoundError: If customer not found
        """
        return self.repository.get(customer_id)
    
    def update_customer(
        self,
        customer_id: int,
        data: CustomerUpdate,
        actor_id: int
    ) -> Customer:
        """
        Update customer.
        
        Args:
            customer_id: Customer ID
            data: Update data
            actor_id: ID of user updating
            
        Returns:
            Updated Customer instance
        """
        customer = self.get_customer(customer_id)
        
        # Capture old state for audit
        old_state = {
            "name": customer.name,
            "email": customer.email,
            "credit_limit": float(customer.credit_limit) if customer.credit_limit else 0
        }
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        
        if "email" in update_data:
            if update_data["email"] != customer.email:
                if self.repository.exists_by_email(update_data["email"]):
                    raise ConflictError("Email already in use")
        
        customer = self.repository.update(customer_id, update_data)
        
        # Audit
        self.audit.record_event(
            entity_type="customer",
            entity_id=customer_id,
            action="updated",
            actor_id=actor_id,
            old_state=old_state,
            new_state={
                "name": customer.name,
                "email": customer.email
            }
        )
        
        return customer
    
    def deactivate_customer(
        self,
        customer_id: int,
        actor_id: int,
        reason: str
    ) -> Customer:
        """
        Deactivate a customer.
        
        Args:
            customer_id: Customer ID
            actor_id: ID of user deactivating
            reason: Reason for deactivation
            
        Returns:
            Deactivated Customer instance
        """
        ValidationEngine.validate_reason_required(reason, "deactivation")
        
        customer = self.get_customer(customer_id)
        
        old_state = {"is_active": customer.is_active}
        
        customer.is_active = False
        customer.status = "inactive"
        self.session.flush()
        
        # Audit
        self.audit.record_event(
            entity_type="customer",
            entity_id=customer_id,
            action="deactivated",
            actor_id=actor_id,
            old_state=old_state,
            new_state={"is_active": False, "status": "inactive"},
            reason=reason
        )
        
        return customer
    
    def search_customers(
        self,
        query: str,
        limit: int = 20
    ) -> List[Customer]:
        """
        Search customers.
        
        Args:
            query: Search string
            limit: Maximum results
            
        Returns:
            List of matching customers
        """
        return self.repository.search(query, limit)
    
    def get_active_customers(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Customer]:
        """
        Get all active customers.
        
        Args:
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of active customers
        """
        return self.repository.get_active_customers(limit, offset)
