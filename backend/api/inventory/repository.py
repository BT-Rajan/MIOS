"""
Inventory repository for MIOS.

Data access layer for inventory operations.
All database queries go through this repository.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from backend.shared.models.inventory import (
    Warehouse,
    StockItem,
    StockMovement,
    StockReservation,
    StockMovementType,
)
from backend.api.inventory.exceptions import (
    WarehouseNotFound,
    WarehouseCodeExists,
    StockItemNotFound,
    ReservationNotFound,
)


class InventoryRepository:
    """Repository for inventory data access."""
    
    def __init__(self, session: Session):
        self.session = session
    
    # Warehouse operations
    
    def get_warehouse(self, warehouse_id: int) -> Optional[Warehouse]:
        """Get warehouse by ID."""
        return self.session.get(Warehouse, warehouse_id)
    
    def get_warehouse_by_code(self, code: str) -> Optional[Warehouse]:
        """Get warehouse by code."""
        stmt = select(Warehouse).where(Warehouse.code == code.upper())
        return self.session.scalar(stmt)
    
    def list_warehouses(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Warehouse]:
        """List warehouses with optional filtering."""
        stmt = select(Warehouse)
        
        if is_active is not None:
            stmt = stmt.where(Warehouse.is_active == is_active)
        
        stmt = stmt.offset(skip).limit(limit)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    def create_warehouse(self, data: Dict[str, Any]) -> Warehouse:
        """Create a new warehouse."""
        try:
            warehouse = Warehouse(**data)
            self.session.add(warehouse)
            self.session.flush()
            return warehouse
        except IntegrityError as e:
            if "warehouses_code_key" in str(e.orig):
                raise WarehouseCodeExists(data.get("code", ""))
            raise
    
    def update_warehouse(
        self,
        warehouse_id: int,
        data: Dict[str, Any]
    ) -> Optional[Warehouse]:
        """Update an existing warehouse."""
        warehouse = self.get_warehouse(warehouse_id)
        if not warehouse:
            return None
        
        for key, value in data.items():
            if hasattr(warehouse, key) and value is not None:
                setattr(warehouse, key, value)
        
        self.session.flush()
        return warehouse
    
    def delete_warehouse(self, warehouse_id: int) -> bool:
        """Soft delete a warehouse."""
        warehouse = self.get_warehouse(warehouse_id)
        if not warehouse:
            return False
        
        warehouse.is_active = False
        self.session.flush()
        return True
    
    # Stock Item operations
    
    def get_stock_item(
        self,
        product_id: int,
        warehouse_id: int
    ) -> Optional[StockItem]:
        """Get stock item by product and warehouse."""
        stmt = select(StockItem).where(
            StockItem.product_id == product_id,
            StockItem.warehouse_id == warehouse_id
        )
        return self.session.scalar(stmt)
    
    def get_stock_item_by_id(self, stock_item_id: int) -> Optional[StockItem]:
        """Get stock item by ID."""
        return self.session.get(StockItem, stock_item_id)
    
    def get_or_create_stock_item(
        self,
        product_id: int,
        warehouse_id: int
    ) -> StockItem:
        """Get existing stock item or create new one."""
        stock_item = self.get_stock_item(product_id, warehouse_id)
        
        if not stock_item:
            stock_item = StockItem(
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity_on_hand=Decimal("0"),
                quantity_reserved=Decimal("0"),
                quantity_available=Decimal("0")
            )
            self.session.add(stock_item)
            self.session.flush()
        
        return stock_item
    
    def list_stock_items(
        self,
        warehouse_id: Optional[int] = None,
        product_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StockItem]:
        """List stock items with optional filtering."""
        stmt = select(StockItem).options(
            joinedload(StockItem.product),
            joinedload(StockItem.warehouse)
        )
        
        if warehouse_id is not None:
            stmt = stmt.where(StockItem.warehouse_id == warehouse_id)
        if product_id is not None:
            stmt = stmt.where(StockItem.product_id == product_id)
        
        stmt = stmt.offset(skip).limit(limit)
        result = self.session.execute(stmt)
        return list(result.scalars().unique().all())
    
    def update_stock_item(
        self,
        stock_item_id: int,
        data: Dict[str, Any]
    ) -> Optional[StockItem]:
        """Update stock item quantities."""
        stock_item = self.get_stock_item_by_id(stock_item_id)
        if not stock_item:
            return None
        
        for key, value in data.items():
            if hasattr(stock_item, key) and value is not None:
                setattr(stock_item, key, value)
        
        # Recalculate available quantity
        stock_item.quantity_available = (
            stock_item.quantity_on_hand - stock_item.quantity_reserved
        )
        
        self.session.flush()
        return stock_item
    
    # Stock Movement operations
    
    def create_movement(self, data: Dict[str, Any]) -> StockMovement:
        """Create a stock movement record."""
        movement = StockMovement(**data)
        self.session.add(movement)
        self.session.flush()
        return movement
    
    def list_movements(
        self,
        product_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StockMovement]:
        """List stock movements with filtering."""
        stmt = select(StockMovement).options(
            joinedload(StockMovement.product),
            joinedload(StockMovement.warehouse)
        )
        
        if product_id is not None:
            stmt = stmt.where(StockMovement.product_id == product_id)
        if warehouse_id is not None:
            stmt = stmt.where(StockMovement.warehouse_id == warehouse_id)
        if reference_type is not None:
            stmt = stmt.where(StockMovement.reference_type == reference_type)
        if reference_id is not None:
            stmt = stmt.where(StockMovement.reference_id == reference_id)
        
        stmt = stmt.order_by(StockMovement.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        
        result = self.session.execute(stmt)
        return list(result.scalars().unique().all())
    
    # Stock Reservation operations
    
    def get_reservation(self, reservation_id: int) -> Optional[StockReservation]:
        """Get reservation by ID."""
        return self.session.get(StockReservation, reservation_id)
    
    def create_reservation(self, data: Dict[str, Any]) -> StockReservation:
        """Create a stock reservation."""
        reservation = StockReservation(**data)
        self.session.add(reservation)
        self.session.flush()
        return reservation
    
    def update_reservation(
        self,
        reservation_id: int,
        data: Dict[str, Any]
    ) -> Optional[StockReservation]:
        """Update a stock reservation."""
        reservation = self.get_reservation(reservation_id)
        if not reservation:
            return None
        
        for key, value in data.items():
            if hasattr(reservation, key) and value is not None:
                setattr(reservation, key, value)
        
        self.session.flush()
        return reservation
    
    def get_active_reservations(
        self,
        reference_type: str,
        reference_id: int
    ) -> List[StockReservation]:
        """Get active reservations for a reference."""
        stmt = select(StockReservation).where(
            StockReservation.reference_type == reference_type,
            StockReservation.reference_id == reference_id,
            StockReservation.status == "active"
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
    
    def cancel_reservation(self, reservation_id: int) -> bool:
        """Cancel a stock reservation."""
        reservation = self.get_reservation(reservation_id)
        if not reservation:
            return False
        
        reservation.status = "cancelled"
        self.session.flush()
        return True
    
    # Inventory summary queries
    
    def get_inventory_summary(
        self,
        product_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get inventory summary across all warehouses."""
        stmt = select(
            StockItem.product_id,
            func.sum(StockItem.quantity_on_hand).label("total_on_hand"),
            func.sum(StockItem.quantity_reserved).label("total_reserved"),
            func.sum(StockItem.quantity_available).label("total_available")
        ).group_by(StockItem.product_id)
        
        if product_id is not None:
            stmt = stmt.where(StockItem.product_id == product_id)
        
        result = self.session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]
