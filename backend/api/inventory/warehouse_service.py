"""
Warehouse service for MIOS.

Business logic layer for warehouse management.
All operations are audited and use shared engines.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy.orm import Session

from backend.shared.audit import AuditEngine
from backend.shared.events.engine import EventBus
from backend.shared.permissions.engine import PermissionEngine

from backend.api.inventory.repository import InventoryRepository
from backend.api.inventory.validators import InventoryValidators
from backend.api.inventory.exceptions import WarehouseNotFound


class WarehouseService:
    """
    Service layer for warehouse operations.
    
    All business logic for warehouse management resides here.
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
    
    def create_warehouse(
        self,
        code: str,
        name: str,
        address: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        is_default: bool = False,
        user_id: int = None
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
            "code": code,
            "name": name,
            "address": address,
            "city": city,
            "country": country,
            "is_active": True,
            "is_default": is_default
        }
        
        warehouse = self.repository.create_warehouse(data)
        
        self.audit.record_event(
            entity="warehouse",
            entity_id=warehouse.id,
            action="created",
            old_state=None,
            new_state=data,
            actor_id=user_id
        )
        
        self.event_bus.publish("warehouse_created", {
            "warehouse_id": warehouse.id,
            "code": warehouse.code
        })
        
        return self._warehouse_to_dict(warehouse)
    
    def get_warehouse(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        """Get warehouse by ID."""
        warehouse = self.repository.get_warehouse(warehouse_id)
        if not warehouse:
            return None
        return self._warehouse_to_dict(warehouse)
    
    def list_warehouses(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List all warehouses."""
        warehouses = self.repository.list_warehouses(
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        return [self._warehouse_to_dict(w) for w in warehouses]
    
    def update_warehouse(
        self,
        warehouse_id: int,
        name: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_default: Optional[bool] = None,
        user_id: int = None
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
        
        if address is not None:
            update_data["address"] = address
        if city is not None:
            update_data["city"] = city
        if country is not None:
            update_data["country"] = country
        if is_active is not None:
            update_data["is_active"] = is_active
        
        if is_default is not None and is_default:
            self._clear_default_warehouse(exclude_id=warehouse_id)
            update_data["is_default"] = True
        
        warehouse = self.repository.update_warehouse(warehouse_id, update_data)
        
        new_state = self._warehouse_to_dict(warehouse)
        self.audit.record_event(
            entity="warehouse",
            entity_id=warehouse_id,
            action="updated",
            old_state=old_state,
            new_state=new_state,
            actor_id=user_id
        )
        
        return new_state
    
    def _validate_warehouse_data(
        self, code: str, name: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate warehouse creation data."""
        result = InventoryValidators.validate_warehouse_code(code)
        if not result.valid:
            return False, result.error
        
        result = InventoryValidators.validate_warehouse_name(name)
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
            "id": warehouse.id,
            "code": warehouse.code,
            "name": warehouse.name,
            "address": warehouse.address,
            "city": warehouse.city,
            "country": warehouse.country,
            "is_active": warehouse.is_active,
            "is_default": warehouse.is_default,
            "created_at": warehouse.created_at,
            "updated_at": warehouse.updated_at
        }
