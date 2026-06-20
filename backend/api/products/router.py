"""Product API router."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.products.service import ProductService
from backend.api.products.schemas import ProductCreate, ProductUpdate, ProductResponse, BOMResponse, RoutingResponse
from backend.core.database import get_db


router = APIRouter(prefix="/products", tags=["Products"])


def get_service(session: Async: Session) -> ProductService:
    """Get product service instance."""
    return ProductService(session)


@router.post("", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    service: ProductService = Depends(get_service),
):
    """Create a new product."""
    # Use actor_id=1 for now (should come from JWT token)
    return await service.create_product(data, actor_id=1)


@router.get("", response_model=List[ProductResponse])
async def list_products(
    search: Optional[str] = Query(None),
    product_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    service: ProductService = Depends(get_service),
):
    """List products with filters."""
    return await service.list_products(
        search=search,
        product_type=product_type,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int = Path(...),
    service: ProductService = Depends(get_service),
):
    """Get product by ID."""
    return await service.get_product(product_id)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int = Path(...),
    data: ProductUpdate = Body(...),
    service: ProductService = Depends(get_service),
):
    """Update product."""
    return await service.update_product(product_id, data, actor_id=1)


@router.delete("/{product_id}", response_model=ProductResponse)
async def deactivate_product(
    product_id: int = Path(...),
    service: ProductService = Depends(get_service),
):
    """Deactivate product (soft delete)."""
    return await service.deactivate_product(product_id, actor_id=1)


@router.get("/{product_id}/bom", response_model=Optional[BOMResponse])
async def get_product_bom(
    product_id: int = Path(...),
    service: ProductService = Depends(get_service),
):
    """Get active BOM for a product."""
    return await service.get_bom(product_id)


@router.post("/{product_id}/bom", response_model=BOMResponse)
async def create_product_bom(
    product_id: int = Path(...),
    components: List[Dict[str, Any]] = Body(...),
    version: str = Body("1.0"),
    service: ProductService = Depends(get_service),
):
    """Create BOM for a product."""
    return await service.create_bom(product_id, components, actor_id=1, version=version)


@router.get("/{product_id}/routing", response_model=Optional[RoutingResponse])
async def get_product_routing(
    product_id: int = Path(...),
    service: ProductService = Depends(get_service),
):
    """Get active routing for a product."""
    return await service.get_routing(product_id)


@router.post("/{product_id}/routing", response_model=RoutingResponse)
async def create_product_routing(
    product_id: int = Path(...),
    operations: List[Dict[str, Any]] = Body(...),
    service: ProductService = Depends(get_service),
):
    """Create routing for a product."""
    return await service.create_routing(product_id, operations, actor_id=1)
