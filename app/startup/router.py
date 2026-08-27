from fastapi import APIRouter, Depends, HTTPException, status
from app.config.constants import API_PREFIX, PORT
from app.api.api_router import router as api_router


router = APIRouter()

@router.get('/', status_code=200)
def service_info():
    return "Service is running on port {port}".format(port=PORT)


# Add API router here
router.include_router(api_router)