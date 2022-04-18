from typing import Any
from pymongo import MongoClient
from core import settings
from models.fundamental_data import FundamentalData
from motor.motor_asyncio import AsyncIOMotorClient

def add_fundamental_data(
    db: MongoClient,
    fundamental_data: dict,
    fundamental_data_collection: str = settings.FUNDAMENTAL_DATA_COLLECTION,
) -> dict:
    fundamental_data = db[fundamental_data_collection].insert_one(fundamental_data)
    new_fundamental_data = db[fundamental_data_collection].find_one(
        {"_id": fundamental_data.inserted_id}
    )
    return new_fundamental_data


def delete_fundamental_data(
    db: MongoClient,
    cik: int,
    fundamental_data_collection: str = settings.FUNDAMENTAL_DATA_COLLECTION,
):
    res_obj = db[fundamental_data_collection].delete_one({"cik": cik})
    return res_obj.acknowledged


async def get_fundamental_data_async(
    db: AsyncIOMotorClient,
    cik: int,
    fundamental_data_collection: str = settings.FUNDAMENTAL_DATA_COLLECTION,
) -> Any:
    fundamental_data = await db[fundamental_data_collection].find_one({"cik": cik})
    if fundamental_data:
        return FundamentalData(**fundamental_data)
    return None
    
