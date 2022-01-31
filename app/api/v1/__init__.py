from fastapi import APIRouter
from api.v1 import company

api_router = APIRouter()
api_router.include_router(company.router, prefix="/company", tags=["company"])
