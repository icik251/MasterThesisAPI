from pymongo import MongoClient
from core import settings
from models import adapter_data as model_adapter_data
from bson.objectid import ObjectId


def add_adater_data(
    db: MongoClient,
    adapter_data_dict: dict,
    adapter_data_collection: str = settings.ADAPTER_DATA_COLLECTION,
) -> dict:
    adapter_data = db[adapter_data_collection].insert_one(adapter_data_dict)
    new_adapter_data = db[adapter_data_collection].find_one(
        {"_id": adapter_data.inserted_id}
    )
    return new_adapter_data


def get_all_adapter_data(
    db: MongoClient,
    use_pydantic=False,
    adapter_data_collection: str = settings.ADAPTER_DATA_COLLECTION,
):
    adapter_data_list = []
    for adapter_data_dict in db[adapter_data_collection].find({}):
        if use_pydantic:
            adapter_data_list.append(
                model_adapter_data.AdapterData(**adapter_data_dict)
            )
        else:
            adapter_data_list.append(adapter_data_dict)

    return adapter_data_list


def update_adapter_data_by_id(
    db: MongoClient,
    _id: ObjectId,
    dict_of_new_field: dict,
    upsert: bool = False,
    adapter_data_collection: str = settings.ADAPTER_DATA_COLLECTION,
):
    db[adapter_data_collection].update_one(
        {"_id": _id}, {"$set": dict_of_new_field}, upsert=upsert
    )
    
    
