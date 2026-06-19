"""
Vendor repository for database operations.

All vendor data access goes through this repository.
"""

from typing import Optional, List

from sqlalchemy.orm import Session

from shared.repositories import BaseRepository
from api.vendors.models import Vendor


class VendorRepository(BaseRepository[Vendor]):
    """
    Repository for vendor entity operations.
    
    Provides centralized data access for all vendor-related queries.
    """
    
    def __init__(self, session: Session) -> None:
        super().__init__(model=Vendor, session=session)
    
    def get_by_code(self, code: str) -> Optional[Vendor]:
        """Get vendor by code."""
        return (
            self.session.query(Vendor)
            .filter(Vendor.code == code)
            .first()
        )
    
    def get_by_email(self, email: str) -> Optional[Vendor]:
        """Get vendor by email."""
        return (
            self.session.query(Vendor)
            .filter(Vendor.email == email)
            .first()
        )
    
    def search(
        self,
        query_string: str,
        limit: int = 20
    ) -> List[Vendor]:
        """Search vendors by name or code."""
        search_pattern = f"%{query_string}%"
        
        return (
            self.session.query(Vendor)
            .filter(
                Vendor.is_deleted == False,
                (Vendor.name.ilike(search_pattern)) |
                (Vendor.code.ilike(search_pattern))
            )
            .limit(limit)
            .all()
        )
    
    def get_active_vendors(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Vendor]:
        """Get all active vendors."""
        return (
            self.session.query(Vendor)
            .filter(
                Vendor.is_active == True,
                Vendor.is_deleted == False
            )
            .order_by(Vendor.name)
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def get_preferred_vendors(
        self,
        limit: int = 50
    ) -> List[Vendor]:
        """Get preferred vendors."""
        return (
            self.session.query(Vendor)
            .filter(
                Vendor.is_active == True,
                Vendor.is_preferred == True,
                Vendor.is_deleted == False
            )
            .order_by(Vendor.rating.desc())
            .limit(limit)
            .all()
        )
    
    def exists_by_email(self, email: str) -> bool:
        """Check if vendor exists by email."""
        return (
            self.session.query(Vendor)
            .filter(Vendor.email == email)
            .first() is not None
        )
    
    def exists_by_code(self, code: str) -> bool:
        """Check if vendor exists by code."""
        return (
            self.session.query(Vendor)
            .filter(Vendor.code == code)
            .first() is not None
        )

