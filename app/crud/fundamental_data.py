from pymongo import MongoClient
from core import settings
from models.fundamental_data import FundamentalData


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
