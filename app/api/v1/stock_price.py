from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from utils import parse_model_to_dict
from databases.mongodb.session import get_database_async
from crud.company import get_company_async

from schemas.stock_price import StockPrice, ErrorResponseModel
from celery_worker import create_stock_prices

router = APIRouter()


@router.post("/", response_description="Adding stock prices to database")
async def add_stock_prices(
    stock_price: StockPrice = Body(...),
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    stock_price_dict = stock_price.dict()
    company_list = await get_company_async(db, stock_price_dict["cik"])

    if company_list:
        # passing the first document in the list for the company as it does not matter
        create_stock_prices.delay(
            parse_model_to_dict(company_list[0]),
            stock_price_dict["start_date"],
            stock_price_dict["end_date"],
        )
        return {"message": "Task added to queue."}
    else:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Company doesn't exist, therefore stock prices can't be added.",
        )
