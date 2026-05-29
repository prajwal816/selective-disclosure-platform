"""
API v1 router — aggregates all endpoint routers under /api/v1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.credentials import router as credentials_router
from app.api.v1.endpoints.share import router as share_router
from app.api.v1.endpoints.verify import router as verify_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(credentials_router)
api_router.include_router(share_router)
api_router.include_router(verify_router)
