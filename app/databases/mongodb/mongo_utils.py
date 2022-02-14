import logging

from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
from core import settings
from .session import db


async def connect_to_mongo_async(mongodb_uri: str = settings.MONGO_DATABASE_URI):
    db.client = AsyncIOMotorClient(mongodb_uri)


async def close_mongo_connection_async():
    db.client.close()


def connect_to_mongo(mongodb_uri: str = settings.MONGO_DATABASE_URI):
    try:
        client = pymongo.MongoClient(mongodb_uri, maxPoolSize=300)
        client.server_info()  # force connection on a request as the
        # connect=True parameter of MongoClient seems
        # to be useless here
    except Exception as e:
        return None

    return pymongo.MongoClient(mongodb_uri, maxPoolSize=300)


def close_mongo_connection(client):
    client.close()
