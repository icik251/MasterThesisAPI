from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from databases.mongodb.session import get_database_async
from crud.company import get_company_async

from schemas.stock_price import StockPrice, ErrorResponseModel
from celery_worker import create_stock_prices

router = APIRouter()


@router.post("/", response_description="Adding stock prices to database")
async def add_metadata(
    cik_post: StockPrice = Body(...),
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    cik_post_dict = cik_post.dict()
    curr_company = await get_company_async(db, cik_post_dict["cik"])

    if curr_company:
        create_stock_prices.delay(cik_post_dict["cik"])
        return {"message": "Task added to queue."}
    else:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Company doesn't exist, therefore metadata can't be added.",
        )
