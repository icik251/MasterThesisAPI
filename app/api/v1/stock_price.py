from typing import Optional
from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from utils import parse_model_to_dict
from databases.mongodb.session import get_database_async
from crud.company import get_company_async
from crud.stock_price import get_stock_prices
from schemas.stock_price import StockPrice, ErrorResponseModel, ResponseModel
from celery_worker import create_stock_prices, create_adj_inflation_stock_prices

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
        )
        return ResponseModel([], "Task added to queue.")
    else:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Company doesn't exist, therefore stock prices can't be added.",
        )


@router.post(
    "/inflation/", response_description="Adding adjsuted to inflation stock prices"
)
async def add_adj_inflation_stock_prices(
    stock_price: StockPrice = Body(...),
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    stock_price_dict = stock_price.dict()
    company_list = await get_company_async(db, stock_price_dict["cik"])

    if company_list:
        stock_prices_list = await get_stock_prices(db, stock_price_dict["cik"])
        if not stock_prices_list:
            return ErrorResponseModel(
                "An error occurred.",
                404,
                "Stock prices are not added for this company. Therefore inflation adjustemnt can't be made",
            )
        for idx, stock_price_model in enumerate(stock_prices_list):
            stock_prices_list[idx] = parse_model_to_dict(stock_price_model)
        create_adj_inflation_stock_prices.delay(stock_prices_list)
        return ResponseModel([], "Task added to queue.")

    else:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Company doesn't exist, therefore stock prices can't be added.",
        )


@router.get(
    "/inflation/{cik}", response_description="Get adjusted for inflation stock prices"
)
async def get_adj_inflation_stock_prices_api(
    cik: int, db: AsyncIOMotorClient = Depends(get_database_async)
):

    stock_prices_list = await get_stock_prices(db=db, cik=cik, ts_type="adj_inflation")
    if not stock_prices_list:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Stock prices adjusted for inflation not found",
        )
    return ResponseModel(
        stock_prices_list, "Stock prices adjusted for inflation retrieved successfully."
    )


@router.get("/{cik}", response_description="Get stock prices")
async def get_stock_prices_api(
    cik: int, db: AsyncIOMotorClient = Depends(get_database_async)
):

    stock_prices_list = await get_stock_prices(db=db, cik=cik, ts_type="adj_close")
    if not stock_prices_list:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Stock prices not found",
        )
    return ResponseModel(stock_prices_list, "Stock prices retrieved successfully.")
