from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from utils import parse_model_to_dict
from databases.mongodb.session import get_database_async
from crud.company import get_company_async
from crud.stock_price import get_stock_prices
from schemas.input_data import InputData, ResponseModel, ErrorResponseModel
from celery_worker import create_model_input_data

router = APIRouter()


@router.post(
    "/", response_description="Reformating and adding model input data to the database"
)
async def add_model_input_data(
    cik_post: InputData = Body(...),
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    cik_dict = cik_post.dict()
    company_list = await get_company_async(db, cik_dict["cik"])
    stock_prices_list = await get_stock_prices(db, cik_dict["cik"], "adj_inflation")

    if company_list and stock_prices_list:
        # Passing list of company objects
        for idx, company_list_model in enumerate(company_list):
            company_list[idx] = parse_model_to_dict(company_list_model)
        for idx, stock_price_model in enumerate(stock_prices_list):
            stock_prices_list[idx] = parse_model_to_dict(stock_price_model)

        create_model_input_data.delay(company_list, stock_prices_list)
        return ResponseModel([], "Task added to queue.")
    else:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Company doesn't exist or stock prices for inflation are not added. Therefore model input data can't be added.",
        )
