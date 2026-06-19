"""
Vendor service layer for business logic.

All vendor operations go through this service.
Uses shared engines for audit, validation, and workflow.
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from core.exceptions import ValidationError, NotFoundError, ConflictError
from shared.audit import AuditEngine
from shared.validation import ValidationEngine
from api.vendors.models import Vendor
from api.vendors.repository import VendorRepository
from api.vendors.schemas import VendorCreate, VendorUpdate


class VendorService:
    """
    Service for vendor business logic.
    
    This is the only entry point for vendor operations.
    All business rules are enforced here.
    """
    
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = VendorRepository(session)
        self.audit = AuditEngine(session)
    
    def create_vendor(
        self,
        data: VendorCreate,
        actor_id: int
    ) -> Vendor:
        """
        Create a new vendor.
        
        Args:
            data: Vendor creation data
            actor_id: ID of user creating vendor
            
        Returns:
            Created Vendor instance
            
        Raises:
            ConflictError: If email already exists
        """
        # Validate required fields
        ValidationEngine.validate_required_field(data.name, "name")
        ValidationEngine.validate_required_field(data.email, "email")
        
        # Check uniqueness
        if self.repository.exists_by_email(data.email):
            raise ConflictError("Vendor with this email already exists")
        
        # Generate code
        next_id = self.repository.count() + 1
        code = Vendor.generate_code(next_id)
        
        # Create vendor
        vendor_data = data.model_dump()
        vendor_data["code"] = code
        
        vendor = self.repository.create(vendor_data)
        
        # Audit
        self.audit.record_event(
            entity_type="vendor",
            entity_id=vendor.id,
            action="created",
            actor_id=actor_id,
            new_state={"code": code, "name": vendor.name}
        )
        
        return vendor
    
    def get_vendor(self, vendor_id: int) -> Vendor:
        """
        Get vendor by ID.
        
        Args:
            vendor_id: Vendor ID
            
        Returns:
            Vendor instance
            
        Raises:
            NotFoundError: If vendor not found
        """
        return self.repository.get(vendor_id)
    
    def update_vendor(
        self,
        vendor_id: int,
        data: VendorUpdate,
        actor_id: int
    ) -> Vendor:
        """
        Update vendor.
        
        Args:
            vendor_id: Vendor ID
            data: Update data
            actor_id: ID of user updating
            
        Returns:
            Updated Vendor instance
        """
        vendor = self.get_vendor(vendor_id)
        
        # Capture old state for audit
        old_state = {
            "name": vendor.name,
            "email": vendor.email,
            "rating": float(vendor.rating) if vendor.rating else 0
        }
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        
        if "email" in update_data:
            if update_data["email"] != vendor.email:
                if self.repository.exists_by_email(update_data["email"]):
                    raise ConflictError("Email already in use")
        
        vendor = self.repository.update(vendor_id, update_data)
        
        # Audit
        self.audit.record_event(
            entity_type="vendor",
            entity_id=vendor_id,
            action="updated",
            actor_id=actor_id,
            old_state=old_state,
            new_state={
                "name": vendor.name,
                "email": vendor.email
            }
        )
        
        return vendor
    
    def deactivate_vendor(
        self,
        vendor_id: int,
        actor_id: int,
        reason: str
    ) -> Vendor:
        """
        Deactivate a vendor.
        
        Args:
            vendor_id: Vendor ID
            actor_id: ID of user deactivating
            reason: Reason for deactivation
            
        Returns:
            Deactivated Vendor instance
        """
        ValidationEngine.validate_reason_required(reason, "deactivation")
        
        vendor = self.get_vendor(vendor_id)
        
        old_state = {"is_active": vendor.is_active}
        
        vendor.is_active = False
        vendor.status = "inactive"
        self.session.flush()
        
        # Audit
        self.audit.record_event(
            entity_type="vendor",
            entity_id=vendor_id,
            action="deactivated",
            actor_id=actor_id,
            old_state=old_state,
            new_state={"is_active": False, "status": "inactive"},
            reason=reason
        )
        
        return vendor
    
    def search_vendors(
        self,
        query: str,
        limit: int = 20
    ) -> List[Vendor]:
        """
        Search vendors.
        
        Args:
            query: Search string
            limit: Maximum results
            
        Returns:
            List of matching vendors
        """
        return self.repository.search(query, limit)
    
    def get_active_vendors(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Vendor]:
        """
        Get all active vendors.
        
        Args:
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of active vendors
        """
        return self.repository.get_active_vendors(limit, offset)
    
    def get_preferred_vendors(
        self,
        limit: int = 50
    ) -> List[Vendor]:
        """
        Get preferred vendors.
        
        Args:
            limit: Maximum results
            
        Returns:
            List of preferred vendors
        """
        return self.repository.get_preferred_vendors(limit)

