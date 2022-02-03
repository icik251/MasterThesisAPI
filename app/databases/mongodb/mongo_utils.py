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
    db.client = pymongo.MongoClient(mongodb_uri)


def close_mongo_connection():
    db.client.close()
