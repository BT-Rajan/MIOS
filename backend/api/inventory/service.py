"""
Inventory service for MIOS.

Business logic layer for inventory operations.
All operations are audited and use shared engines.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from backend.shared.audit.engine import AuditEngine
from backend.shared.events.engine import EventBus
from backend.shared.permissions.engine import PermissionEngine

from backend.api.inventory.repository import InventoryRepository
from backend.api.inventory.validators import InventoryValidators
from backend.api.inventory.exceptions import (
    WarehouseNotFound,
    StockItemNotFound,
    InsufficientStock,
    ReservationNotFound,
)


class InventoryService:
    """Service layer for inventory operations."""
    
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
    
    def create_warehouse(
        self, code: str, name: str, address: Optional[str] = None,
        city: Optional[str] = None, country: Optional[str] = None,
        is_default: bool = False, user_id: int = None
    ) -> Dict[str, Any]:
        """Create a new warehouse."""
        if not self.permissions.can(user_id, "create_warehouse"):
            raise PermissionError("User cannot create warehouses")
        
        valid, error = self._validate_warehouse_data(code, name)
        if not valid:
            raise ValueError(error)
        
        if is_default:
            self._clear_default_warehouse()
        
        data = {
            "code": code, "name": name, "address": address,
            "city": city, "country": country,
            "is_active": True, "is_default": is_default
        }
        
        warehouse = self.repository.create_warehouse(data)
        self.audit.record_event(
            entity="warehouse", entity_id=warehouse.id,
            action="created", old_state=None, new_state=data, actor_id=user_id
        )
        self.event_bus.publish("warehouse_created", {
            "warehouse_id": warehouse.id, "code": warehouse.code
        })
        return self._warehouse_to_dict(warehouse)
    
    def get_warehouse(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        """Get warehouse by ID."""
        warehouse = self.repository.get_warehouse(warehouse_id)
        return self._warehouse_to_dict(warehouse) if warehouse else None
    
    def list_warehouses(
        self, is_active: Optional[bool] = None,
        skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List all warehouses."""
        warehouses = self.repository.list_warehouses(
            is_active=is_active, skip=skip, limit=limit
        )
        return [self._warehouse_to_dict(w) for w in warehouses]
    
    def update_warehouse(
        self, warehouse_id: int, name: Optional[str] = None,
        address: Optional[str] = None, city: Optional[str] = None,
        country: Optional[str] = None, is_active: Optional[bool] = None,
        is_default: Optional[bool] = None, user_id: int = None
    ) -> Optional[Dict[str, Any]]:
        """Update warehouse details."""
        if not self.permissions.can(user_id, "update_warehouse"):
            raise PermissionError("User cannot update warehouses")
        
        warehouse = self.repository.get_warehouse(warehouse_id)
        if not warehouse:
            raise WarehouseNotFound(warehouse_id)
        
        old_state = self._warehouse_to_dict(warehouse)
        update_data = {}
        
        if name is not None:
            valid, error = InventoryValidators.validate_warehouse_name(name)
            if not valid:
                raise ValueError(error)
            update_data["name"] = name
        
        for field in ["address", "city", "country"]:
            if locals().get(field) is not None:
                update_data[field] = locals()[field]
        if is_active is not None:
            update_data["is_active"] = is_active
        
        if is_default is not None and is_default:
            self._clear_default_warehouse(exclude_id=warehouse_id)
            update_data["is_default"] = True
        
        warehouse = self.repository.update_warehouse(warehouse_id, update_data)
        new_state = self._warehouse_to_dict(warehouse)
        self.audit.record_event(
            entity="warehouse", entity_id=warehouse_id,
            action="updated", old_state=old_state, new_state=new_state,
            actor_id=user_id
        )
        return new_state
    
    def delete_warehouse(self, warehouse_id: int, user_id: int = None) -> bool:
        """Soft delete a warehouse."""
        if not self.permissions.can(user_id, "delete_warehouse"):
            raise PermissionError("User cannot delete warehouses")
        
        warehouse = self.repository.get_warehouse(warehouse_id)
        if not warehouse:
            return False
        
        old_state = self._warehouse_to_dict(warehouse)
        success = self.repository.delete_warehouse(warehouse_id)
        
        if success:
            self.audit.record_event(
                entity="warehouse", entity_id=warehouse_id,
                action="deleted", old_state=old_state,
                new_state={"is_active": False}, actor_id=user_id
            )
            self.event_bus.publish("warehouse_deleted", {
                "warehouse_id": warehouse_id
            })
        return success
    
    def _validate_warehouse_data(self, code: str, name: str) -> tuple[bool, Optional[str]]:
        """Validate warehouse creation data."""
        for validator_func, value in [
            (InventoryValidators.validate_warehouse_code, code),
            (InventoryValidators.validate_warehouse_name, name)
        ]:
            result = validator_func(value)
            if not result.valid:
                return False, result.error
        return True, None
    
    def _clear_default_warehouse(self, exclude_id: Optional[int] = None):
        """Clear default flag from all warehouses."""
        warehouses = self.repository.list_warehouses(is_active=True)
        for warehouse in warehouses:
            if exclude_id and warehouse.id == exclude_id:
                continue
            if warehouse.is_default:
                self.repository.update_warehouse(
                    warehouse.id, {"is_default": False}
                )
    
    def _warehouse_to_dict(self, warehouse) -> Dict[str, Any]:
        """Convert warehouse model to dictionary."""
        return {
            "id": warehouse.id, "code": warehouse.code,
            "name": warehouse.name, "address": warehouse.address,
            "city": warehouse.city, "country": warehouse.country,
            "is_active": warehouse.is_active, "is_default": warehouse.is_default,
            "created_at": warehouse.created_at, "updated_at": warehouse.updated_at
        }
    
    def get_stock_level(
        self, product_id: int, warehouse_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get current stock level for a product."""
        if warehouse_id:
            stock_item = self.repository.get_stock_item(product_id, warehouse_id)
            if not stock_item:
                return {
                    "product_id": product_id, "warehouse_id": warehouse_id,
                    "quantity_on_hand": Decimal("0"),
                    "quantity_reserved": Decimal("0"),
                    "quantity_available": Decimal("0")
                }
            return {
                "product_id": product_id, "warehouse_id": warehouse_id,
                "quantity_on_hand": stock_item.quantity_on_hand,
                "quantity_reserved": stock_item.quantity_reserved,
                "quantity_available": stock_item.quantity_available
            }
        else:
            summary = self.repository.get_inventory_summary(product_id)
            if summary:
                return {
                    "product_id": product_id,
                    "quantity_on_hand": Decimal(str(summary[0]["total_on_hand"])),
                    "quantity_reserved": Decimal(str(summary[0]["total_reserved"])),
                    "quantity_available": Decimal(str(summary[0]["total_available"]))
                }
            return {
                "product_id": product_id,
                "quantity_on_hand": Decimal("0"),
                "quantity_reserved": Decimal("0"),
                "quantity_available": Decimal("0")
            }
    
    def get_inventory_summary(
        self, product_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get inventory summary across all warehouses."""
        return self.repository.get_inventory_summary(product_id)
    
    def _movement_to_dict(self, movement) -> Dict[str, Any]:
        """Convert movement model to dictionary."""
        return {
            "id": movement.id, "warehouse_id": movement.warehouse_id,
            "product_id": movement.product_id,
            "movement_type": movement.movement_type.value if hasattr(movement.movement_type, 'value') else str(movement.movement_type),
            "quantity": movement.quantity, "unit_cost": movement.unit_cost,
            "total_value": movement.total_value, "reason": movement.reason,
            "reference_type": movement.reference_type,
            "reference_id": movement.reference_id,
            "performed_by": movement.performed_by,
            "created_at": movement.created_at
        }
    
    def _reservation_to_dict(self, reservation) -> Dict[str, Any]:
        """Convert reservation model to dictionary."""
        return {
            "id": reservation.id, "stock_item_id": reservation.stock_item_id,
            "product_id": reservation.product_id,
            "warehouse_id": reservation.warehouse_id,
            "quantity": reservation.quantity,
            "reference_type": reservation.reference_type,
            "reference_id": reservation.reference_id,
            "reference_line_id": reservation.reference_line_id,
            "status": reservation.status, "expires_at": reservation.expires_at,
            "notes": reservation.notes, "created_at": reservation.created_at,
            "updated_at": reservation.updated_at,
            "created_by": reservation.created_by
        }
