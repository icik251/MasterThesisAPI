from fastapi import APIRouter
from api.v1 import company, metadata

api_router = APIRouter()
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(metadata.router, prefix="/metadata", tags=["metadata"])
api_router.include_router(metadata.router, prefix="/stock_price", tags=["stock_price"])
