from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()

api_router.include_router(health.router)

# Register domain routers here as you build them out:
# from app.api.v1.endpoints import suppliers, orders
# api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
# api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
