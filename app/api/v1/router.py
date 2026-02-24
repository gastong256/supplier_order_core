from fastapi import APIRouter

from app.api.v1.endpoints import health, orders, products, suppliers

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
