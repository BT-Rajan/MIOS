"""
Vendor API router.

HTTP endpoints for vendor operations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.api.vendors.schemas import VendorCreate, VendorUpdate, VendorResponse
from backend.api.vendors.service import VendorService


router = APIRouter(prefix="/vendors", tags=["vendors"])


def get_service(db: : Session) -> VendorService:
    """Get vendor service instance."""
    return VendorService(db)


@router.post("/", response_model=VendorResponse, status_code=201)
def create_vendor(
    data: VendorCreate,
    service: VendorService = Depends(get_service)
):
    """Create a new vendor."""
    # TODO: Get actor_id from authenticated user
    actor_id = 1
    return service.create_vendor(data, actor_id)


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: int,
    service: VendorService = Depends(get_service)
):
    """Get vendor by ID."""
    try:
        return service.get_vendor(vendor_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: int,
    data: VendorUpdate,
    service: VendorService = Depends(get_service)
):
    """Update vendor."""
    # TODO: Get actor_id from authenticated user
    actor_id = 1
    try:
        return service.update_vendor(vendor_id, data, actor_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{vendor_id}")
def deactivate_vendor(
    vendor_id: int,
    reason: str = Query(..., min_length=10),
    service: VendorService = Depends(get_service)
):
    """Deactivate a vendor (soft delete)."""
    # TODO: Get actor_id from authenticated user
    actor_id = 1
    try:
        return service.deactivate_vendor(vendor_id, actor_id, reason)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search", response_model=List[VendorResponse])
def search_vendors(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, le=100),
    service: VendorService = Depends(get_service)
):
    """Search vendors by name or code."""
    return service.search_vendors(q, limit)


@router.get("/", response_model=List[VendorResponse])
def list_active_vendors(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    service: VendorService = Depends(get_service)
):
    """List all active vendors."""
    return service.get_active_vendors(limit, offset)


@router.get("/preferred", response_model=List[VendorResponse])
def list_preferred_vendors(
    limit: int = Query(default=20, le=50),
    service: VendorService = Depends(get_service)
):
    """List preferred vendors."""
    return service.get_preferred_vendors(limit)

