from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from schemas.input_data import InputData
from core import settings
from models import input_data as model_input_data
from bson.objectid import ObjectId


def add_input_data(
    db: MongoClient,
    input_data: dict,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
) -> dict:
    input_data = db[input_data_collection].insert_one(input_data)
    new_input_data = db[input_data_collection].find_one({"_id": input_data.inserted_id})
    return new_input_data

def get_all_input_data(db: MongoClient,
                       is_used=True,
                        use_pydantic=False,
                        input_data_collection: str = settings.INPUT_DATA_COLLECTION):
    
    query = (
        {"is_used": True}
        if is_used
        else {}
    )

    input_data_list = []
    for input_data_dict in db[input_data_collection].find(query):
        if use_pydantic:
            input_data_list.append(model_input_data.InputData(**input_data_dict))
        else:
            input_data_list.append(input_data_dict)

    return input_data_list

async def async_get_all_input_data(db: AsyncIOMotorClient,
                       is_used=True,
                        use_pydantic=False,
                        input_data_collection: str = settings.INPUT_DATA_COLLECTION):
    
    query = (
        {"is_used": True}
        if is_used
        else {}
    )
    list_of_input_data = []
    async for input_data_dict in db[input_data_collection].find(query):
        if use_pydantic:
            list_of_input_data.append(model_input_data.InputData(**input_data_dict))
        else:
            list_of_input_data.append(input_data_dict)
            
    return list_of_input_data

    

def get_input_data_by_kfold_split_type(
    db: MongoClient,
    k_fold,
    split_type,
    exclude_without_label=True,
    use_pydantic=False,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    input_data_list = []

    query = (
        {f"k_fold_config.{k_fold}": split_type, "label": {"$ne": None}}
        if exclude_without_label
        else {f"k_fold_config.{k_fold}": split_type}
    )

    for input_data_dict in db[input_data_collection].find(query):
        if use_pydantic:
            input_data_list.append(model_input_data.InputData(**input_data_dict))
        else:
            input_data_list.append(input_data_dict)

    return input_data_list


def get_input_data_by_year_q(
    db: MongoClient,
    year,
    q,
    is_used=True,
    use_pydantic=False,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    input_data_list = []

    query = (
        {"year": year, "q": q, "is_used": True}
        if is_used
        else {"year": year, "q": q}
    )

    for input_data_dict in db[input_data_collection].find(query):
        if use_pydantic:
            input_data_list.append(model_input_data.InputData(**input_data_dict))
        else:
            input_data_list.append(input_data_dict)

    return input_data_list


async def get_input_data_by_year_q_async(
    db: AsyncIOMotorClient,
    year,
    q,
    is_used=True,
    use_pydantic=False,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    input_data_list = []

    query = (
        {"year": year, "q": q, "is_used": True}
        if is_used
        else {"year": year, "q": q}
    )

    async for input_data_dict in db[input_data_collection].find(query):
        if use_pydantic:
            input_data_list.append(model_input_data.InputData(**input_data_dict))
        else:
            input_data_list.append(input_data_dict)

    return input_data_list


def update_input_data_by_id(
    db: MongoClient,
    _id: ObjectId,
    dict_of_new_field: dict,
    upsert: bool = False,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    db[input_data_collection].update_one(
        {"_id": _id}, {"$set": dict_of_new_field}, upsert=upsert
    )
    
async def async_update_input_data_by_id(
    db: AsyncIOMotorClient,
    _id: ObjectId,
    dict_of_new_field: dict,
    upsert: bool = False,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    db[input_data_collection].update_one(
        {"_id": _id}, {"$set": dict_of_new_field}, upsert=upsert
    )
    return 1
    
def get_input_data_by_cik(
    db: MongoClient,
    cik: int,
    is_used=True,
    use_pydantic=False,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    query = (
        {"cik": cik, "is_used": True}
        if is_used
        else {"cik": cik}
    )

    input_data_list = []
    for input_data_dict in db[input_data_collection].find(query):
        if use_pydantic:
            input_data_list.append(model_input_data.InputData(**input_data_dict))
        else:
            input_data_list.append(input_data_dict)

    return input_data_list


async def update_many_input_data_by_industry(
    db: AsyncIOMotorClient,
    industry: str,
    dict_of_new_field: dict,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    db[input_data_collection].update_many(
        {"industry": industry}, {"$set": dict_of_new_field}, upsert=True
    )
    return 1


async def update_many_input_data_by_year_q(
    db: AsyncIOMotorClient,
    year: int,
    q: int,
    dict_of_new_field: dict,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    # list_of_res = []
    db[input_data_collection].update_many(
        {"year": year, "q": q}, {"$set": dict_of_new_field}, upsert=True
    )

    return 1

async def update_many_input_data_by_cik(
    db: AsyncIOMotorClient,
    cik: int,
    dict_of_new_field: dict,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    # list_of_res = []
    db[input_data_collection].update_many(
        {"cik": cik}, {"$set": dict_of_new_field}, upsert=True
    )

    return 1


def delete_input_data(
    db: MongoClient,
    cik: int,
    year: str,
    type: str,
    q: int,
    input_data_collection: str = settings.INPUT_DATA_COLLECTION,
):
    res_obj = db[input_data_collection].delete_one(
        {"cik": cik, "year": year, "type": type, "q": q}
    )
    return res_obj.acknowledged
