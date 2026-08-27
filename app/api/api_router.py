from fastapi import APIRouter
from app.config.constants import API_PREFIX
from .llm_service.llm_service_routes import router as  llm_service_router


router = APIRouter(prefix=API_PREFIX)


def add_routes():
    router.include_router(llm_service_router)


add_routes()