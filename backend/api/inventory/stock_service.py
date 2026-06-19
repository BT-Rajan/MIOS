"""
Stock service for MIOS.

Business logic layer for stock management.
All operations are audited and use shared engines.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from backend.shared.audit.engine import AuditEngine
from backend.shared.events.engine import EventBus
from backend.shared.permissions.engine import PermissionEngine
from backend.shared.models.inventory import StockMovementType

from backend.api.inventory.repository import InventoryRepository
from backend.api.inventory.validators import InventoryValidators
from backend.api.inventory.exceptions import (
    WarehouseNotFound,
    StockItemNotFound,
    InsufficientStock,
    NegativeStockError,
)


class StockService:
    """
    Service layer for stock operations.
    
    All business logic for stock management resides here.
    Uses repository pattern for data access.
    All operations are audited.
    """
    
    def __init__(
        self,
        session: Session,
        audit_engine: AuditEngine,
        event_bus: EventBus,
        permission_engine: PermissionEngine
    ):
        self.session = session
        self.repository = InventoryRepository(session)
        self.audit = audit_engine
        self.event_bus = event_bus
        self.permissions = permission_engine
    
    def receive_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: Decimal,
        unit_cost: Optional[Decimal] = None,
        reason: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Receive stock into warehouse."""
        if not self.permissions.can(user_id, "receive_stock"):
            raise PermissionError("User cannot receive stock")
        
        valid, error = InventoryValidators.validate_stock_movement(
            "receipt", quantity, reason
        )
        if not valid:
            raise ValueError(error)
        
        warehouse = self.repository.get_warehouse(warehouse_id)
        if not warehouse:
            raise WarehouseNotFound(warehouse_id)
        
        stock_item = self.repository.get_or_create_stock_item(
            product_id, warehouse_id
        )
        
        old_quantity = stock_item.quantity_on_hand
        
        stock_item.quantity_on_hand += quantity
        stock_item.quantity_available = (
            stock_item.quantity_on_hand - stock_item.quantity_reserved
        )
        if unit_cost:
            stock_item.unit_cost = unit_cost
        
        self.session.flush()
        
        total_value = quantity * unit_cost if unit_cost else None
        movement = self.repository.create_movement({
            "warehouse_id": warehouse_id,
            "stock_item_id": stock_item.id,
            "product_id": product_id,
            "movement_type": StockMovementType.RECEIPT,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "total_value": total_value,
            "reason": reason,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "performed_by": user_id
        })
        
        self.audit.record_event(
            entity="stock_movement",
            entity_id=movement.id,
            action="receipt",
            old_state={"quantity": str(old_quantity)},
            new_state={"quantity": str(stock_item.quantity_on_hand)},
            actor_id=user_id,
            reason=reason
        )
        
        self.event_bus.publish("stock_received", {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "quantity": str(quantity),
            "movement_id": movement.id
        })
        
        return self._movement_to_dict(movement)
    
    def issue_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: Decimal,
        reason: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Issue stock from warehouse."""
        if not self.permissions.can(user_id, "issue_stock"):
            raise PermissionError("User cannot issue stock")
        
        valid, error = InventoryValidators.validate_stock_movement(
            "issue", quantity, reason
        )
        if not valid:
            raise ValueError(error)
        
        stock_item = self.repository.get_stock_item(product_id, warehouse_id)
        if not stock_item:
            raise StockItemNotFound(product_id, warehouse_id)
        
        if quantity > stock_item.quantity_available:
            raise InsufficientStock(
                product_id=product_id,
                warehouse_id=warehouse_id,
                requested=float(quantity),
                available=float(stock_item.quantity_available)
            )
        
        old_quantity = stock_item.quantity_on_hand
        
        stock_item.quantity_on_hand -= quantity
        stock_item.quantity_available = (
            stock_item.quantity_on_hand - stock_item.quantity_reserved
        )
        
        self.session.flush()
        
        movement = self.repository.create_movement({
            "warehouse_id": warehouse_id,
            "stock_item_id": stock_item.id,
            "product_id": product_id,
            "movement_type": StockMovementType.ISSUE,
            "quantity": quantity,
            "unit_cost": stock_item.unit_cost,
            "total_value": (
                quantity * stock_item.unit_cost
                if stock_item.unit_cost else None
            ),
            "reason": reason,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "performed_by": user_id
        })
        
        self.audit.record_event(
            entity="stock_movement",
            entity_id=movement.id,
            action="issue",
            old_state={"quantity": str(old_quantity)},
            new_state={"quantity": str(stock_item.quantity_on_hand)},
            actor_id=user_id,
            reason=reason
        )
        
        self.event_bus.publish("stock_issued", {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "quantity": str(quantity),
            "movement_id": movement.id
        })
        
        return self._movement_to_dict(movement)
    
    def adjust_stock(
        self,
        product_id: int,
        warehouse_id: int,
        quantity: Decimal,
        reason: str,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Adjust stock (positive or negative)."""
        if not self.permissions.can(user_id, "adjust_stock"):
            raise PermissionError("User cannot adjust stock")
        
        if not reason:
            raise ValueError("Reason required for stock adjustments")
        
        stock_item = self.repository.get_stock_item(product_id, warehouse_id)
        if not stock_item:
            raise StockItemNotFound(product_id, warehouse_id)
        
        old_quantity = stock_item.quantity_on_hand
        new_quantity = old_quantity + quantity
        
        if new_quantity < 0:
            raise NegativeStockError(product_id, warehouse_id)
        
        stock_item.quantity_on_hand = new_quantity
        stock_item.quantity_available = (
            stock_item.quantity_on_hand - stock_item.quantity_reserved
        )
        
        self.session.flush()
        
        movement = self.repository.create_movement({
            "warehouse_id": warehouse_id,
            "stock_item_id": stock_item.id,
            "product_id": product_id,
            "movement_type": StockMovementType.ADJUSTMENT,
            "quantity": abs(quantity),
            "unit_cost": stock_item.unit_cost,
            "total_value": (
                abs(quantity) * stock_item.unit_cost
                if stock_item.unit_cost else None
            ),
            "reason": reason,
            "performed_by": user_id
        })
        
        self.audit.record_event(
            entity="stock_movement",
            entity_id=movement.id,
            action="adjustment",
            old_state={"quantity": str(old_quantity)},
            new_state={"quantity": str(new_quantity)},
            actor_id=user_id,
            reason=reason
        )
        
        self.event_bus.publish("stock_adjusted", {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "quantity": str(quantity),
            "movement_id": movement.id
        })
        
        return self._movement_to_dict(movement)
    
    def get_stock_level(
        self,
        product_id: int,
        warehouse_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get current stock level for a product."""
        if warehouse_id:
            stock_item = self.repository.get_stock_item(
                product_id, warehouse_id
            )
            if not stock_item:
                return {
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "quantity_on_hand": Decimal("0"),
                    "quantity_reserved": Decimal("0"),
                    "quantity_available": Decimal("0")
                }
            return {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity_on_hand": stock_item.quantity_on_hand,
                "quantity_reserved": stock_item.quantity_reserved,
                "quantity_available": stock_item.quantity_available
            }
        else:
            summary = self.repository.get_inventory_summary(product_id)
            if summary:
                return {
                    "product_id": product_id,
                    "quantity_on_hand": Decimal(
                        str(summary[0]["total_on_hand"])
                    ),
                    "quantity_reserved": Decimal(
                        str(summary[0]["total_reserved"])
                    ),
                    "quantity_available": Decimal(
                        str(summary[0]["total_available"])
                    )
                }
            return {
                "product_id": product_id,
                "quantity_on_hand": Decimal("0"),
                "quantity_reserved": Decimal("0"),
                "quantity_available": Decimal("0")
            }
    
    def get_stock_movements(
        self,
        product_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get stock movement history."""
        movements = self.repository.list_movements(
            product_id=product_id,
            warehouse_id=warehouse_id,
            reference_type=reference_type,
            reference_id=reference_id,
            skip=skip,
            limit=limit
        )
        return [self._movement_to_dict(m) for m in movements]
    
    def _movement_to_dict(self, movement) -> Dict[str, Any]:
        """Convert movement model to dictionary."""
        return {
            "id": movement.id,
            "warehouse_id": movement.warehouse_id,
            "product_id": movement.product_id,
            "movement_type": movement.movement_type.value,
            "quantity": movement.quantity,
            "unit_cost": movement.unit_cost,
            "total_value": movement.total_value,
            "reason": movement.reason,
            "reference_type": movement.reference_type,
            "reference_id": movement.reference_id,
            "performed_by": movement.performed_by,
            "created_at": movement.created_at
        }
