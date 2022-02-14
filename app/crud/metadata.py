from pymongo import MongoClient
from core import settings


def add_metadata(
    db: MongoClient,
    metadata: dict,
    metadata_collection: str = settings.METADATA_COLLECTION,
) -> dict:
    metadata = db[metadata_collection].insert_one(metadata)
    new_metadata = db[metadata_collection].find_one({"_id": metadata.inserted_id})
    return new_metadata
