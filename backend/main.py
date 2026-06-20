"""
FastAPI application factory.

Creates and configures the main application instance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.core.config import get_settings
from backend.core.database import init_db


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    init_db()
    yield
    # Shutdown (cleanup if needed)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Manufacturing Intelligence Operating System",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure per environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    def health_check():
        return {"status": "healthy", "version": settings.app_version}
    
    # Register API routers
    from backend.api.auth.router import router as auth_router
    from backend.api.users.router import router as users_router
    from backend.api.customers.router import router as customers_router
    from backend.api.vendors.router import router as vendors_router
    from backend.api.products.router import router as products_router
    from backend.api.inventory.router import router as inventory_router
    from backend.api.orders.router import router as orders_router
    from backend.api.procurement.router import router as procurement_router
    from backend.api.production.router import router as production_router
    from backend.api.workers.router import router as workers_router
    from backend.api.finance.router import router as finance_router
    from backend.api.reports.router import router as reports_router
    from backend.api.conversation.router import router as conversation_router

    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/api/users", tags=["Users"])
    app.include_router(customers_router, prefix="/api/customers", tags=["Customers"])
    app.include_router(vendors_router, prefix="/api/vendors", tags=["Vendors"])
    app.include_router(products_router, prefix="/api/products", tags=["Products"])
    app.include_router(inventory_router, prefix="/api/inventory", tags=["Inventory"])
    app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])
    app.include_router(procurement_router, prefix="/api/procurement", tags=["Procurement"])
    app.include_router(production_router, prefix="/api/production", tags=["Production"])
    app.include_router(workers_router, prefix="/api/workers", tags=["Workers"])
    app.include_router(finance_router, prefix="/api/finance", tags=["Finance"])
    app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
    app.include_router(conversation_router, prefix="/api/conversation", tags=["Conversation"])
    
    return app


app = create_app()
