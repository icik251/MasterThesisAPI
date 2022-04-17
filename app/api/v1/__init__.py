from fastapi import APIRouter
from api.v1 import company, fundamental_data, stock_price, input_data

api_router = APIRouter()
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(
    stock_price.router, prefix="/stock_price", tags=["stock_price"]
)
api_router.include_router(input_data.router, prefix="/input_data", tags=["input_data"])
api_router.include_router(fundamental_data.router, prefix="/fundamental_data", tags=["fundamental_data"])
