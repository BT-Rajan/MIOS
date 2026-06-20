"""Product repository for database operations."""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.products.models import Product, BOM, BOMComponent, Routing, RoutingOperation
from backend.shared.repositories.base import BaseRepository


class ProductRepository(BaseRepository):
    """Repository for Product entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Product)

    async def get_by_code(self, code: str) -> Optional[Product]:
        """Get product by code."""
        query = select(Product).where(Product.code == code, Product.deleted_at.is_(None))
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_bom(self, product_id: int) -> Optional[Product]:
        """Get product with BOM relationships."""
        query = (
            select(Product)
            .where(Product.id == product_id, Product.deleted_at.is_(None))
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def search(self, search_term: str, limit: int = 50) -> List[Product]:
        """Search products by code or name."""
        query = select(Product).where(
            and_(
                Product.deleted_at.is_(None),
                (Product.code.ilike(f"%{search_term}%") | Product.name.ilike(f"%{search_term}%"))
            )
        ).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())


class BOMRepository(BaseRepository):
    """Repository for BOM entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, BOM)

    async def get_active_by_product(self, product_id: int) -> Optional[BOM]:
        """Get active BOM for a product."""
        query = (
            select(BOM)
            .where(BOM.product_id == product_id, BOM.is_active == True)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_versions_by_product(self, product_id: int) -> List[BOM]:
        """Get all BOM versions for a product."""
        query = (
            select(BOM)
            .where(BOM.product_id == product_id)
            .order_by(BOM.version.desc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())


class BOMComponentRepository(BaseRepository):
    """Repository for BOMComponent entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, BOMComponent)

    async def get_by_bom(self, bom_id: int) -> List[BOMComponent]:
        """Get all components for a BOM."""
        query = select(BOMComponent).where(BOMComponent.bom_id == bom_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())


class RoutingRepository(BaseRepository):
    """Repository for Routing entity."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Routing)

    async def get_by_product(self, product_id: int) -> List[Routing]:
        """Get all routings for a product."""
        query = select(Routing).where(Routing.product_id == product_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_active_by_product(self, product_id: int) -> Optional[Routing]:
        """Get active routing for a product."""
        query = (
            select(Routing)
            .where(Routing.product_id == product_id, Routing.is_active == True)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
