"""
Customer API router.

HTTP endpoints for customer operations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.api.customers.schemas import CustomerCreate, CustomerUpdate, CustomerResponse
from backend.api.customers.service import CustomerService


router = APIRouter(prefix="/customers", tags=["customers"])


def get_service(db: : Session) -> CustomerService:
    """Get customer service instance."""
    return CustomerService(db)


@router.post("/", response_model=CustomerResponse, status_code=201)
def create_customer(
    data: CustomerCreate,
    service: CustomerService = Depends(get_service)
):
    """Create a new customer."""
    # TODO: Get actor_id from authenticated user
    actor_id = 1
    return service.create_customer(data, actor_id)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    service: CustomerService = Depends(get_service)
):
    """Get customer by ID."""
    try:
        return service.get_customer(customer_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    service: CustomerService = Depends(get_service)
):
    """Update customer."""
    # TODO: Get actor_id from authenticated user
    actor_id = 1
    try:
        return service.update_customer(customer_id, data, actor_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{customer_id}")
def deactivate_customer(
    customer_id: int,
    reason: str = Query(..., min_length=10),
    service: CustomerService = Depends(get_service)
):
    """Deactivate a customer (soft delete)."""
    # TODO: Get actor_id from authenticated user
    actor_id = 1
    try:
        return service.deactivate_customer(customer_id, actor_id, reason)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search", response_model=List[CustomerResponse])
def search_customers(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, le=100),
    service: CustomerService = Depends(get_service)
):
    """Search customers by name or code."""
    return service.search_customers(q, limit)


@router.get("/", response_model=List[CustomerResponse])
def list_active_customers(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    service: CustomerService = Depends(get_service)
):
    """List all active customers."""
    return service.get_active_customers(limit, offset)
