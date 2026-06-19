"""Product service for business logic."""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.products.models import Product, BOMHeader, BOMItem
from backend.api.products.repository import ProductRepository, BOMHeaderRepository, BOMItemRepository
from backend.api.products.schemas import ProductCreate, ProductUpdate
from backend.api.products.exceptions import (
    ProductNotFoundException,
    ProductDuplicateCodeException,
    BOMNotFoundException,
)
from backend.api.products.validators import (
    validate_product_code,
    validate_product_name,
    validate_positive_quantity,
    validate_cost,
)
from backend.shared.audit import AuditEngine
from backend.shared.events import EventBus


class ProductService:
    """Service for Product operations."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._product_repo = ProductRepository(session)
        self._bom_header_repo = BOMHeaderRepository(session)
        self._bom_item_repo = BOMItemRepository(session)
        self._audit = AuditEngine()
        self._events = EventBus()

    async def create_product(self, data: ProductCreate, actor_id: int) -> Product:
        """Create a new product."""
        # Validate
        validate_product_code(data.code)
        validate_product_name(data.name)
        
        # Check duplicate
        existing = await self._product_repo.get_by_code(data.code)
        if existing:
            raise ProductDuplicateCodeException(data.code)

        # Create
        product = Product(
            code=data.code,
            name=data.name,
            description=data.description,
            unit_of_measure=data.unit_of_measure or "EA",
            product_type=data.product_type or "finished_good",
            standard_cost=data.standard_cost or 0.0,
            sale_price=data.sale_price or 0.0,
            is_active=True,
        )
        
        self._session.add(product)
        await self._session.flush()
        
        # Audit
        await self._audit.record_event(
            entity="product",
            entity_id=product.id,
            action="created",
            old_state=None,
            new_state=product.to_dict(),
            actor_id=actor_id,
            reason="Product creation",
        )
        
        return product

    async def get_product(self, product_id: int) -> Product:
        """Get product by ID."""
        product = await self._product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundException(product_id)
        return product

    async def list_products(
        self,
        search: Optional[str] = None,
        product_type: Optional[str] = None,
        is_active: Optional[bool] = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Product]:
        """List products with filters."""
        if search:
            return await self._product_repo.search(search, limit)
        
        # Basic listing
        query_filters = [Product.deleted_at.is_(None)]
        if product_type:
            query_filters.append(Product.product_type == product_type)
        if is_active is not None:
            query_filters.append(Product.is_active == is_active)
            
        return await self._product_repo.list(filters=query_filters, limit=limit, offset=offset)

    async def update_product(
        self,
        product_id: int,
        data: ProductUpdate,
        actor_id: int,
    ) -> Product:
        """Update product."""
        product = await self.get_product(product_id)
        
        old_state = product.to_dict()
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(product, field) and value is not None:
                setattr(product, field, value)
        
        await self._session.flush()
        
        # Audit
        await self._audit.record_event(
            entity="product",
            entity_id=product_id,
            action="updated",
            old_state=old_state,
            new_state=product.to_dict(),
            actor_id=actor_id,
            reason="Product update",
        )
        
        return product

    async def deactivate_product(self, product_id: int, actor_id: int) -> Product:
        """Deactivate product (soft delete)."""
        product = await self.get_product(product_id)
        old_state = product.to_dict()
        
        product.is_active = False
        
        await self._session.flush()
        
        await self._audit.record_event(
            entity="product",
            entity_id=product_id,
            action="deactivated",
            old_state=old_state,
            new_state=product.to_dict(),
            actor_id=actor_id,
            reason="Product deactivation",
        )
        
        return product

    async def create_bom(
        self,
        product_id: int,
        components: list[dict],
        actor_id: int,
        version: str = "1.0",
    ) -> BOMHeader:
        """Create BOM for a product."""
        product = await self.get_product(product_id)
        
        # Deactivate existing BOMs
        existing_bom = await self._bom_header_repo.get_active_by_product(product_id)
        if existing_bom:
            existing_bom.is_active = False
        
        # Create new BOM header
        bom_code = f"BOM-{product.code}-V{version}"
        bom = BOMHeader(
            code=bom_code,
            product_id=product_id,
            version=int(version.replace(".", "")),
            is_active=True,
        )
        
        self._session.add(bom)
        await self._session.flush()
        
        # Add components
        for idx, comp_data in enumerate(components):
            validate_positive_quantity(comp_data.get("quantity", 0))
            component = BOMItem(
                bom_header_id=bom.id,
                component_product_id=comp_data["component_product_id"],
                quantity=comp_data["quantity"],
                unit_of_measure=comp_data.get("unit_of_measure", "piece"),
                sequence_number=idx + 1,
            )
            self._session.add(component)
        
        await self._session.flush()
        
        # Audit
        await self._audit.record_event(
            entity="bom_header",
            entity_id=bom.id,
            action="created",
            old_state=None,
            new_state={"product_id": product_id, "version": version},
            actor_id=actor_id,
            reason=f"BOM creation for product {product.code}",
        )
        
        return bom

    async def get_bom(self, product_id: int) -> BOMHeader | None:
        """Get active BOM for a product."""
        return await self._bom_header_repo.get_active_by_product(product_id)
