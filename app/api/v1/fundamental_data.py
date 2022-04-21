from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from databases.mongodb.session import get_database_async
from crud.company_base import get_company_base_async

from schemas.fundamental_data import FundamentalData, ErrorResponseModel, ResponseModel
from schemas.fundamental_data_avg import (
    FundamentalDataAvg,
    ErrorResponseModel,
    ResponseModel,
)
from celery_worker import create_fundamental_data, average_fundamental_data

router = APIRouter()


@router.post("/", response_description="Fundamental data added into the queue")
async def add_fundamental_data(
    metadata: FundamentalData = Body(...),
    db: AsyncIOMotorClient = Depends(get_database_async),
):
    metadata_dict = metadata.dict()
    curr_company_base = await get_company_base_async(db, metadata_dict["cik"])

    if curr_company_base:
        create_fundamental_data.delay(metadata_dict["cik"], curr_company_base["ticker"])
        return ResponseModel([], "Task added to queue.")
    else:
        return ErrorResponseModel(
            "An error occurred.",
            404,
            "Company base doesn't exist, therefore fundamental data can't be added.",
        )


@router.post("/average_impute/", response_description="Average KPIs and impute where data is missing")
async def add_fundamental_data(
    fundamental_data_avg: FundamentalDataAvg = Body(...)
):
    fundamental_data_avg_dict = fundamental_data_avg.dict()

    average_fundamental_data.delay(
        fundamental_data_avg_dict["year"], fundamental_data_avg_dict["q"]
    )
    return ResponseModel([], "Task added to queue.")
