from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.farms import router as farms_router
from app.api.v1.animals import router as animals_router, group_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.production import router as production_router
from app.api.v1.finance import router as finance_router
from app.api.v1.ai_entry import router as ai_entry_router
from app.api.v1.ai_assistant import router as ai_assistant_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.alerts import router as alerts_router

v1_router = APIRouter()

v1_router.include_router(auth_router)
v1_router.include_router(farms_router)
v1_router.include_router(animals_router)
v1_router.include_router(group_router)
v1_router.include_router(inventory_router)
v1_router.include_router(production_router)
v1_router.include_router(finance_router)
v1_router.include_router(ai_entry_router)
v1_router.include_router(ai_assistant_router)
v1_router.include_router(analytics_router)
v1_router.include_router(alerts_router)


__all__ = ["v1_router"]
