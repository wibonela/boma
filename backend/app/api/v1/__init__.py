"""
API v1 router aggregation.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import users, properties, bookings, reviews

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(users.router)
api_router.include_router(properties.router)
api_router.include_router(bookings.router)
api_router.include_router(reviews.router)

# Placeholder route until endpoints are implemented
@api_router.get("/", tags=["info"])
async def api_info():
    """API v1 information endpoint."""
    return {
        "message": "BOMA API v1",
        "status": "active",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
        }
    }
