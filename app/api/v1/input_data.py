from typing import Optional
from urllib import response
from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from utils import parse_model_to_dict
from databases.mongodb.session import get_database_async

from crud.company import get_company_async
from crud.stock_price import get_stock_prices
from crud.fundamental_data import get_fundamental_data_async
from crud.input_data import get_input_data_by_year_q_async, update_many_input_data_by_industry, update_many_input_data_by_year_q

from schemas.input_data import InputData, ResponseModel, ErrorResponseModel
from schemas.scaler import Scaler

from models.input_data import UpdateIsIsedInputData

from celery_worker import create_model_input_data, create_scaled_data

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
    fundamental_data_dict = await get_fundamental_data_async(db, cik_dict["cik"])

    if company_list and stock_prices_list and fundamental_data_dict:
        # Passing list of company objects
        for idx, company_list_model in enumerate(company_list):
            company_list[idx] = parse_model_to_dict(company_list_model)
        for idx, stock_price_model in enumerate(stock_prices_list):
            stock_prices_list[idx] = parse_model_to_dict(stock_price_model)
        fundamental_data_dict = parse_model_to_dict(fundamental_data_dict)

        create_model_input_data.delay(
            company_list, stock_prices_list, fundamental_data_dict
        )
        return ResponseModel([], "Task added to queue.")
    else:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Company doesn't exist or stock prices for inflation are not added or fundamental data is not added. Therefore model input data can't be added.",
        )


@router.get("/{year}/{q}", response_description="Get input data for year and quarter")
async def get_input_data(
    year: int = 2017,
    q: int = 1,
    exclude_without_label: Optional[bool] = True,
    db: AsyncIOMotorClient = Depends(get_database_async),
):

    list_of_input_data = await get_input_data_by_year_q_async(db, year, q, exclude_without_label, True)
    if list_of_input_data:
        return ResponseModel(list_of_input_data, "Result retrieved")
    else:
        return ErrorResponseModel(
            "An error occurred.", 404, f"No input data for {year}, {q}"
        )


@router.post("/scale/", response_description="Scale label data from a certain k-fold")
async def scale_data(scaler_post: Scaler = Body(...)):
    scaled_dict = scaler_post.dict()
    create_scaled_data.delay(scaled_dict["k_fold"])
    return ResponseModel([], "Task added to queue.")


@router.put("/", response_description="Update input data")
async def update_input_is_used(
    industry: Optional[str] = None,
    year: Optional[int] = None, 
    q: Optional[int] = None,
    updated_is_used_input_data: UpdateIsIsedInputData = Body(...),
    db: AsyncIOMotorClient = Depends(get_database_async),
):  
    if industry:
        res_list = await update_many_input_data_by_industry(db, industry, updated_is_used_input_data.dict())
        return ResponseModel(
            res_list, f"Succesfully updated for industry {industry}"
        )
    elif year and q:
        res_list = await update_many_input_data_by_year_q(db, year, q, updated_is_used_input_data.dict())
        return ResponseModel(
            res_list, f"Succesfully updated for year {year} and quarter {q}"
        )
    return ErrorResponseModel("Correct data not provided", 412, "No industry or year and q provided")
