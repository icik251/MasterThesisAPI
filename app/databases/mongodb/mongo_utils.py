import logging

from motor.motor_asyncio import AsyncIOMotorClient
from core import settings
from .session import db

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGO_DATABASE_URI)

async def close_mongo_connection():
    db.client.close()
