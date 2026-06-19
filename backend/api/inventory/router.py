"""
Inventory router for MIOS.

FastAPI router for inventory management endpoints.
All business logic delegated to service layer.
"""
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.database import get_session
from backend.shared.audit.engine import AuditEngine
from backend.shared.events.engine import EventBus
from backend.shared.permissions.engine import PermissionEngine
from backend.shared.models.inventory import StockMovementType

from backend.api.inventory.schemas import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
    StockItemResponse,
    StockMovementCreate,
    StockMovementResponse,
    StockReservationCreate,
    StockReservationUpdate,
    StockReservationResponse,
    InventorySummary,
)
from backend.api.inventory.service import InventoryService
from backend.api.inventory.exceptions import (
    WarehouseNotFound,
    StockItemNotFound,
    InsufficientStock,
    ReservationNotFound,
)


router = APIRouter(prefix="/inventory", tags=["inventory"])


def get_inventory_service(
    db: Session = Depends(get_session),
    audit_engine: AuditEngine = Depends(AuditEngine),
    event_bus: EventBus = Depends(EventBus),
    permission_engine: PermissionEngine = Depends(PermissionEngine)
) -> InventoryService:
    """Get inventory service instance."""
    return InventoryService(
        session=db,
        audit_engine=audit_engine,
        event_bus=event_bus,
        permission_engine=permission_engine
    )


# Warehouse endpoints
@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    warehouse_data: WarehouseCreate,
    service: InventoryService = Depends(get_inventory_service),
    current_user_id: int = Query(..., description="Current user ID")
):
    """Create a new warehouse."""
    try:
        return service.create_warehouse(
            code=warehouse_data.code,
            name=warehouse_data.name,
            address=warehouse_data.address,
            city=warehouse_data.city,
            country=warehouse_data.country,
            is_default=warehouse_data.is_default,
            user_id=current_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(
    warehouse_id: int,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get warehouse by ID."""
    warehouse = service.get_warehouse(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse


@router.get("/warehouses", response_model=List[WarehouseResponse])
def list_warehouses(
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: InventoryService = Depends(get_inventory_service)
):
    """List all warehouses with optional filtering."""
    return service.list_warehouses(
        is_active=is_active,
        skip=skip,
        limit=limit
    )


@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int,
    warehouse_data: WarehouseUpdate,
    service: InventoryService = Depends(get_inventory_service),
    current_user_id: int = Query(..., description="Current user ID")
):
    """Update warehouse details."""
    try:
        result = service.update_warehouse(
            warehouse_id=warehouse_id,
            name=warehouse_data.name,
            address=warehouse_data.address,
            city=warehouse_data.city,
            country=warehouse_data.country,
            is_active=warehouse_data.is_active,
            is_default=warehouse_data.is_default,
            user_id=current_user_id
        )
        if not result:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        return result
    except WarehouseNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/warehouses/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(
    warehouse_id: int,
    service: InventoryService = Depends(get_inventory_service),
    current_user_id: int = Query(..., description="Current user ID")
):
    """Soft delete a warehouse."""
    try:
        success = service.delete_warehouse(warehouse_id, user_id=current_user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Warehouse not found")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# Stock level endpoints
@router.get("/stock/product/{product_id}")
def get_stock_level(
    product_id: int,
    warehouse_id: Optional[int] = Query(None),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get current stock level for a product."""
    return service.get_stock_level(product_id, warehouse_id)


@router.get("/stock/products/summary", response_model=List[InventorySummary])
def get_inventory_summary(
    product_id: Optional[int] = Query(None),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get inventory summary across all warehouses."""
    return service.get_inventory_summary(product_id)


# Stock movement endpoints
@router.post("/stock/movements", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
def create_stock_movement(
    movement_data: StockMovementCreate,
    service: InventoryService = Depends(get_inventory_service),
    current_user_id: int = Query(..., description="Current user ID")
):
    """Create a stock movement (receipt, issue, adjustment, etc.)."""
    try:
        if movement_data.movement_type == StockMovementType.RECEIPT:
            return service.receive_stock(
                product_id=movement_data.product_id,
                warehouse_id=movement_data.warehouse_id,
                quantity=movement_data.quantity,
                unit_cost=movement_data.unit_cost,
                reason=movement_data.reason,
                reference_type=movement_data.reference_type,
                reference_id=movement_data.reference_id,
                user_id=current_user_id
            )
        elif movement_data.movement_type == StockMovementType.ISSUE:
            return service.issue_stock(
                product_id=movement_data.product_id,
                warehouse_id=movement_data.warehouse_id,
                quantity=movement_data.quantity,
                reason=movement_data.reason,
                reference_type=movement_data.reference_type,
                reference_id=movement_data.reference_id,
                user_id=current_user_id
            )
        elif movement_data.movement_type == StockMovementType.ADJUSTMENT:
            return service.adjust_stock(
                product_id=movement_data.product_id,
                warehouse_id=movement_data.warehouse_id,
                quantity=movement_data.quantity,
                reason=movement_data.reason or "Manual adjustment",
                user_id=current_user_id
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Movement type '{movement_data.movement_type.value}' not supported via this endpoint"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InsufficientStock as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/stock/movements", response_model=List[StockMovementResponse])
def list_stock_movements(
    product_id: Optional[int] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    reference_type: Optional[str] = Query(None),
    reference_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get stock movement history with filtering."""
    return service.get_stock_movements(
        product_id=product_id,
        warehouse_id=warehouse_id,
        reference_type=reference_type,
        reference_id=reference_id,
        skip=skip,
        limit=limit
    )


# Stock reservation endpoints
@router.post("/stock/reservations", response_model=StockReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    reservation_data: StockReservationCreate,
    service: InventoryService = Depends(get_inventory_service),
    current_user_id: int = Query(..., description="Current user ID")
):
    """Create a stock reservation."""
    try:
        return service.create_reservation(
            product_id=reservation_data.product_id,
            warehouse_id=reservation_data.warehouse_id,
            quantity=reservation_data.quantity,
            reference_type=reservation_data.reference_type,
            reference_id=reservation_data.reference_id,
            reference_line_id=reservation_data.reference_line_id,
            expires_at=reservation_data.expires_at,
            notes=reservation_data.notes,
            user_id=current_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InsufficientStock as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/stock/reservations/{reservation_id}", response_model=StockReservationResponse)
def get_reservation(
    reservation_id: int,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get stock reservation by ID."""
    reservation = service.get_reservation(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation


@router.put("/stock/reservations/{reservation_id}", response_model=StockReservationResponse)
def update_reservation(
    reservation_id: int,
    reservation_data: StockReservationUpdate,
    service: InventoryService = Depends(get_inventory_service),
    current_user_id: int = Query(..., description="Current user ID")
):
    """Update stock reservation."""
    try:
        result = service.update_reservation(
            reservation_id=reservation_id,
            quantity=reservation_data.quantity,
            status=reservation_data.status,
            expires_at=reservation_data.expires_at,
            notes=reservation_data.notes,
            user_id=current_user_id
        )
        if not result:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return result
    except ReservationNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/stock/reservations/{reservation_id}/cancel", response_model=StockReservationResponse)
def cancel_reservation(
    reservation_id: int,
    service: InventoryService = Depends(get_inventory_service),
    current_user_id: int = Query(..., description="Current user ID")
):
    """Cancel a stock reservation."""
    try:
        result = service.cancel_reservation(reservation_id, user_id=current_user_id)
        if not result:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/stock/reservations/reference/{ref_type}/{ref_id}", response_model=List[StockReservationResponse])
def list_reservations_by_reference(
    ref_type: str,
    ref_id: int,
    service: InventoryService = Depends(get_inventory_service)
):
    """Get active reservations for a reference (e.g., sales order)."""
    return service.get_active_reservations(ref_type, ref_id)
