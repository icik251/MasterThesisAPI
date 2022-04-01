from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from schemas.input_data import InputData
from core import settings
from models import input_data as model_input_data


def add_input_data(
    db: MongoClient,
    input_data: dict,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
) -> dict:
    input_data = db[input_data_collection].insert_one(input_data)
    new_input_data = db[input_data_collection].find_one({"_id": input_data.inserted_id})
    return new_input_data


def get_input_data(
    db: MongoClient,
    k_fold,
    split_type,
    exclude_without_label=True,
    use_pydantic=False,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    input_data_list = []

    query = (
        {f"k_fold_config.{k_fold}": split_type}
        if exclude_without_label
        else {f"k_fold_config.{k_fold}": split_type, "label": None}
    )

    for input_data_dict in db[input_data_collection].find(query):
        if use_pydantic:
            input_data_list.append(model_input_data.InputData(**input_data_dict))
        else:
            input_data_list.append(input_data_dict)

    return input_data_list


def delete_input_data(
    db: MongoClient,
    cik: int,
    year: str,
    type: str,
    period_of_report: datetime,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    res_obj = db[input_data_collection].delete_one(
        {"cik": cik, "year": year, "type": type, "period_of_report": period_of_report}
    )
    return res_obj.acknowledged
